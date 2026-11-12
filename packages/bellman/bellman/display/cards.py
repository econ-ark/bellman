"""The records a denotation answers with, and the card of a piece or of a
definition, set from those records alone.

A card is a printing of what its record holds. Every printed expression is
`format_expression` of a term the record holds, under the names the record
gives its identities; no term is rewritten by matching its shape, nothing is
inferred at printing time, and nothing branches on a stage's name. The stage
composes its sheets in :mod:`bellman.stage.inventory`. This module reads no
module of `bellman.stage`: its only input is the answer it prints. Every line
of a card is set by :mod:`bellman.syntax.layout` at the width of 78.

The records stand here, from a wire (`Wire`) to the stage's own answer
(`StageDenotation`): each prints itself as its card, or as its lines where it
holds no title block, and a `Piece` unpacks as its key and the mapping line
`mapping_line` writes. The queries of `bellman.stage` build these records.
`card_sections` answers a card's sections, each with its heading and its rows
as the card prints them, from the sections the card forms before it joins
them, so that a reader of one section reads no printed card back.
`rule_rows` answers the rules of a primitive's `Rule` section each on one
line, and `source_lines` the file and the line number of each line the
`Source` section quotes, from the same records.

A card is a title over sections: a heavy line under the title and one
closing the card; each section opened by its heading at column zero, its
content two columns in, a blank line between two sections; a light line
across the card before the footer where the card has a body, the footer's
first section `Source`, the file's name once and the lines by number; every
entry of `Operations` its number and key, one `in:` and `out:` line with
`out:` at column 40, a short line and its rule lines, a blank line between
two entries, except on the stage card, whose entries are builders and print
no short line and no rule line; the short lines of a card, under every
entry's row and above the `out` rows of `Signature`, ending at one column;
and every column of a section sized to its longest entry plus two.
"""

from __future__ import annotations

import dataclasses
import re
from collections import namedtuple
from pathlib import PurePosixPath

from bellman.display.printed_records import (
    SIDE_WORDS,
    bundle_name,
    tuple_text,
    wires_by_value_bundle,
)
from bellman.display.sheets import Sheet
from bellman.native.identity import OPERATOR_KINDS, Identity
from bellman.native.labels import function_name
from bellman.native.predicates import And, Compare, Complementarity, IsInteger, Member, Not
from bellman.native.records import CategoryCodes, Record
from bellman.refusals import METHOD_CONDITIONS
from bellman.syntax import layout
from bellman.syntax.vocabulary import PERCH_MARK, PERCH_WORD, WRITTEN_MARK
from bellman.typing import typed_expressions as S
from bellman.typing.category_codes import describe
from bellman.typing.typed_expressions import WireType

# The words a card prints, under the keys its functions read them by: the
# words of a title, the direction words of the stage card, the headings of
# the sections in the order they stand on a card, the labels of an entry of
# `Operations` and of the rows of `Signature`, and the stage card's footer.
WORDS = {
    # the words of a title
    "stage": "STAGE",
    "backward-address": "BACKWARD",
    "policy-address": "POLICY",
    "forward-address": "FORWARD",
    "builders": "BUILDERS",
    "builder": "BUILDER",
    "initial": "INITIAL DIAGRAM",
    "block": "BLOCK",
    "method-address": "METHOD",
    "correspondence-address": "CORRESPONDENCE",
    "distribution-address": "DISTRIBUTION",
    "parameter-address": "PARAMETER",
    "derived-address": "DERIVED PARAMETER",
    "g-address": "LAW OF MOTION",
    "G-address": "VALUE AGGREGATOR",
    # the direction words of the stage card
    "backward": "backward",
    "forward": "forward",
    # the headings of the sections of a card, in the order they stand on it
    "signature": "Signature",
    "defines": "Defines",
    "at": "At",
    "where": "Where",
    "declared": "Declared",
    "rule": "Rule",
    "operations": "Operations",
    "conditions": "Conditions",
    "method": "Method",
    "options": "Options",
    "keywords": "Keywords",
    "grid": "Grid",
    "source": "Source",
    "definitions": "Definitions referenced",
    "file": "File",
    "perches": "Perches",
    "appendix": "Appendix",
    "admits": "Admits",
    # the sub-labels of the rows of `Signature`, and the labels of the lines
    # of an entry of `Operations`
    "in": SIDE_WORDS["in"],
    "out": SIDE_WORDS["out"],
    "in-label": "in:",
    "out-label": "out:",
    "rule-label": "rule:",
    # the word before the conditions of a row of the definitions listing
    "conditions-word": "conditions",
    # the stage card's footer
    "appendix-name": "Bellman-SYM, Appendix C",
    "appendix-path": "docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md",
    "unmarked": "unmarked: decision",
}

# --- the records a denotation answers with ---


class _Displayed:
    """A record of a denotation that displays itself: `lines` is its printed
    lines at column zero (`card_body_lines`), `sheet` its card (`card_of`), and
    `str` the card where the record holds a title block and the lines where it
    holds none. Equality and hashing are of the record's own fields, which the
    dataclass decorator supplies."""

    # the title block of the card, held by every record reached below the
    # stage; the stage's own answer carries none and prints its lines
    title = None

    @property
    def lines(self):
        """The record's printed lines; see
        `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
        return card_body_lines(self, 0)

    @property
    def sheet(self):
        """The record's card; see
        `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
        return card_of(self)

    def __str__(self):
        return str(self.sheet) if self.title is not None else "\n".join(self.lines)

    __repr__ = __str__


@dataclasses.dataclass(frozen=True, repr=False)
class TitleBlock(_Displayed):
    """The address, subtitle and stamp identifying the piece on a card.
    `pair` is the pair of perches a backward or a forward builder joins,
    `cntn → dcsn`, printed in the title of the builder's own card and of
    every piece card whose address names that builder, at every grain;
    `""` elsewhere, including on the policy builder, whose title carries no
    pair.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    address: str
    subtitle: str = ""
    stamp: str = ""
    _: dataclasses.KW_ONLY
    stage: str = ""
    identity: object = None
    level: str = ""
    direction: str = ""
    keys: tuple = ()
    grain: str = "builder"
    pair: str = ""


class Wire(_Displayed):
    """One typed wire: its displayed `name`, the carrier the query that built
    it derived (`mathematical_type`, a `WireType`, printed as `type`),
    its retained `identity` and originating `sort`. It unpacks as `(identity,
    type)` and displays the same wire line as its containing card. The record
    holds its carrier and no reference to its stage, so a card or an encoding
    is written from the record alone.

    Equality and hashing retain that two-entry signature contract. They do
    not compare the additional defining expressions; compare `expression`
    and `definition` explicitly when comparing mathematical answers.
    `controls` names the declared components of a policy-set member.
    `rules` holds the relations the operation that writes the wire declares
    on it, each a `Rule` at the point; `residuals` holds, on the unnamed input
    of a solve, the residual equations of the lines that write it, each a
    `Rule` naming its residual.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §6."""

    def __init__(
        self,
        name,
        identity,
        sort=None,
        *,
        mathematical_type,
        note="",
        expression=None,
        definition=None,
        controls=(),
        rules=(),
        residuals=(),
    ):
        if not isinstance(mathematical_type, WireType):
            raise TypeError(
                f"a wire holds its carrier as a WireType; got {type(mathematical_type).__name__}"
            )
        for key, value in (
            ("name", name),
            ("identity", identity),
            ("sort", sort),
            ("mathematical_type", mathematical_type),
            ("note", note),
            ("expression", expression),
            ("definition", definition),
            ("controls", tuple(controls)),
            ("rules", tuple(rules)),
            ("residuals", tuple(residuals)),
        ):
            object.__setattr__(self, key, value)

    def __setattr__(self, name, value):
        raise dataclasses.FrozenInstanceError("a wire answer is immutable")

    def __delattr__(self, name):
        raise dataclasses.FrozenInstanceError("a wire answer is immutable")

    @property
    def type(self):
        return str(self.mathematical_type)

    def component(self, name):
        """The projected set-valued type of one component of a joint policy,
        not a new wire or a selected policy: the wire's own type for a policy
        of one control, and for a joint choice the set of functions of the
        state that agree with some member of the joint set, which
        `typed_expressions.projected_policy_set` writes; `KeyError` for a name
        that is no control of this wire.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §6.
        """
        matches = [
            n
            for n, identity in enumerate(self.controls)
            if name == identity or name == identity.field
        ]
        if len(matches) != 1:
            raise KeyError(name)
        answer = self.mathematical_type
        if len(self.controls) == 1:
            return answer
        result, target = S.projected_policy_set(answer.carrier, self.controls, matches[0])
        return WireType(answer.sort[:4] + (target,), result, answer.declarations)

    def __iter__(self):
        return iter((self.identity, self.type))

    def __len__(self):
        return 2

    def __getitem__(self, index):
        return (self.identity, self.type)[index]

    def __eq__(self, other):
        if not isinstance(other, (Wire, tuple)):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __hash__(self):
        return hash(tuple(self))


@dataclasses.dataclass(frozen=True, repr=False)
class Statement(_Displayed):
    """An authored line with its address, text and retained file position.
    `doc` records the `!doc` annotation. Display-only `no_wire` retains the
    block's margin annotation without changing the position or value.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §4."""

    address: object
    text: str
    position: str = ""
    _: dataclasses.KW_ONLY
    doc: bool = False
    no_wire: bool = dataclasses.field(default=False, compare=False)


@dataclasses.dataclass(frozen=True, repr=False)
class Denoted(_Displayed):
    """One object denoted by a kernel's statements: its symbol, type, defining
    rule, cited construction rule and identity. Display-only `bare` prints a
    policy map or distribution convention without a preceding symbol.
    `specializes` identifies the retained kernel when this object is its local
    expression at a supplied policy; that expression has no new stored
    identity. The category map of a set marked `!categories` is the set's
    second object, whose expression is the `CategoryCodes` of its record.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §6."""

    symbol: str
    mathematical_type: object
    expression: object
    _: dataclasses.KW_ONLY
    cited: str
    identity: object = ""
    bare: bool = dataclasses.field(default=False, compare=False)
    specializes: object = None

    @property
    def type(self):
        """The display of the derived carrier.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §6.
        """
        return str(self.mathematical_type) if self.mathematical_type is not None else ""

    @property
    def rule(self):
        """The display of the defining expression; a category map as
        `category_codes.describe` writes it.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §6.
        """
        return (
            str(self.expression)
            if isinstance(self.expression, Textual)
            else describe(self.expression, self.symbol)
            if isinstance(self.expression, CategoryCodes)
            else S.format_expression(self.expression)
            if self.expression is not None
            else ""
        )


@dataclasses.dataclass(frozen=True, repr=False)
class Rule(_Displayed):
    """A relation an operation declares on its output, held at the point:
    `statement` the relation as a term with the coordinates free, `where` the
    clauses it is read under, each a term, `on` the set it holds on, the
    image `𝑚_d≻(Xa)` of a grid relation, or, for a relation read at a point
    of several coordinates, the membership of the point in its domain,
    `(m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊`, or None where it holds at every
    point, and `label` the id of the line the relation is, where that line
    is a property attached to the row's line by a dotted id,
    `optimality.euler`, or None. A residual line of a solve is a `Rule`
    whose statement names the residual, `r₁ = c − 𝑐≻(…)`, and the outputs of a
    law of motion are one, `(a, h, z) = 𝑔≻(m, z_d, c, h_choice)`."""

    statement: object
    where: tuple = ()
    on: object = None
    label: object = None


@dataclasses.dataclass(frozen=True, repr=False)
class Declared(_Displayed):
    """A line marked `!doc` as the condition on the constructed output of its
    builder, printed in the `Declared` section: `source` the line as the file
    writes it, a `Statement` with its position, and
    `statement` the line read by identity with the constructed output
    substituted, `𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]`,
    a term. The line forms no operation and no piece."""

    source: object
    statement: object


@dataclasses.dataclass(frozen=True, repr=False)
class Textual(_Displayed):
    """Retained wording for a mathematical part not yet derived as an
    expression."""

    text: str

    def __str__(self):
        return self.text + " [textual]"

    __repr__ = __str__


@dataclasses.dataclass(frozen=True, repr=False)
class Hypothesis(_Displayed):
    """A proposition the denotation requires, assumes or defines, with that
    kind of hypothesis recorded separately from its sentence.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    kind: str
    predicate: object

    @property
    def proposition(self):
        return (
            str(self.predicate)
            if isinstance(self.predicate, Textual)
            else S.format_expression(self.predicate)
        )


@dataclasses.dataclass(frozen=True, repr=False)
class KernelClause(_Displayed):
    """The kernel clause on an operator's card: kind, symbol, owner, identity,
    authored statements, denoted objects and hypotheses. `Kernel` is the
    separate text record returned by `kernel()`.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §6."""

    kind: str
    symbol: str = ""
    owner: str = ""
    _: dataclasses.KW_ONLY
    identity: object = ""
    statements: tuple = ()
    denoted: tuple = ()
    hypotheses: tuple = ()


@dataclasses.dataclass(frozen=True, repr=False, eq=False)
class MethodClause(_Displayed, Record):
    """The components typed at one place, as a card's `Method` section
    prints them: the place's `address`, its `method` word with its keyword
    arguments, its `grid` and its `handler`, each None where not typed,
    `written`, the components on one line as the `Method` row prints them,
    and `options`, the rows of the `Options` section, one `(keyword, value)`
    pair per keyword argument of the method word, the value the configured
    value of the setting the argument names where one is bound and the
    argument as written otherwise (`denotations._method_clause`)."""

    address: object
    method: object
    grid: object
    handler: str | None
    _: dataclasses.KW_ONLY
    written: str
    options: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "options", tuple(tuple(pair) for pair in self.options))


@dataclasses.dataclass(frozen=True, repr=False)
class BlockDenoted(Denoted):
    """An object a block file defines (specification 0.6 §4): the `Denoted`
    with `written_at`, the block file's name and the line of the
    definition, `cons_egm.bl:3`, which the card's `Definitions referenced`
    prints after the identity."""

    written_at: str = ""


@dataclasses.dataclass(frozen=True, repr=False)
class ImageByName(_Displayed):
    """An image written as the name of the output wire, when that name already
    states the composition with the kernel.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    expression: object

    @property
    def name(self):
        return S.format_expression(self.expression)


@dataclasses.dataclass(frozen=True, repr=False)
class ImageAtPoint(_Displayed):
    """An image written as a function of its point: `point` gives the
    coordinate identities and `term` the rule evaluated there.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    expression: object

    @property
    def point(self):
        return tuple(variable.identity for variable, _ in self.expression.bindings)

    @property
    def term(self):
        return S.format_expression(self.expression.body)


@dataclasses.dataclass(frozen=True, repr=False)
class ImageSet(_Displayed):
    """The set of admissible outputs, with bound variable, type and condition.
    It makes no selection and may be empty. `names` retains the coordinates
    whose declared sets the card must state; where no point is bound, the
    condition is the authored relation.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    expression: object

    @property
    def variable(self):
        return S.format_expression(self.expression.bound)

    @property
    def type(self):
        return S.format_expression(self.expression.base)

    @property
    def condition(self):
        return " ∧ ".join(S.format_expression(term) for term in self.expression.conds)

    @property
    def names(self):
        return tuple(sorted(S.free_identities(self.expression), key=str))


@dataclasses.dataclass(frozen=True, repr=False)
class OperatorCard(_Displayed):
    """A primitive operator's denotation: kind, policy parameters, typed
    inputs and outputs, image, feasibility, affine inputs, kernel, hypotheses,
    control coordinates, conditions, methods, the policy it is at, the local
    abbreviations and title. Its display is its card. `at` holds the policy
    the operation is held at, typed as the policy builder types it, and
    `where` the local abbreviations the operation reads: the section of a
    law of motion at a label as a `Denoted` with its identity, `𝑔_keep≻`,
    and the outputs of a law of motion as a `Rule`, `(a, h, z) = 𝑔≻(m, z_d,
    c, h_choice)`; the law of motion at the policy is written out where a
    term reads it and has no entry (RL14).

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    kind: str
    policies: tuple = ()
    inputs: tuple = ()
    _: dataclasses.KW_ONLY
    outputs: tuple = ()
    image: object = None
    feasible: tuple = ()
    affine: str = ""
    kernel: object = None
    required: tuple = ()
    coordinate: tuple = ()
    conditions: tuple = ()
    method: tuple = ()
    title: object = None
    expression: object = None
    definitions: tuple = ()
    source: str = ""
    at: tuple = ()
    where: tuple = ()


class Piece(_Displayed, tuple):
    """A named piece within a composite: its navigation key, whole name and
    own denotation record. It unpacks as the key and the first printed line,
    and its display comes from the contained record.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""

    def __new__(cls, key, name, record):
        made = super().__new__(cls, (key, mapping_line(record)))
        made.key = key
        made.name = name
        made.record = record
        return made


def mapping_line(record):
    """The input and output names used when a denotation Piece unpacks, and
    the mapping the stage sheet's GRAPHS section prints for a builders graph
    from its `Signature`, `(𝑉≻, 𝑑𝑉≻) ↦ (𝑉≺, 𝑑𝑉≺), 𝑐(m_d)`: each wire under the
    name its card gives it."""
    inputs = tuple_text(_side_names(record, record.inputs))
    outputs = _side_names(record, record.outputs)
    if isinstance(record, OperatorCard):
        return f"{inputs} ↦ {tuple_text(outputs)}"
    return f"{inputs} ↦ {', '.join(outputs)}"


def _side_names(record, wires):
    """The names of the wires of one side of a piece, as the record holds
    them: a primitive operator's wires by name, a composite's by the bundles
    they form."""
    if isinstance(record, OperatorCard):
        return tuple(wire.name for wire in wires)
    return tuple(bundle_name(group) for group in wires_by_value_bundle(wires))


@dataclasses.dataclass(frozen=True, repr=False)
class Composite(_Displayed):
    """A builder, sub-builder or builders-graph denotation, with policy
    parameters, typed wires and named pieces. `chain` and `order` state their
    composition; `free` records free names and their sources. The header,
    control coordinates, conditions, methods and title remain on the record.
    `at` holds the policy a decision builder is at, typed as the policy
    builder types it, and `where` the local abbreviations its pieces
    introduce, each once; `doc` holds the lines marked `!doc` of the block as
    the conditions on the constructed output, each a `Declared`, which form
    no piece;
    `declarations` holds the lines of the block that declare its multipliers,
    as the file writes them, each a `Statement` that stands in the `Source`
    section and forms no piece.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""

    policies: tuple = ()
    inputs: tuple = ()
    outputs: tuple = ()
    _: dataclasses.KW_ONLY
    pieces: tuple = ()
    chain: bool = False
    order: tuple = ()
    order_kind: str = "application"
    free: tuple = ()
    header: tuple = ()
    coordinate: tuple = ()
    conditions: tuple = ()
    method: tuple = ()
    title: object = None
    definitions: tuple = ()
    source: str = ""
    at: tuple = ()
    where: tuple = ()
    doc: tuple = ()
    declarations: tuple = ()


@dataclasses.dataclass(frozen=True, repr=False)
class AuthoredCard(_Displayed):
    """An authored block, line, initial diagram or refusal. `kind`
    distinguishes them. The record retains typed wires, statements,
    contained pieces, header, control coordinates, authored tags and
    descriptions, methods and title. A card prints these retained parts.

    See `docs/Bellman-Sym/API/stage/02-initial.md` §3."""

    kind: str
    inputs: tuple = ()
    outputs: tuple = ()
    _: dataclasses.KW_ONLY
    statements: tuple = ()
    pieces: tuple = ()
    header: tuple = ()
    coordinate: tuple = ()
    tags: tuple = ()
    describes: tuple = ()
    method: tuple = ()
    title: object = None
    conditions: tuple = ()
    definitions: tuple = ()
    source: str = ""


@dataclasses.dataclass(frozen=True, repr=False)
class DefinitionCard(_Displayed):
    """A declaration's denotation: its kind, positioned statement, denoted
    objects and cited rules, hypotheses, authored descriptions, conditions,
    methods and title. An authored block line instead answers `AuthoredCard`.

    See `docs/Bellman-Sym/API/stage/08-definitions.md` §3."""

    kind: str
    statement: object = None
    denoted: tuple = ()
    _: dataclasses.KW_ONLY
    hypotheses: tuple = ()
    describes: tuple = ()
    conditions: tuple = ()
    method: tuple = ()
    title: object = None
    definitions: tuple = ()
    source: str = ""


@dataclasses.dataclass(frozen=True, repr=False)
class StageDenotation(_Displayed):
    """The denotations of the backward and forward builders graphs, under
    their direction names. A refused direction retains its refusal sentence.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §4."""

    directions: tuple = ()
    stage: str = ""
    source: str = ""
    _: dataclasses.KW_ONLY
    definitions: tuple = ()
    conditions: tuple = ()

    def __str__(self):
        return str(self.sheet)

    __repr__ = __str__


# --- the cards ---


def card_of(record):
    """The complete card of one detached denotation answer."""
    parts = _card_parts(record)
    return _assemble(
        parts.title,
        [section.lines for section in parts.body],
        [section.lines for section in parts.footer],
    )


# One section of a card as the card prints it. `label` is the key of its
# heading in `WORDS`, `rule` for `Rule`. `heading` is its heading line,
# `Source  cons.bl`. `rows` holds its rows, each the lines the row prints on.
CardSection = namedtuple("CardSection", "label heading rows")


def card_sections(record):
    """The sections of the card of a titled denotation answer, in the order
    the card prints them, each a `CardSection`: the key of its heading, its
    heading line and its rows, each row the lines it prints on with their
    indentation. They are the sections the card forms and lays out before it
    joins them (`_card_parts`), so the lines are the card's own. A row is a
    line at the section's least indentation together with the deeper lines
    after it, which continue it: a rule the width breaks, an authored line
    whose annotation stands on the line after it, an entry of `Operations`
    with its `in:` and rule lines. A blank line belongs to no row."""
    parts = _card_parts(record)
    return tuple(
        CardSection(section.block.label, section.lines[0], _printed_rows(section.lines[1:]))
        for section in parts.body + parts.footer
    )


def _card_parts(record):
    """The parts of the card of a titled denotation answer (`_CardParts`):
    the stage card's for the stage's own answer, and an ordinary card's for
    any other record that holds a title block."""
    if isinstance(record, StageDenotation):
        return _stage_card(record)
    if getattr(record, "title", None) is None:
        raise TypeError(f"a card requires a titled denotation answer; got {type(record).__name__}")
    return _ordinary_card(record)


def _printed_rows(lines):
    """The rows of a section from the lines it prints under its heading: a
    line at the section's least indentation begins a row, and the deeper
    lines after it continue that row. A blank line belongs to no row."""
    content = [line for line in lines if line.strip()]
    if not content:
        return ()
    column = min(len(line) - len(line.lstrip(" ")) for line in content)
    rows = []
    for line in content:
        if not rows or len(line) - len(line.lstrip(" ")) == column:
            rows.append([line])
        else:
            rows[-1].append(line)
    return tuple(tuple(row) for row in rows)


def rule_rows(record, omitted=()):
    """The rows of the `Rule` section of a primitive operator's card, each on
    one line: each document the section prints (`_piece_rules`) as
    `layout.flat` writes it, so that a rule the width breaks stands on one
    line and the region it holds on follows it after two spaces,
    `𝑉 = (…)[𝑑]  on (m_f, m_h) ∈ ℝ₊₊ × ℝ₊₊`, whether the card sets that
    region at the margin of the rule's line or on a line of its own. The
    rules `omitted` holds, `Rule` records, are left out, as an evaluation
    leaves out the rules it repeats from the operation before it; a record
    is compared, not its printing, since two cards may spell one rule
    differently. A record of any other kind has no `Rule` section and
    answers none."""
    if not isinstance(record, OperatorCard):
        return ()
    documents = _piece_rules(_Names(record), record, omitted)
    return tuple(layout.flat(document) for document in documents)


# One authored line the `Source` section of a card quotes: `file`, the name of
# the file it stands in, `cons.bl`, and `number`, its line number; each None
# where the line holds no position, which the section labels by its address.
SourceLine = namedtuple("SourceLine", "file number")


def source_lines(record):
    """The authored lines the `Source` section of a titled record's card
    quotes, in the order it quotes them (`_quoted`), each a `SourceLine`:
    the file and the line number the section prints for it."""
    return tuple(
        SourceLine(_file_name(item), _line_number(item))
        if item.position
        else SourceLine(None, None)
        for item in _quoted(record)
    )


def header_line(record):
    """The line of a block's header as a `SourceLine`, read from the position
    the block's record holds beside the header's text (`AuthoredCard.header`,
    `cons.bl:21`); None for a record that holds no header or a header at no
    position."""
    header = getattr(record, "header", None)
    if not header or len(header) < 2 or not header[1]:
        return None
    positioned = _Positioned(header[1])
    return SourceLine(_file_name(positioned), _line_number(positioned))


# A block's header as the two readers of a source position take an authored
# line: by its attribute `position`, `applications/…/cons.bl:21`.
_Positioned = namedtuple("_Positioned", "position")


def card_body_lines(record, column=0):
    """The record's printed lines without its title, each indented by
    `column`: a titled record's card body, between its two heavy lines; any
    other record's own lines, a wire or a denoted object as its typed entry,
    a statement as the file writes it, a rule with its clauses, a
    hypothesis by its proposition."""
    if getattr(record, "title", None) is not None or isinstance(record, StageDenotation):
        lines = str(card_of(record)).splitlines()
        heavy = layout.horizontal_line(layout.HEAVY)
        body = lines[lines.index(heavy) + 1 :]
        if body and body[-1] == heavy:
            body = body[:-1]
        return tuple(" " * column + line if line else "" for line in body)
    names = _Names(record)
    if isinstance(record, (Wire, Denoted)):
        name, document = _name_and_carrier(names, record)
        name = name if isinstance(name, layout.Document) else layout.text(name)
        return _lines(
            layout.concat(name, " : ", document) if document is not None else name, column
        )
    if isinstance(record, Statement):
        return _lines(layout.text(record.text), column)
    if isinstance(record, Rule):
        return tuple(
            line for document in _rule_lines(names, (record,)) for line in _lines(document, column)
        )
    if isinstance(record, Declared):
        return _lines(names.document(record.statement), column)
    if isinstance(record, Hypothesis):
        return _lines(layout.text(record.proposition), column)
    if isinstance(record, Textual):
        return _lines(layout.text(str(record)), column)
    if isinstance(record, (ImageByName, ImageAtPoint, ImageSet)):
        return _lines(names.document(record.expression), column)
    if isinstance(record, MethodClause):
        return _lines(_method_documents(record).method, column)
    if isinstance(record, KernelClause):
        return tuple(line for item in record.denoted for line in card_body_lines(item, column))
    if isinstance(record, Piece):
        return card_body_lines(record.record, column)
    raise TypeError(f"printed reads a denotation answer; got {type(record).__name__}")


def _lines(document, column):
    return tuple(
        layout.render(layout.nest(column, layout.concat(" " * column, document))).split("\n")
    )


def method_card(answer):
    """The card of one row of the method table: what the method admits, the
    keyword arguments the package reads, each with its domain and whether
    the word requires it, and the perch on whose states its grid lies where
    it reads one."""
    tag = getattr(answer, "_tag", "")
    admitted = _CardBlock("admits")
    for item in answer.admits:
        admitted.row(layout.text(" ".join(item) if isinstance(item, tuple) else str(item)))
    keywords = _CardBlock("keywords")
    for name, keyword in answer.keywords.items():
        keywords.row(layout.text(f"{name}, {keyword}"))
    if not answer.keywords:
        keywords.row(layout.text("none"))
    grid = _CardBlock("grid")
    grid.row(layout.text(grid_sentence(getattr(answer, "grid", None))))
    return _assemble(
        [f"{WORDS['method-address']} !{tag}"], _blocks((admitted, keywords, grid)), ()
    )


def grid_sentence(perch):
    """The words of a row's `grid` column: the states on which the word's
    grid lies, the perch named by its word (`PERCH_WORD`), or `none` for a
    word that reads no grid."""
    if perch is None:
        return "none"
    if perch == "output":
        return "on the states of the perch at which the function the place holds stands"
    return f"on the states of the {PERCH_WORD[perch]} perch"


def definition_listing(record, key, key_width):
    """One keyed row of ``definitions.list()`` from its detached answer: the
    key, then the record's lines (`_listing_lines`) from the column after the
    key; where a line would then pass the width, the key on a line of its
    own and the record's lines under it, two columns in. The key remains the
    exact value accepted by ``definitions.denote``; no type is reconstructed
    from the retained definition table."""
    names = _Names(record)
    column = INDENT + key_width + 3
    lines = _listing_lines(names, record, column)
    if any(len(line) > layout.WIDTH for line in lines):
        return (" " * INDENT + key,) + tuple(_listing_lines(names, record, INDENT + GAP))
    head = " " * INDENT + f"{key:<{key_width}}" + " " * 3
    if lines and lines[0][:column].isspace():
        lines[0] = head + lines[0][column:]
    else:
        lines.insert(0, head.rstrip())
    return tuple(lines)


def _listing_lines(names, record, column):
    """The lines of one record of the definitions listing from column
    `column`: the object as the entry of its card's `Defines` section, laid
    out in the same columns, and its conditions on the lines below, the word
    `conditions` at that column; an authored line as the file writes it where
    it fits, and otherwise broken as the `Source` section of a card breaks
    it."""
    lines = []
    if isinstance(record, DefinitionCard):
        entries = _defines_block(names, record).entries
        starts = _column_starts(_columns(entries), at=column)
        for cells in entries:
            lines.extend(_fitted_row(cells, starts))
    elif isinstance(record, AuthoredCard):
        for statement in record.statements:
            if len(statement.text) <= layout.WIDTH - column:
                lines.append(" " * column + statement.text)
                continue
            head, tail = _split_annotation(statement.text)
            after = column + len(head) + GAP
            lines.extend(
                _authored_lines(
                    head, tail, column, after if after + len(tail) <= layout.WIDTH else None
                )
            )
    conditions = _conditions_block(names, record).entries
    if conditions:
        # the word `conditions` at the entry's column and the terms one space
        # after it, one to a line
        rows = [
            (WORDS["conditions-word"] if place == 0 else "", *cells)
            for place, cells in enumerate(conditions)
        ]
        starts = _column_starts(
            _columns(rows), at=column, fixed=(len(WORDS["conditions-word"]) + 1,)
        )
        for cells in rows:
            lines.extend(_fitted_row(cells, starts))
    return lines


def _stage_card(record):
    """The parts of the stage card (`_CardParts`): the signature of the two
    builders graphs, the declared conditions, the builders in order of
    application and the conditions, with the source, the file, the perch
    marks and the appendix in its footer. `Operations` numbers the builders
    of each graph and prints each with its `in:` and `out:` line and no rule
    line, a builder's rules standing on its own card; the sections built
    after it name an unnamed wire by its entry's number
    (`_Names.producers`)."""
    names = _Names(record)
    directions = [
        (direction, held) for direction, held in record.directions if not isinstance(held, str)
    ]
    before = [
        _signature_block(
            names,
            tuple(
                _SignatureSide(heading=WORDS[direction], inputs=held.inputs, outputs=held.outputs)
                for direction, held in directions
            ),
        )
    ]
    after = [
        _declared_block(names, record),
        _OperationRows(
            names,
            tuple(
                _OperationsPart(heading=WORDS[direction], record=held)
                for direction, held in directions
            ),
            opened=False,
        ),
        _conditions_block(names, record),
    ]
    return _card(
        names,
        record,
        title=[f"{WORDS['stage']} {record.stage}"],
        before=before,
        after=after,
        footer_head=_source_blocks(record),
        footer_tail=[_file_block(record), _perches_block(record), _appendix_block()],
    )


def _ordinary_card(record):
    """The parts of the card of a piece or a definition (`_CardParts`): the
    signature, the object a definition defines and the policy a builder is
    at before the `Where` section; the declared conditions, the rule, the
    operations, the conditions and the methods after it; the source in the
    footer. `Operations` numbers its entries, so the sections built after it
    name an unnamed wire by its entry's number (`_Names.producers`)."""
    names = _Names(record)
    before = []
    if getattr(record, "inputs", None) or getattr(record, "outputs", None):
        before.append(
            _signature_block(
                names,
                (_SignatureSide(heading=None, inputs=record.inputs, outputs=record.outputs),),
            )
        )
    if isinstance(record, DefinitionCard):
        before.append(_defines_block(names, record))
    before.append(_at_block(names, record))
    after = [_declared_block(names, record)]
    if isinstance(record, OperatorCard):
        after.append(_rule_block(names, record))
    if getattr(record, "pieces", ()):
        after.append(_OperationRows(names, (_OperationsPart(heading=None, record=record),)))
    after.append(_conditions_block(names, record))
    after.extend(_method_blocks(record))
    return _card(
        names,
        record,
        title=_title(record),
        before=before,
        after=after,
        footer_head=_source_blocks(record),
        footer_tail=[],
    )


# The parts of a card before they are joined: its title's lines, and the
# sections of its body and of its footer, each a `_Laid`.
_CardParts = namedtuple("_CardParts", "title body footer")
# One section of a card with content, and the lines it prints, its heading
# line first.
_Laid = namedtuple("_Laid", "block lines")


def _card(names, record, *, title, before, after, footer_head, footer_tail):
    """The parts of a card from its sections, built and not yet laid out
    (`_CardParts`): the column at which its short lines end fixed from them
    first (`_end_column`); the `Where` section between the sections before
    it and after it, holding the abbreviations those sections write; the
    footer's `Definitions referenced` from the lines of the title and the
    whole body."""
    end = _end_column(before + after)
    before, after = _laid(before, end), _laid(after, end)
    where = _laid([_where_block(names, record, _written((), before + after))], end)
    body = before + where + after
    footer = (
        _laid(footer_head, end)
        + _laid([_definitions_block(names, record, _written(title, body))], end)
        + _laid(footer_tail, end)
    )
    return _CardParts(title, body, footer)


def _end_column(sections):
    """The one column at which every short line of a card ends: the end of
    the longest `in:` and `out:` line of `Operations` where the card has that
    section, and the end of the longest row of `Signature` otherwise."""
    entries = [section for section in sections if isinstance(section, _OperationRows) and section]
    if entries:
        return max(section.widest() for section in entries)
    return max(
        (section.widest() for section in sections if section and section.label == "signature"),
        default=0,
    )


def _written(title, sections):
    """The text a card writes above its footer: its title and the lines of
    its body, which the footer's `Definitions referenced` reads; `sections`
    are the sections of the body with their lines (`_Laid`)."""
    return "\n".join(list(title) + [line for section in sections for line in section.lines])


def _title(record):
    """The title's lines: the address on one line where it fits, and
    otherwise broken before a `/`, the continuation two columns in; the
    grammar reads every line above the heavy line as the title."""
    head, *rest = _address(record.title).split(" / ")
    document = layout.concat(
        head, *(layout.group(layout.nest(2, layout.line(), "/ " + part)) for part in rest)
    )
    return layout.render(document).split("\n")


def _address(title):
    """The address of a card from its title block: the stage; a definition by
    its kind and name; an initial diagram or a block; a builders graph at its
    grain; a builder, the policy builder among them, and the keys of the
    piece within it; a backward or a forward builder names the pair of
    perches it joins before the block identifier, which then stands in
    parentheses, whatever grain the card stands at, since the pair names
    the builder and not only its own card."""
    head = f"{WORDS['stage']} {title.stage}"
    identity = title.identity
    keys = [str(key) for key in title.keys]
    if title.level == "stage":
        return head
    if title.level == "definition" and isinstance(identity, Identity):
        kind = WORDS.get(f"{identity.kind}-address", identity.kind.upper())
        name = identity.field or identity.address or identity.stem
        return f"{head} / {kind} {name}"
    direction = WORDS.get(f"{title.direction}-address", title.direction.upper())
    if title.level == "initial":
        segment = (
            f"{direction} {WORDS['initial']}" if not keys else f"{direction} {WORDS['block']}"
        )
    elif not keys:
        segment = f"{direction} {WORDS['builders']}"
    else:
        word = (
            WORDS["builder"]
            if title.direction != "policy"
            else f"{WORDS['policy-address']} {WORDS['builder']}"
        )
        segment = f"{direction} {word}" if title.direction != "policy" else word
    if keys:
        block = keys.pop(0)
        segment += f" {title.pair} ({block})" if title.pair else f" {block}"
    elif title.grain != "builder":
        segment += " / " + WORDS.get(title.grain, title.grain.upper())
    return " / ".join((head, segment) + tuple(keys))


# --- the sections of the body, in the order a card prints them ---


# The wires of one direction of `Signature`, under its heading, which the
# stage card gives each direction and a piece's card gives none.
_SignatureSide = namedtuple("_SignatureSide", "heading inputs outputs")


def _signature_block(names, sides):
    """The `Signature` section: the rows sub-labeled `in` and `out`, each a
    wire's name and its carrier with the colons aligned, the carrier
    continued under its own first character, and the short line above the
    `out` rows; a bundle of wires that carry one object prints once. `sides`
    is a sequence of `_SignatureSide`, one per direction on the stage card,
    each under the word of its direction."""
    block = _CardBlock("signature", fixed=(max(len(WORDS["in"]), len(WORDS["out"])) + GAP,))
    for side in sides:
        if side.heading:
            block.subheading(side.heading)
        for place, (word, wires) in enumerate(
            ((WORDS["in"], side.inputs), (WORDS["out"], side.outputs))
        ):
            if place and side.inputs and side.outputs:
                block.short()
            seen = set()
            first = True
            for wire in wires:
                name, carrier = _name_and_carrier(names, wire)
                key = (_cell_text(name), _cell_text(carrier))
                if key in seen:
                    continue
                seen.add(key)
                if isinstance(name, str):
                    block.row(word if first else "", name, _after(":", carrier))
                else:
                    # an expression in place of a name stands on its row, the
                    # carrier under the colons on the next line
                    block.wide(word if first else "", name, _after(":", carrier))
                first = False
    return block


def _after(sign, document):
    """`document` after the sign that joins it to a name, `: ` or `= `, its
    continuation lines under its own first character."""
    return layout.concat(sign, " ", layout.nest(len(sign) + 1, document))


def _typed_block(label, names, items):
    """An `At` or `Where` section: one typed entry per line, the colons
    aligned."""
    block = _CardBlock(label)
    for item in items:
        name, document = _name_and_carrier(names, item)
        block.row(name, _after(":", document) if document is not None else "")
    return block


def _defines_block(names, record):
    """A definition card's object, typed, with its rule: `𝑢 : ℝ₊₊ → ℝ,  c ↦
    c^(1 − ρ)/(1 − ρ)`; a set `Xm = ℝ₊₊`, and under a set marked
    `!categories` its category map, `0 ↦ newborn, 1 ↦ old (categories
    household_status)`; a distribution `ψ ~ LogNormal(…)` and, on the line
    under it, its measure at the written parameters, `P_ψ = measure on ℝ
    given by B ↦ …`; a derived parameter `h := 1/(1 − Γ/R)` and, on the line
    under it, its value at the calibration, `= 52.0`; a parameter or a field
    `ρ ∈ [1, ∞)`."""
    block = _CardBlock("defines")
    laws, defined = set(), set()
    for denoted in record.denoted:
        identity = denoted.identity
        kind = getattr(identity, "kind", "")
        symbol = denoted.symbol or _field_name(identity, "")
        if not symbol and isinstance(identity, Identity) and identity.subjects:
            symbol = tuple_text(tuple(identity.subjects))
        # a document is made only where the entry prints it
        held = denoted.expression
        sort = getattr(denoted.mathematical_type, "sort", ())
        if isinstance(held, CategoryCodes):
            # the set's second object, on the line under the set's row and in
            # the column of the set's rule
            block.row("", layout.concat("  ", layout.nest(2, _category_map(denoted))))
        elif kind == "set":
            rule = names.rule(held)
            block.row(symbol, _after("=", rule) if rule is not None else "")
        elif kind == "distribution" and held is not None:
            # the declared law as written is a distribution's first object,
            # and its measure at the written parameters its second
            block.row(symbol, _after("=" if identity in laws else "~", names.rule(held)))
            laws.add(identity)
        elif kind == "derived":
            # a derived parameter's definition is its first object, and its
            # value at the calibration, on the line under it, its second
            # (AMD-MT-003, build contract §5); the set its definition
            # declares stands before the definition, as a parameter's set
            # stands before its value, and the reals, the set of a derived
            # parameter whose definition declares none, are not printed
            if identity in defined:
                block.row("", _after("=", names.rule(held)))
            elif denoted.type != "ℝ":
                carrier = _carrier_document(names, denoted)
                block.row(symbol, layout.concat(_after("∈", carrier), ",  := ", names.rule(held)))
                defined.add(identity)
            else:
                block.row(symbol, _after(":=", names.rule(held)))
                defined.add(identity)
        elif kind in ("parameter", "setting") or (sort and sort[0] in ("scalar", "state")):
            carrier = _carrier_document(names, denoted)
            head = _after("∈", carrier) if carrier is not None else layout.text("")
            if held is not None and kind in ("parameter", "setting"):
                head = layout.concat(head, ",  = ", names.rule(held))
            block.row(symbol, head)
        else:
            carrier = _carrier_document(names, denoted)
            rule = names.rule(held)
            if carrier is not None:
                block.row(
                    symbol,
                    _after(
                        ":",
                        layout.group(
                            carrier, *((",", layout.line("  "), rule) if rule is not None else ())
                        ),
                    ),
                )
            elif rule is not None:
                block.row(symbol, _after("=", rule))
    return block


def _at_block(names, record):
    """The `At` section, the policy a decision builder is at: the `Denoted`
    records under a builder's `at`, typed as the policy builder types it; a
    piece's card and the stage card print none."""
    return _typed_block("at", names, record.at if isinstance(record, Composite) else ())


def _where_block(names, record, written):
    """The `Where` section, the local abbreviations a card introduces: the
    records under `where`, one line each. A `Denoted` alias is typed with its
    defining relation at the point, `𝑔_keep≻ : ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,
    𝑔_keep≻(m_f, m_h) = 𝑔≻(m_f, m_h, keep)`, and printed only where a line
    of the card writes it, that is where its name stands in `written`, the
    lines of the card's other sections, so that an alias the record holds
    and no line reads is not printed. A `Rule` is printed by its
    statement, the outputs of a law of motion `(a, h, z) = 𝑔≻(m, z_d, c,
    h_choice)`, wherever a rule of the card reads a name it defines; on the
    stage card those of every builder, each once."""
    block = _CardBlock("where")
    parts = _records(record) if isinstance(record, StageDenotation) else (record,)
    seen = set()
    for part in parts:
        if not isinstance(part, (Composite, OperatorCard)):
            continue
        for item in part.where:
            if isinstance(item, Rule):
                # the outputs of a law, `(y_f, y_p) = 𝑔≻(…)`, stand only
                # where a name the rule defines stands on the card; the whole
                # left side is looked for first, so that a name whose comma
                # no run of name characters crosses, `A≻,policy`, is found
                defined = [names.text(item.statement.left)] + re.findall(
                    f"{_NAME_CHARACTER}+", names.text(item.statement.left)
                )
                if not any(_stands_in(name, written) for name in defined):
                    continue
                for document in _rule_lines(names, (item,)):
                    if layout.flat(document) not in seen:
                        seen.add(layout.flat(document))
                        block.row(document)
                continue
            if not _stands_in(item.symbol, written):
                continue
            name, document = _name_and_carrier(names, item)
            # one alias, one signature: two aliases of one name on two
            # domains print each with its own
            key = (name, layout.flat(document) if document is not None else "")
            if key in seen:
                continue
            seen.add(key)
            block.row(name, _after(":", document) if document is not None else "")
    return block


def _declared(record):
    """The `Declared` records of a builder's `doc`, and of every builder under
    a stage's directions, each once."""
    found = []
    for part in _records(record):
        if isinstance(part, Composite):
            found.extend(declared for declared in part.doc if declared not in found)
    return found


def _declared_block(names, record):
    """The `Declared` section, the line marked `!doc` as a condition on the
    constructed output: the statement of each `Declared` the builder holds
    under `doc`, one per row, no status word; its source line stands in the
    footer's `Source` section."""
    block = _CardBlock("declared")
    for declared in _declared(record):
        block.row(names.document(declared.statement))
    return block


def _rule_block(names, record):
    """The `Rule` section, a primitive's mapping or relation: its rules as
    `_piece_rules` gives them, one per row."""
    block = _CardBlock("rule")
    for document in _piece_rules(names, record):
        block.row(document)
    return block


def _piece_rules(names, record, omitted=()):
    """The rules of a piece, each once: the rules held on its outputs; an
    output made of authored residual lines as those lines, `r₁ = …`; the
    mapping of an output that carries no name; and a solve's unnamed input as
    the residual lines it is made from, after the head the output's rule
    gives. A piece's card prints them under `Rule`, and a builder's card
    under the piece's entry of `Operations`. The rules `omitted` holds,
    `Rule` records, are left out (`rule_rows`)."""
    made, seen = [], set()

    def put(document):
        text = layout.flat(document)
        if text not in seen:
            seen.add(text)
            made.append(document)

    for wire in getattr(record, "outputs", ()):
        for document in _rule_documents(names, wire, omitted):
            put(document)
        if wire.residuals:
            for document in _residual_documents(names, wire):
                put(document)
        elif not wire.rules and not _named(wire) and wire.expression is not None:
            put(names.document(wire.expression))
    for wire in getattr(record, "inputs", ()):
        for document in _residual_documents(names, wire):
            put(document)
    return made


def _typed_outputs(names, record):
    """The outputs of a piece as its signature types them, a bundle of wires
    that carry one object once: `𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)`."""
    made, seen = [], set()
    for wire in getattr(record, "outputs", ()):
        name, carrier = _name_and_carrier(names, wire, together=True)
        name = name if isinstance(name, layout.Document) else layout.text(name)
        document = layout.concat(name, " : ", carrier) if carrier is not None else name
        if layout.flat(document) not in seen:
            seen.add(layout.flat(document))
            made.append(document)
    return made


def _rule_lines(names, rules):
    """The lines of a sequence of `Rule` records: each rule's statement, a
    membership in a set of maps as `_typed_membership` prints it, a
    conjunction of relations as `_conjunction_document` prints it, a
    property after its label, `optimality.euler: 𝑑𝑢(𝑐(m_d)) = …`, the
    statement continued under its own first character; with the image it
    holds on as a region note, `on 𝑚_d≻(Xa)`, at the right margin where the
    rule's last line leaves room for it and under the rule otherwise, and
    each clause it is read under on a line of its own after `where`."""
    made = []
    for rule in rules:
        document = _typed_membership(names, rule.statement)
        if document is None:
            document = _conjunction_document(names, rule.statement)
        if document is None:
            document = names.document(rule.statement)
        if rule.label is not None:
            document = layout.concat(f"{rule.label}: ", layout.align(document))
        if rule.on is not None:
            document = layout.concat(document, layout.margin("on " + names.text(rule.on)))
        made.append(document)
        for clause in rule.where:
            made.append(layout.concat("where ", names.document(clause)))
    return made


# the statements that bind at least as tightly as a relation, which stand as
# members of a conjunction without parentheses
_RELATION_FORMS = (Compare, Complementarity, Member, IsInteger, Not)


def _conjunction_document(names, statement):
    """A rule's statement that is a conjunction of relations, nested on the
    left, printed on one line where it fits and otherwise with each later
    member on a line of its own at the rule's column, after `∧ `, as
    `card-redesign.md` §3 draws the two clauses of the pension worker's
    rule: `𝑑𝑢(𝑐) = β · 𝑑𝑉_f≻(y_f, y_p) ⟂ y_f ≥ 0` over `∧ 𝑑𝑢(𝑐) = …`. A
    member broken over lines continues two columns past the rule's column,
    so that a later member continues under its own first character. None
    for a statement of any other form, or with a member that is no
    relation, whose conjunction `format_document` prints with the
    parentheses it needs."""
    members, held = [], statement
    while isinstance(held, And):
        members.insert(0, held.right)
        held = held.left
    members.insert(0, held)
    if len(members) == 1 or not all(isinstance(member, _RELATION_FORMS) for member in members):
        return None
    parts = [names.document(members[0])]
    for member in members[1:]:
        parts.extend((layout.line(), "∧ ", names.document(member)))
    return layout.group(*parts)


def _typed_membership(names, statement):
    """A statement that functions lie in a set of maps with their
    feasibility, `𝑐 ∈ (Xm → ℝ₊₊) ∧ 𝑐(m_d) ∈ Γ(m_d)` (the rule of an
    Evaluation, the identity into the declared carrier), printed as the card
    prints a declared carrier: the membership as the functions' type, on one
    line with the feasibility after a comma, `𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈
    Γ(m_d)`, and where that does not fit, the feasibility conditions together
    on the next line where they fit (`_carrier_document`); None for a
    statement of any other form (`typed_expressions.membership_parts`)."""
    parts = S.membership_parts(statement)
    if parts is None:
        return None
    typed = layout.concat(names.document(parts.subject), " : ")
    if not parts.conditions:
        return layout.concat(typed, layout.group(names.document(parts.base)))
    conditions = []
    for condition in parts.conditions:
        if conditions:
            conditions.extend((",", layout.line("  ")))
        conditions.append(names.document(condition))
    return layout.concat(
        typed,
        layout.group(
            names.document(parts.base), ",", layout.line("  "), layout.group(*conditions)
        ),
    )


def _rule_documents(names, wire, omitted=()):
    """The rules the operation that writes `wire` declares on it, as the
    record holds them under `Wire.rules`, which a piece's `Rule` section and
    its entry of `Operations` print, less the `Rule` records `omitted`
    holds."""
    return _rule_lines(names, tuple(rule for rule in wire.rules if rule not in omitted))


def _residual_documents(names, wire):
    """The residual lines of an unnamed wire made from authored lines, as the
    record holds them under `Wire.residuals`, `r₁ = …`: on the output of the
    Aggregation that forms them and on the input of the solve that reads
    them."""
    return _rule_lines(names, wire.residuals)


def _output_documents(names, wire):
    """What an operation writes on one wire: its name where it has one, its
    expression otherwise."""
    if _named(wire):
        return [layout.text(_wire_name(names, wire))]
    if wire.expression is not None:
        return [names.document(wire.expression)]
    return [layout.text(wire.name)]


# The pieces of one record in `Operations`, under its heading, which the
# stage card gives each direction and a builder's card gives none.
_OperationsPart = namedtuple("_OperationsPart", "heading record")


# One entry of `Operations`: the column at which its number stands, two
# columns in, or four under the direction it belongs to on the stage card;
# its number, empty for a sub-builder and for an authored piece; its depth
# among the entries it stands inside; its key; the names it reads; the
# documents of what it writes; and the documents of its rules.
_Entry = namedtuple("_Entry", "column number depth key reads writes rules")


class _OperationRows:
    """The `Operations` section: its entries, numbered as the listings number
    the pieces: on a builder's card the primitives in order of application,
    the sub-builders opened and their entries carrying no number; on the stage
    card the builders of each graph, under the word of its direction,
    numbered in order of application, not opened and with no rule line, since
    a builder's rules stand on its own card. Every entry is made from
    its record when the section is built, its number, its key, what it reads,
    an earlier output that has no name by that entry's number, `(1)`, what it
    writes and its rules, so that the numbers and the column at which the
    short lines end are fixed before any line is laid out. The outputs of a
    numbered entry are recorded as written by that entry, for the entries and
    the sections after it (`_Names.producers`)."""

    label = "operations"
    heading = WORDS["operations"]

    def __init__(self, names, parts, *, opened=True):
        self.names, self.opened = names, opened
        self.items = []
        for part in parts:
            column = INDENT
            if part.heading:
                self.items.append(_Heading(text=part.heading))
                column += GAP
            # each graph numbers its builders from one and prints each rule
            # once
            self.count, self.producers, self.printed = 0, {}, set()
            self._add(
                part.record,
                column,
                0,
                {wire.identity for wire in getattr(part.record, "inputs", ())},
            )

    def _add(self, record, column, depth, inputs):
        """The entries of the pieces of `record` in order, their keys two
        columns in at each `depth`: a primitive's entry numbered, a
        sub-builder's entries beneath its own where the card opens it."""
        for piece in getattr(record, "pieces", ()):
            child = piece.record
            composite = bool(getattr(child, "pieces", ())) and self.opened
            number = ""
            if not composite and isinstance(child, (OperatorCard, Composite)):
                self.count += 1
                number = str(self.count)
            reads, writes = self._reads(child, inputs), self._writes(child)
            if number:
                for wire in child.outputs:
                    self.producers.setdefault(wire.identity, number)
                    self.names.producers.setdefault(wire.identity, number)
            key = str(piece.key).lstrip("←→ ")
            self.items.append(
                _Entry(column, number, depth, key, reads, writes, self._rules(child, composite))
            )
            if composite:
                self._add(child, column, depth + 1, inputs)

    def _reads(self, child, inputs):
        """What an entry reads: a builder input or an earlier output by its
        name, an unnamed one by the number of the entry that wrote it,
        `(1)`."""
        found = []
        for wire in getattr(child, "inputs", ()):
            if _named(wire) or wire.identity in inputs:
                text = _wire_name(self.names, wire)
            elif wire.identity in self.producers:
                text = f"({self.producers[wire.identity]})"
            else:
                text = _wire_name(self.names, wire)
            if text not in found:
                found.append(text)
        return found

    def _writes(self, child):
        """What an entry writes: each output by its name, or by its
        expression where it has none, the wires of one bundle once."""
        made, seen = [], set()
        for wire in getattr(child, "outputs", ()):
            for document in _output_documents(self.names, wire):
                if layout.flat(document) not in seen:
                    seen.add(layout.flat(document))
                    made.append(document)
        return made

    def _rules(self, child, composite=False):
        """The rule lines of an entry: what its piece's own card prints under
        `Rule` (`_piece_rules`), each rule once on the card, at the operation
        that forms it, so that an Evaluation, whose outputs carry the rules of
        the operation it names, repeats none, and a builder or a sub-builder
        opened on the card prints only the rules none of its pieces holds; an
        operation or a builder left with no line prints its outputs as its
        signature types them, an Evaluation the declared carrier with its
        feasibility, `𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)`. An authored piece of an
        initial diagram holds no rule and prints none, and nor does a builder
        on the stage card, where the section is not opened: its rules stand
        on its own card."""
        if not self.opened:
            return []
        inner = set()
        for part in _records(child) if composite else ():
            if part is not child:
                inner.update(layout.flat(held) for held in _piece_rules(self.names, part))
        made = []
        for document in _piece_rules(self.names, child):
            text = layout.flat(document)
            if text not in self.printed and text not in inner:
                self.printed.add(text)
                made.append(document)
        if made or not isinstance(child, (OperatorCard, Composite)):
            return made
        return _typed_outputs(self.names, child)

    def __bool__(self):
        return any(isinstance(item, _Entry) for item in self.items)

    def _width(self):
        """The width of the column of numbers: its longest number."""
        entries = [item for item in self.items if isinstance(item, _Entry)]
        return max((len(entry.number) for entry in entries), default=0)

    def widest(self):
        """The end of the section's longest `in:` and `out:` line."""
        width = self._width()
        return max(
            (
                len(line)
                for item in self.items
                if isinstance(item, _Entry)
                for line in _in_out_lines(_entry_column(item, width), item.reads, item.writes)
            ),
            default=0,
        )

    def lines(self, end=0):
        """The section's lines: its heading, then its entries, a blank line
        between two, each direction's word two columns in before its
        entries, and every short line ending at column `end`."""
        width = self._width()
        made = [self.heading]
        for place, item in enumerate(self.items):
            if place and not isinstance(self.items[place - 1], _Heading):
                made.append("")
            if isinstance(item, _Heading):
                made.append(" " * INDENT + item.text)
            else:
                made.extend(_entry_lines(item, width, end))
        return made


def _entry_column(entry, width):
    """The column at which an entry's key, its `in:`, its short line and its
    `rule:` stand: after its number, right-aligned in a column `width` wide,
    and two spaces, and two columns in at each depth."""
    return entry.column + (width + GAP if width else 0) + GAP * entry.depth


def _entry_lines(entry, width, end):
    """The lines of one entry of `Operations`: its number and its key; then,
    at the key's column, its `in:` and `out:` line, and, where it has rule
    lines, its short line, ending at column `end`, and its rule lines."""
    at = _entry_column(entry, width)
    number = f"{entry.number:>{width}}" + " " * GAP if width else ""
    lines = [(" " * entry.column + number + " " * (GAP * entry.depth) + entry.key).rstrip()]
    lines.extend(_in_out_lines(at, entry.reads, entry.writes))
    if entry.rules:
        lines.append(" " * at + layout.horizontal_line(layout.LIGHT, max(end - at, 1)))
        lines.extend(_labeled_rules(at, entry.rules))
    return lines


def _in_out_lines(at, reads, writes):
    """The `in:` and `out:` line of an entry whose key stands at column `at`:
    what it reads after `in:`, and `out:` at column 40, on the same line where
    the inputs end by column 38 and on a line of its own otherwise, so that
    the outputs of a card stand in one column. Each list stands on one line
    where it fits and breaks after every comma otherwise, its items under the
    first. An output wider than the room after `out:` at column 40, a mapping
    written in full, stands on the line after the inputs with `out:` at the
    key's column, so that it has the width of the card."""
    inputs = _labeled_list(at, WORDS["in-label"], reads)
    outputs = _labeled_list(OUT_COLUMN, WORDS["out-label"], writes)
    room = layout.WIDTH - OUT_COLUMN - len(WORDS["out-label"]) - 1
    if any(len(layout.flat(item)) > room for item in writes) or any(
        len(line) > layout.WIDTH for line in outputs
    ):
        return inputs + _labeled_list(at, WORDS["out-label"], writes)
    if len(inputs) == 1 and len(inputs[0]) <= OUT_COLUMN - GAP:
        return [inputs[0].ljust(OUT_COLUMN) + outputs[0][OUT_COLUMN:]] + outputs[1:]
    return inputs + outputs


def _labeled_list(at, label, items):
    """`label` at column `at`, then the items after one space, `𝑐≻, 𝑚_d≻`,
    on one line where they fit and one to a line otherwise, each under the
    first."""
    parts = []
    for place, item in enumerate(items):
        if place:
            parts.extend((",", layout.line()))
        parts.append(item if isinstance(item, layout.Document) else layout.text(item))
    listed = layout.align(layout.bounded(DEPTH, layout.group(*parts)))
    return layout.render(layout.concat(" " * at, label, " ", listed)).split("\n")


def _labeled_rules(at, documents):
    """The rule lines of an entry whose key stands at column `at`: `rule:` and
    the first rule, each further rule on a line of its own under the first
    rule's first character, every rule continued under its own first
    character, and no deeper than `DEPTH` columns past it."""
    label = WORDS["rule-label"] + " "
    column = at + len(label)
    lines = []
    for place, document in enumerate(documents):
        head = " " * at + label if place == 0 else " " * column
        lines.extend(
            layout.render(
                layout.concat(head, layout.nest(column, layout.bounded(DEPTH, document)))
            ).split("\n")
        )
    return lines


def _conditions_block(names, record):
    """The `Conditions` section: one line per condition, its term, the owning
    piece named on a builder's or the stage's card; the declared statement,
    which stands under `Declared`, is no condition of the section, so that no
    condition is printed twice."""
    block = _CardBlock("conditions")
    declared = {names.text(item.statement) for item in _declared(record)}
    if isinstance(record, (Composite, StageDenotation)):
        for owner, condition in _conditions_with_owners(
            names, record, whole_names=isinstance(record, StageDenotation)
        ):
            if _condition_key(names, condition) in declared:
                continue
            block.row(owner, _condition_document(names, condition))
    else:
        seen = declared
        for condition in _own_conditions(record):
            text = _condition_key(names, condition)
            if text not in seen:
                seen.add(text)
                block.row(_condition_document(names, condition))
    return block


def _condition_key(names, condition):
    """The text of a condition's term, by which a card prints it once; the
    name of a condition a bound method requires, which holds no term."""
    if condition.predicate is None:
        return condition.condition
    return names.text(condition.predicate)


def _condition_document(names, condition):
    """The printed condition: its term, or, for a condition a bound method
    requires, its name, its sentence and its status, broken at the spaces
    where it does not fit (specification 0.6 §4.1)."""
    if condition.predicate is not None:
        return names.document(condition.predicate)
    words = f"{condition.condition}: {condition.explanation}   [{condition.status}]".split(" ")
    parts = [words[0]]
    for word in words[1:]:
        parts.extend((layout.softline(), word))
    return layout.group(layout.nest(2, *parts))


def _own_conditions(record):
    """The conditions a record holds as terms, and those a bound method
    requires, which print by their names; any other condition without a term
    is no condition of the card."""
    return tuple(
        condition
        for condition in getattr(record, "conditions", ())
        if condition.predicate is not None or condition.condition in METHOD_CONDITIONS
    )


def _conditions_with_owners(names, record, *, whole_names=False):
    """Every condition of a composite once, with the piece that owns it: the
    deepest piece holding it, named by its key where it stands directly in the
    card's record, and by its whole name, the spelling of its identity, where
    it stands deeper or on the stage card; a condition no piece holds by its
    first subject."""
    found, seen = [], set()

    def walk(part, nested):
        # the conditions of the pieces within `part` that hold no pieces
        for piece in getattr(part, "pieces", ()):
            key = piece.name if whole_names or nested else str(piece.key).lstrip("←→ ")
            walk(piece.record, True)
            if getattr(piece.record, "pieces", ()):
                continue
            for condition in _own_conditions(piece.record):
                text = _condition_key(names, condition)
                if text not in seen:
                    seen.add(text)
                    found.append((key, condition))

    for _, held in getattr(record, "directions", ()):
        if not isinstance(held, str):
            walk(held, False)
    walk(record, False)
    for condition in _own_conditions(record):
        text = _condition_key(names, condition)
        if text in seen:
            continue
        seen.add(text)
        found.append((_owner_of(names, condition), condition))
    return found


def _owner_of(names, condition):
    """The owner of a condition no piece of the card holds, from its first
    subject: a definition by its symbol, `𝑢`; a function, a choice or a field
    of the file by its name; anything else, a line or the result of an
    operation, by the spelling of its identity."""
    subject = condition.entries[0] if condition.entries else ""
    if not isinstance(subject, Identity):
        return str(subject)
    return names.symbols.get(subject) or _field_name(subject, str(subject))


def _method_blocks(record):
    """A `Method` section for each method bound on the record, each followed
    by an `Options` section where the method sets options."""
    blocks = []
    for method in getattr(record, "method", ()):
        documents = _method_documents(method)
        blocks.append(_CardBlock("method").row(documents.method))
        if documents.options:
            option_block = _CardBlock("options")
            for option in documents.options:
                option_block.row(option)
            blocks.append(option_block)
    return blocks


# The rows of one bound method: the `Method` row and the `Options` rows.
_MethodDocuments = namedtuple("_MethodDocuments", "method options")


def _method_documents(method):
    """The `Method` row, the components as the clause writes them on one
    line, with the place at the margin, and the `Options` rows,
    `name = value`, one per pair the clause's `options` holds, as a
    `_MethodDocuments`."""
    document = layout.text(method.written or "none")
    if method.address:
        document = layout.concat(document, layout.margin(str(method.address)))
    options = [layout.text(f"{key} = {value}") for key, value in method.options]
    return _MethodDocuments(method=document, options=options)


# --- the footer ---


def _source_blocks(record):
    """The `Source` sections, excerpts of the files the card rests on: the
    file named once in a section's heading, `Source  cons.bl`, then each
    authored line the card quotes from it, its line number and the line as
    the file writes it. Where the lines stand in several files, each file has
    a section of its own, the stage file's first (`_quoted`), and the lines
    of every section stand in one column. The annotation `:: [id=…]` stands
    in one column two spaces after the longest statement where every
    annotation then ends within the width, and otherwise every annotation
    stands on the line after its statement, two columns in, as the
    continuation of a statement wider than the width does. A line with no
    position is labeled by its address, and where such a line stands among
    the lines of several files, one section labels each line by its file's
    name with the number, `cons.bl:32`."""
    statements = _quoted(record)
    files = list(dict.fromkeys(_file_name(item) for item in statements if item.position))
    by_file = len(files) > 1 and all(
        item.position and _line_number(item) is not None for item in statements
    )
    if by_file:
        blocks = {
            name: _CardBlock("source", heading=WORDS["source"] + " " * GAP + name)
            for name in files
        }
    else:
        heading = WORDS["source"] + (" " * GAP + files[0] if len(files) == 1 else "")
        blocks = {None: _CardBlock("source", heading=heading)}
    if not statements:
        return list(blocks.values())
    positions = [_position_text(item, one_file=len(files) == 1 or by_file) for item in statements]
    width = max(len(text) for text in positions)
    statement_at = INDENT + width + GAP
    split = [_split_annotation(item.text) for item in statements]
    annotated = [(head, tail) for head, tail in split if tail]
    annotation_at = None
    if annotated:
        column = statement_at + max(len(head) for head, _ in annotated) + GAP
        if all(column + len(tail) <= layout.WIDTH for _, tail in annotated):
            annotation_at = column
    for item, position, (head, tail) in zip(statements, positions, split):
        lines = _authored_lines(head, tail, statement_at, annotation_at)
        lines[0] = " " * INDENT + position + lines[0][INDENT + len(position) :]
        block = blocks[_file_name(item) if by_file else None]
        for line in lines:
            block.row(layout.text(line[INDENT:]))
    return list(blocks.values())


def _quoted(record):
    """The authored lines the `Source` section quotes, in its order: the
    lines the record rests on (`_statements`), by line number where every
    one of them holds one, and as held otherwise. Where they stand in more
    than one file, the lines of the stage file the record names come first,
    then those of each other file in the order the record holds them, each
    file's lines by number."""
    statements = list(_statements(record))
    numbered = [(_line_number(item), place, item) for place, item in enumerate(statements)]
    if all(number is not None for number, _, _ in numbered):
        own = PurePosixPath(str(getattr(record, "source", "") or "")).name
        files = list(dict.fromkeys(_file_name(item) for item in statements))
        rank = {name: (name != own, place) for place, name in enumerate(files)}
        statements = [
            item
            for _, _, item in sorted(
                numbered, key=lambda entry: (rank[_file_name(entry[2])], *entry[:2])
            )
        ]
    return statements


def _split_annotation(text):
    """An authored line's statement and its annotation `:: [id=…]`, each
    without the spaces around it; an empty annotation where it holds none."""
    head, separator, tail = text.partition("::")
    if not separator:
        return text.rstrip(), ""
    return head.rstrip(), (separator + tail).strip()


def _authored_lines(head, tail, at, annotation_at=None):
    """The lines of one authored statement standing at column `at`: the
    statement, broken at a run of spaces where it is wider than the width,
    each continuation two columns in; its annotation `tail` at column
    `annotation_at` on the statement's line where one is given and the
    statement fits on that line, and otherwise on the lines after the
    statement, two columns in."""
    first, *rest = _segments(head, layout.WIDTH - at, layout.WIDTH - at - GAP)
    lines = [" " * at + first] + [" " * (at + GAP) + segment for segment in rest]
    if not tail:
        return lines
    if annotation_at is not None and not rest and len(lines[0]) + GAP <= annotation_at:
        lines[0] = lines[0].ljust(annotation_at) + tail
        return lines
    room = layout.WIDTH - at - GAP
    lines.extend(" " * (at + GAP) + segment for segment in _segments(tail, room, room))
    return lines


def _statements(record):
    """The authored lines a record rests on, as held: a piece's own line where
    it has one, the lines its kernel cites otherwise; a builder's block's
    lines from its pieces; a stage's from its builders; a definition's own."""
    identity = getattr(getattr(record, "title", None), "identity", None)
    found = []

    def add(items):
        for item in items:
            if isinstance(item, Statement) and item not in found:
                found.append(item)

    if isinstance(record, DefinitionCard):
        statement = record.statement
        held = (statement,) if isinstance(statement, Statement) else tuple(statement or ())
        if record.kind not in ("g", "G"):
            # a definition's source is its declaration; a block's line that
            # reads it stands on that block's cards
            add(item for item in held if not item.doc and "." not in str(item.address))
        else:
            add(held)
        return tuple(found)
    if isinstance(record, OperatorCard):
        # the lines the kernel cites; a line marked `!doc` is the builder's
        # declared condition and stands on the builder's card, unless the
        # piece is the one that line forms
        kernel = record.kernel
        held = tuple(kernel.statements) if kernel is not None else ()
        own = getattr(identity, "address", None)
        add(item for item in held if not item.doc or str(item.address) == own)
        return tuple(found)
    add(getattr(record, "statements", ()))
    if isinstance(record, Composite):
        # the line marked `!doc` of a builder, as the file writes it, whose
        # statement stands under `Declared`
        add(declared.source for declared in record.doc)
        # the lines declaring the builder's multipliers, which form no piece
        add(record.declarations)
    block = getattr(identity, "block", None) if isinstance(identity, Identity) else None
    for part in _records(record):
        if part is record:
            continue
        for item in _statements(part):
            if block is None or str(item.address).split(".", 1)[0] == block:
                add((item,))
    return tuple(found)


def _line_number(statement):
    _, separator, location = statement.position.rpartition(":")
    return int(location) if separator and location.isdigit() else None


def _file_name(statement):
    """The name of the file a positioned statement stands in, `cons.bl`."""
    path, separator, _ = statement.position.rpartition(":")
    return PurePosixPath(path if separator else statement.position).name


def _position_text(statement, one_file=True):
    """The label of an authored line in the `Source` section: its line
    number, `32`, where the card's lines stand in one file, and the file's
    name with it, `cons.bl:32`, where they stand in several; the address word
    of a line that has no position."""
    if not statement.position:
        return str(statement.address)
    path, separator, location = statement.position.rpartition(":")
    if not separator:
        return PurePosixPath(statement.position).name
    return location if one_file else f"{PurePosixPath(path).name}:{location}"


def _segments(text, first, rest):
    """An authored line in pieces no wider than `first` and then `rest`
    columns, broken at a run of spaces (`_space_cut`), the run dropped at the
    break as the `Source` section drops it before `::`; a line that fits is
    one piece. A run of characters with no space in it is broken before an
    operator sign or after a comma, and at the width where it has neither, so
    that no quoted line stands over the width and no character is dropped:
    nothing is abbreviated."""
    lines = text.split("\n")
    if len(lines) > 1:
        # an authored line that holds a newline is laid out line by line
        return [
            piece
            for place, held in enumerate(lines)
            for piece in _segments(held, first if place == 0 else rest, rest)
        ]
    pieces, remaining, width = [], text, max(first, 1)
    while len(remaining) > width:
        cut = _space_cut(remaining, width)
        if cut > 0:
            head, tail = remaining[:cut].rstrip(), remaining[cut:].lstrip()
        else:
            cut = _run_cut(remaining, width)
            head, tail = remaining[:cut], remaining[cut:]
        if not head or not tail:
            break
        pieces.append(head)
        remaining, width = tail, max(rest, 1)
    pieces.append(remaining)
    return pieces


def _space_cut(text, width):
    """The place of the last space among the first `width + 1` characters of
    an authored line that stands inside no argument list of an application,
    `𝑢(c, h_choice)`, so that a broken line keeps each application whole where
    it can, and of the last space among them otherwise; 0 where there is
    none."""
    last = outside = 0
    # for each bracket open at the place, whether it opens an argument list
    opened = []
    for place, character in enumerate(text[: width + 1]):
        if character in "([{":
            opened.append(_opens_arguments(text, place))
        elif character in ")]}" and opened:
            opened.pop()
        elif character == " " and place > 0:
            last = place
            outside = place if not any(opened) else outside
    return outside or last


def _run_cut(run, width):
    """The column at which a run of characters wider than `width` is broken:
    before the last sign `+`, `*`, `^` or `/` within the width, after the
    last comma within it otherwise, and at the width where it has neither."""
    signs = [place for place in range(1, width + 1) if run[place] in "+*^/"]
    if signs:
        return signs[-1]
    commas = [place + 1 for place in range(width) if run[place] == ","]
    if commas:
        return commas[-1]
    return width


def _definitions_block(names, record, written):
    """The `Definitions referenced` section: every name the card writes
    above its footer (`written`, the lines of its title and body) that the
    definitions hold, with the key that answers it, and no other, in the
    order the record holds them, which is the order of the stage's
    definitions table, the file's order of declaration, an object a block
    file defines followed by that file's name and the line of its definition,
    `cons_egm.bl:3`; a definition's card does not list the object it
    defines. The names stand in a column at least `NAME_WIDTH` wide, so that
    the keys of short names stand at one column on every card."""
    block = _CardBlock("definitions", least=(NAME_WIDTH,))
    own = {denoted.identity for denoted in getattr(record, "denoted", ())}
    for name, denoted in names.written_in(written, own):
        # an object a block file defines is followed by that file and line
        written_at = getattr(denoted, "written_at", "")
        block.row(name, str(denoted.identity), *((written_at,) if written_at else ()))
    return block


def _file_block(record):
    """The `File` section of the stage card: the stage file the record was
    elaborated from, where it holds one. A path wider than the card breaks
    after a `/`, as `sheets.PathLine` breaks the same path in the subtitle of
    the stage's description."""
    block = _CardBlock("file")
    if getattr(record, "source", ""):
        parts = record.source.split("/")
        block.row(
            layout.group(
                *[layout.concat(part + "/", layout.softline("")) for part in parts[:-1]], parts[-1]
            )
        )
    return block


def _perches_block(record):
    """The perch marks a stage card writes: `≺  arrival, written [<]`."""
    perches = []
    for part in _records(record):
        for wire in tuple(getattr(part, "inputs", ())) + tuple(getattr(part, "outputs", ())):
            perch = getattr(wire.identity, "perch", None)
            if WRITTEN_MARK.get(perch) and perch not in perches:
                perches.append(perch)
    block = _CardBlock("perches")
    for perch in sorted(perches, key=("arvl", "cntn").index):
        block.row(PERCH_MARK[perch], f"{PERCH_WORD[perch]}, written {WRITTEN_MARK[perch]}")
    block.row("", WORDS["unmarked"])
    return block


def _appendix_block():
    """The `Appendix` section of the stage card: the appendix of the
    language's specification that gives the meaning of a stage, by name and
    path."""
    return (
        _CardBlock("appendix")
        .row(layout.text(WORDS["appendix-name"]))
        .row(layout.text(WORDS["appendix-path"]))
    )


def _blocks(blocks, end=0):
    """The lines of each section that has content, in order, its short lines
    ending at column `end`."""
    return [block.lines(end) for block in blocks if block]


def _laid(blocks, end=0):
    """Each section that has content, in order, with the lines it prints
    (`_Laid`), its short lines ending at column `end`."""
    return [_Laid(block, block.lines(end)) for block in blocks if block]


# --- the columns of a section ---


INDENT = 2  # the rows of a section stand two columns in, under its heading
GAP = 2  # a column is its longest entry plus two
OUT_COLUMN = 40  # the `out:` of every entry of `Operations`


# the least width of the column of names of `Definitions referenced`, so that
# the key of a name of up to four characters stands at column eight
NAME_WIDTH = 6


# the continuations of an entry stand two columns past the entry's operator,
# once per operator, and at most this many columns past the column the entry
# starts at, so that a deeply nested expression keeps the rest of the line
# for its text
DEPTH = 20


def _column_starts(columns, *, at=INDENT, least=(), fixed=()):
    """The start column of each column of a table, the last column open:
    every other column is sized to its longest entry plus two, not narrower
    than its least width, or to its fixed width where one is given."""
    starts, column = [], at
    for place, entries in enumerate(columns):
        starts.append(column)
        if place == len(columns) - 1:
            break
        if place < len(fixed) and fixed[place]:
            column += fixed[place]
            continue
        width = max((len(_cell_text(entry)) for entry in entries), default=0) + GAP
        floor = least[place] if place < len(least) else 0
        column += max(width, floor)
    return starts


def _columns(rows):
    """The cells of each column of a table that a further cell follows on
    their row: a row's last cell is open and sizes no column, so that a rule
    standing alone on a `Where` row leaves the column of names to the
    names."""
    width = max((len(row) for row in rows), default=0)
    return [[row[place] for row in rows if place + 1 < len(row)] for place in range(width)]


def _cell_text(cell):
    """The text of a cell: a document as it reads on one line, a string as it
    is."""
    return cell if isinstance(cell, str) else layout.flat(cell)


# The three kinds of row of a section laid out as a table: an entry row, its
# cells in the section's columns, `wide` where its name is an expression that
# stands on its row and its carrier on the next; a sub-heading, the word of
# the direction the rows under it belong to on the stage card; and the short
# line above the `out` rows of `Signature`.
_Row = namedtuple("_Row", "cells wide")
_Heading = namedtuple("_Heading", "text")
_Short = namedtuple("_Short", ())


class _CardBlock:
    """One section of a card laid out as a table: its heading at column zero,
    then its rows two columns in, or four under a sub-heading, every column
    but the last as wide as its longest entry plus two and not narrower than
    its least width, or as its fixed width where one is given, and the last
    cell open, a break continuing under it. A section with no entry row is
    not printed."""

    def __init__(self, label, *, least=(), fixed=(), heading=None):
        self.label = label
        self.heading = WORDS[label] if heading is None else heading
        self.rows = []
        self.least, self.fixed = least, fixed

    def row(self, *cells):
        self.rows.append(_Row(cells=tuple(cells), wide=False))
        return self

    def wide(self, *cells):
        """A row whose second-last cell is an expression standing in place of
        a name: it stands on the row, breaking under its own column, and the
        last cell follows on the next line at the last column; the widths of
        the columns are read from the other rows."""
        self.rows.append(_Row(cells=tuple(cells), wide=True))
        return self

    def subheading(self, text):
        """The word of a direction, two columns in, over the rows after it."""
        self.rows.append(_Heading(text=text))
        return self

    def short(self):
        """The short line above the `out` rows of `Signature`, from the
        column of the names to the column at which the card's short lines
        end."""
        self.rows.append(_Short())
        return self

    @property
    def entries(self):
        return [row.cells for row in self.rows if isinstance(row, _Row) and not row.wide]

    def __bool__(self):
        return any(isinstance(row, _Row) for row in self.rows)

    def _starts(self):
        """The start column of each column: the rows two columns in, and four
        where a sub-heading stands among them; the expression a wide row holds
        in place of a name sizes no column."""
        at = INDENT + (GAP if any(isinstance(row, _Heading) for row in self.rows) else 0)
        sized = [
            row.cells[:-2] + ("", row.cells[-1]) if row.wide else row.cells
            for row in self.rows
            if isinstance(row, _Row)
        ]
        return _column_starts(_columns(sized), at=at, least=self.least, fixed=self.fixed)

    def _row_lines(self, row, starts):
        """The lines of one row within the width (`_fitted_row`); a wide
        row's last cell on the line after its name, at the last column where
        it fits there."""
        cells = row.cells
        if not row.wide:
            return _fitted_row(cells, starts)
        lines = _rendered_row(("",) * (len(cells) - 1) + (cells[-1],), starts)
        if any(len(line) > layout.WIDTH for line in lines):
            lines = _below(cells, starts)
        return _rendered_row(cells[:-1], starts) + lines

    def widest(self):
        """The end of the section's longest row: the column at which the
        short lines of a card with no `Operations` end."""
        starts = self._starts()
        return max(
            (
                len(line)
                for row in self.rows
                if isinstance(row, _Row)
                for line in self._row_lines(row, starts)
            ),
            default=0,
        )

    def lines(self, end=0):
        """The section's lines: its heading, then its rows, the word of a
        direction two columns in, and the short line ending at column
        `end`."""
        starts = self._starts()
        made = [self.heading]
        for row in self.rows:
            if isinstance(row, _Heading):
                made.append(" " * INDENT + row.text)
            elif isinstance(row, _Short):
                made.append(
                    " " * starts[1] + layout.horizontal_line(layout.LIGHT, max(end - starts[1], 1))
                )
            else:
                made.extend(self._row_lines(row, starts))
        return made


def _fitted_row(cells, starts):
    """The lines of one row within the width: the row as `_rendered_row` lays
    it out, and its last cell on the lines after the others (`_below`) where
    a line of the row would pass the width, or where the row would break the
    argument list of an application that stays whole under the row; the
    others print no line where they hold no text, as on the row of a set's
    category map (`_defines_block`)."""
    lines = _rendered_row(cells, starts)
    if len(cells) < 2:
        return lines
    over = any(len(line) > layout.WIDTH for line in lines)
    if not over and not _breaks_an_application(lines):
        return lines
    below = _below(cells, starts)
    if over or not _breaks_an_application(below):
        others = _rendered_row(cells[:-1], starts) if any(map(_cell_text, cells[:-1])) else []
        return others + below
    return lines


def _breaks_an_application(lines):
    """Whether a line of `lines` but the last ends inside the argument list of
    an application, `𝑔≻(m_d,` before `c)`."""
    opened = []
    for line in lines[:-1]:
        for place, character in enumerate(line):
            if character in "([{":
                opened.append(_opens_arguments(line, place))
            elif character in ")]}" and opened:
                opened.pop()
        if any(opened):
            return True
    return False


def _opens_arguments(text, place):
    """Whether the bracket at `place` of a printed or authored line opens the
    argument list of an application: a `(` directly after a name,
    `𝑢(c)`."""
    return text[place] == "(" and place > 0 and bool(re.match(_NAME_CHARACTER, text[place - 1]))


def _below(cells, starts):
    """The lines of a row's last cell standing under the row, two columns in
    from the cell before it, so that a row wider than the card keeps the
    width."""
    return _rendered_row((cells[-1],), [starts[len(cells) - 2] + GAP])


def _rendered_row(cells, starts):
    """The lines of one row: every cell but the last as text at its column,
    the last as a document nested at its column, so that a break continues
    under it, and no deeper than `DEPTH` columns past it."""
    parts, column = [], 0
    for cell, start in zip(cells[:-1], starts):
        text = _cell_text(cell)
        parts.append(" " * max(start - column, 0) + text)
        column = max(start, column) + len(text)
    last, start = cells[-1], starts[len(cells) - 1]
    at = max(start, column)
    document = last if isinstance(last, layout.Document) else layout.text(last)
    row = layout.concat(
        *parts, " " * max(start - column, 0), layout.nest(at, layout.bounded(DEPTH, document))
    )
    return layout.render(row).split("\n")


def _assemble(title, body, footer):
    """The card: the title and the heavy line under it; the sections of the
    body, a blank line between two; the light line across the card before
    the sections of the footer where the card has a body, and the sections of
    the footer, a blank line between two; and the heavy line closing it. A
    card with no body prints no light line: the heavy line under its title
    already stands above its footer, and two lines across the card would
    stand one under the other."""
    lines = list(title) + [layout.horizontal_line(layout.HEAVY)]
    for place, section in enumerate(body):
        if place:
            lines.append("")
        lines.extend(section)
    if footer:
        if body:
            lines.append(layout.horizontal_line(layout.LIGHT))
        for place, section in enumerate(footer):
            if place:
                lines.append("")
            lines.extend(section)
    lines.append(layout.horizontal_line(layout.HEAVY))
    return Sheet("\n".join(lines))


# --- wires ---


def _named(wire):
    """Whether a wire prints by a name: a policy by its controls; an unnamed
    input of a solve by the names of its residual lines; a function, a
    choice, a measure, an alias or a field of the file by its name; a result
    an Evaluation reads by the name that Evaluation gives it; any other
    occurrence's result, and a function composed with the law of motion, by
    its expression, as the `out:` line of an entry of `Operations` prints
    them."""
    if wire.controls or wire.residuals:
        return True
    identity = wire.identity
    if not isinstance(identity, Identity):
        return False
    if identity.is_result:
        # a result an Evaluation reads carries the name that Evaluation gives
        # it, and its rules state that name at the point, `𝑉` with
        # `𝑉(m_d) = …`; any other result prints by its expression, an
        # Expectation's whose rule states its own reference at the point,
        # `(2)(k_d) = E_{Ψ, θ}[…]`, among them
        return any(
            S.stated_function(rule.statement) not in (None, identity) for rule in wire.rules
        )
    if identity.mark is not None:
        return False
    return identity.kind in ("function", "choice", "measure", "alias", "field")


def _residual_names(names, wire):
    """An unnamed input of a solve by the names of the residual lines it is
    made from, `(r₁, r₂)`: each line under `Wire.residuals` is
    the equation `rᵢ = …` whose left side names the residual."""
    return tuple_text(tuple(names.text(rule.statement.left) for rule in wire.residuals))


def _wire_name(names, wire):
    """The name a wire prints by, or, for a wire that carries none, its
    expression as held (the long form; `Operations` refers to it by the
    number of the entry that writes it instead)."""
    if wire.controls:
        return _control_name(wire.controls)
    if wire.residuals:
        return _residual_names(names, wire)
    if _named(wire):
        if wire.identity.kind == "measure" and wire.identity.mark == "with-distribution":
            # an extension's output by the name its record holds, its input's
            # name and its law, `μ⊗P_ν⊗P_{Ψ|ν}`
            return wire.name
        return _field_name(wire.identity, wire.name)
    if wire.expression is not None:
        return names.text(wire.expression)
    return wire.name


def _carrier_document(names, item, bound_names=(), *, together=False):
    """The carrier of a wire or a denoted object as a document: a set of
    policies as its type and its feasibility, `Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)`,
    every other set as held. Where it does not fit on one line, each part
    stands on a line of its own, or, with `together`, the type on the first
    line and the feasibility conditions together on the next where they fit,
    as the rule line of an entry of `Operations` prints a declared carrier."""
    carrier = getattr(getattr(item, "mathematical_type", None), "carrier", None)
    if carrier is None:
        return None
    variables, base, conditions = S.policy_set_parts(carrier)
    extra = tuple(zip(variables, bound_names)) if len(variables) == len(bound_names) else ()
    parts = []
    for condition in conditions:
        if parts:
            parts.extend((",", layout.line("  ")))
        parts.append(names.document(condition, extra))
    if not parts:
        return layout.group(names.document(base, extra))
    if together:
        parts = [layout.group(*parts)]
    return layout.group(names.document(base, extra), ",", layout.line("  "), *parts)


def _name_and_carrier(names, item, *, together=False):
    """`(name, carrier document)` of a wire or a denoted object: the entry of
    a `Signature`, `At` or `Where` section; the name of a wire that carries
    none is the document of its expression. `together` is
    `_carrier_document`'s."""
    if isinstance(item, Wire):
        bound = (
            tuple(function_name(c.field, c.perch) for c in item.controls) if item.controls else ()
        )
        carrier = _carrier_document(names, item, bound, together=together)
        if not _named(item) and item.expression is not None:
            return names.document(item.expression), carrier
        return _wire_name(names, item), carrier
    symbol = getattr(item, "symbol", "") or _field_name(getattr(item, "identity", None), "")
    # a policy's set of functions binds the policy itself, named as the card
    # names it, `𝑐(m_d) ∈ Γ(m_d)` (the `At` section of a decision builder); a
    # joint policy's components by the functions they are, `𝑐(m, z_d) ∈
    # Γ_c(m)`, as the head names them
    bound = _subject_names(getattr(item, "identity", None)) or _bound_function_names(item)
    document = _carrier_document(names, item, bound)
    expression = getattr(item, "expression", None)
    rule = _category_map(item) if isinstance(expression, CategoryCodes) else names.rule(expression)
    if rule is not None:
        document = (
            layout.group(document, ",", layout.line("  "), rule) if document is not None else rule
        )
    return symbol, document


# --- names ---


def _field_name(identity, fallback):
    """A function, a choice, an alias or a measure of the file by its name and
    perch mark: `𝑉≻`, `𝑚_d≻`, `𝑐`, `μ≺`; a field of the file in
    roman with its mark, `a≻`; anything else by `fallback`."""
    if not isinstance(identity, Identity):
        return fallback
    if identity.kind == "measure":
        # the perch's `μ≻`, or an extension's `μ⊗P_ν` as the record names it
        return S.printed_name(identity)
    if identity.kind in ("function", "choice", "alias") and identity.field:
        return function_name(identity.field, identity.perch)
    if identity.kind == "field" and identity.field:
        return identity.field + PERCH_MARK.get(identity.perch, "")
    return fallback


def _subject_names(identity):
    """The printed names of the functions an identity stands for: a joint
    policy's components by their subjects, `(𝑐, ℎ_choice)`, a function by its
    field, `𝑐`; nothing for anything else."""
    if not isinstance(identity, Identity):
        return ()
    subjects = identity.subjects or ((identity.field,) if identity.field else ())
    return tuple(function_name(subject, identity.perch) for subject in subjects)


def _bound_function_names(item):
    """The printed names of the functions a denoted set of policies binds,
    read from its carrier's bound variables, `(𝑐, ℎ_choice)`: each by its
    field and perch, as a function of the file is spelled."""
    carrier = getattr(getattr(item, "mathematical_type", None), "carrier", None)
    return tuple(function_name(field, perch) for field, perch in S.policy_fields(carrier))


def _control_name(controls):
    """A policy by the names of its controls, `𝑐` or `(𝑐, ℎ)`."""
    return tuple_text(
        tuple(function_name(identity.field, identity.perch) for identity in controls)
    )


def _records(record):
    """The record, the records held under its directions and the records of
    its pieces, depth first; a refused direction, held as a sentence, is no
    record."""
    yield record
    for _, held in getattr(record, "directions", ()):
        if not isinstance(held, str):
            yield from _records(held)
    for piece in getattr(record, "pieces", ()):
        yield from _records(piece.record)


class _Names:
    """The printed names of the identities a card's expressions refer to, and
    the definitions the card may list in its footer.

    A definition prints by the symbol its record holds (`𝑔≻`, `𝑢`, `Γ`); a
    function, a choice, an alias or a measure of the file by its field and
    perch mark, an alias that a `Rule` under `where` defines by the sort of
    the rule's right side; every other identity as `format_expression` names
    it."""

    def __init__(self, record):
        self.symbols = {}
        self.denoted = []
        # the numbers of the entries of `Operations`, by the wire each entry
        # writes, filled as the section is built: a reference to an unnamed
        # wire in a section built after it prints by its producer's number,
        # `(2)`, as the `in:` line does
        self.producers = {}
        for part in _records(record):
            for denoted in getattr(part, "definitions", ()):
                identity = denoted.identity
                if isinstance(identity, Identity) and identity not in self.symbols:
                    self.symbols[identity] = denoted.symbol
                    self.denoted.append(denoted)
            for item in getattr(part, "where", ()):
                # an abbreviation a `Rule` defines is spelled by the sort of
                # the rule's right side: a set in roman, `A≻,policy`, and a
                # function in italic
                if not isinstance(item, Rule):
                    continue
                for identity in S.free_identities(item.statement.left):
                    if (
                        isinstance(identity, Identity)
                        and identity.kind == "alias"
                        and identity.field
                        and identity not in self.symbols
                    ):
                        self.symbols[identity] = (
                            identity.field
                            if S.denotes_a_set(item.statement.right)
                            else function_name(identity.field)
                        )

    def pairs_for(self, expression, extra=()):
        """The printed name of each identity free in `expression`, after the
        pairs `extra`: an unnamed wire by its producer's row or key, a
        declared law as a measure, a measure extended by declared laws by its
        laws, a definition by its symbol, a function, a choice or a field by
        its field and perch mark, and an alias in italic."""
        pairs = list(extra)
        for identity in sorted(S.free_identities(expression), key=str):
            if not isinstance(identity, Identity):
                continue
            if identity.is_result and identity.kind in OPERATOR_KINDS:
                # an unnamed wire by its producer's row where the card numbers
                # it, and by the producer's key on a card that does not
                number = self.producers.get(identity)
                key = identity.key_within(identity.block) if identity.block else str(identity)
                pairs.append(
                    (
                        identity,
                        f"({number})" if number is not None else key.removesuffix(":result"),
                    )
                )
            elif identity.kind == "distribution":
                # a declared law in a formula is a measure, `P_ν`, or the
                # kernel its record names, `P_{Ψ|ν}`; the subject alone,
                # `ν`, names its declaration and not the law
                symbol = self.symbols.get(identity, "")
                pairs.append(
                    (identity, symbol if symbol.startswith("P_") else S.printed_name(identity))
                )
            elif identity.kind == "measure":
                # a measure extended by declared laws is named by its input
                # and its law; each law by the symbol its record names,
                # `P_{Ψ|ν}`, as a law in a formula is
                held = identity
                while isinstance(held, Identity) and held.kind == "measure":
                    if held.mark == "with-distribution" and held.subjects:
                        law = Identity("distribution", stage=held.stage, subjects=held.subjects)
                        symbol = self.symbols.get(law, "")
                        pairs.append(
                            (law, symbol if symbol.startswith("P_") else S.printed_name(law))
                        )
                    held = held.owner
            elif identity in self.symbols:
                pairs.append((identity, self.symbols[identity]))
            elif identity.kind in ("function", "choice", "field") and identity.perch is not None:
                pairs.append((identity, _field_name(identity, identity.stem)))
            elif identity.kind == "alias" and identity.field:
                pairs.append((identity, function_name(identity.field)))
        return tuple(pairs)

    def document(self, expression, extra=()):
        """`expression` as a document, under the names the card gives its
        identities."""
        return S.format_document(expression, names=self.pairs_for(expression, extra))

    def text(self, expression, extra=()):
        """`expression` as the text of one line, under the card's names."""
        return layout.flat(self.document(expression, extra))

    def rule(self, expression):
        """The document of a defining rule: `format_document` of a term, the
        wording of a `Textual` part as held, with no marker, its words
        filling the lines; None where there is none."""
        if expression is None:
            return None
        if isinstance(expression, Textual):
            return _filled(expression.text)
        return self.document(expression)

    def names_of(self, denoted):
        """The names a card may write a definition by: its symbol; for a
        declared law also its name as a measure in a formula, `P_ν`,
        `P_{Ψ, θ}`, its subjects bound as one, `(Ψ, θ)`, and each subject as
        a coordinate, `Ψ`, since a card that writes the shock writes the name
        its law declares."""
        names = [denoted.symbol] if denoted.symbol else []
        identity = denoted.identity
        if isinstance(identity, Identity) and identity.kind == "distribution":
            subjects = tuple(identity.subjects)
            joint = ("(" + ", ".join(subjects) + ")",) if len(subjects) > 1 else ()
            for name in (S.printed_name(identity), *joint, *subjects):
                if name and name not in names:
                    names.append(name)
        return names

    def written_in(self, text, own=()):
        """The definitions written in `text`, the lines of a card above its
        footer, which the `Definitions referenced` section lists: each under
        every name the card writes it by, a joint law by each of its subjects
        that stands, `Ψ` and `θ`, in the order the record holds them, the
        card's own object left out."""
        found, listed = [], set()
        for denoted in self.denoted:
            if denoted.identity in own:
                continue
            for name in self.names_of(denoted):
                if name not in listed and _stands_in(name, text):
                    listed.add(name)
                    found.append((name, denoted))
        return found


def _filled(text):
    """The words of `text` filling the lines: a break may follow any word,
    each decided on its own, the continuation two columns in."""
    words = text.split(" ")
    return layout.concat(
        layout.text(words[0]),
        *(layout.group(layout.nest(2, layout.line(), word)) for word in words[1:]),
    )


def _category_map(denoted):
    """A set's category map as `Denoted.rule` writes it, filling the lines: a
    break may follow the comma after a category, each decided on its own, so
    that a code stands on the line of its category, the continuation two
    columns in."""
    first, *rest = denoted.rule.split(", ")
    return layout.concat(
        layout.text(first),
        *(layout.concat(",", layout.group(layout.nest(2, layout.line(), part))) for part in rest),
    )


# the characters of a printed name: word characters other than the
# superscript digits, the perch marks and a prime; a superscript digit ends a
# name, since `format_expression` writes an integer exponent as superscript
# digits directly after its base, `σ_ξ²`, `c⁻²`
_NAME_CHARACTER = r"(?:[^\W⁰¹²³⁴⁵⁶⁷⁸⁹]|[≺≻′])"


def _stands_in(symbol, text):
    """Whether `symbol` is written in `text`: as a whole run of name
    characters where the symbol is one, `𝑑𝑢` in `Inv(𝑑𝑢)` and not in
    `𝑑𝑢𝑖𝑛𝑣`, nor `A≻` in the abbreviation `A≻,policy`, whose comma and
    block name continue the run, while `σ_ξ` stands in `σ_ξ²/2`, whose
    superscript digit is the exponent of a power; and as a substring
    otherwise, `(Ψ, θ)`."""
    if re.fullmatch(f"{_NAME_CHARACTER}+", symbol):
        return (
            re.search(
                f"(?<!{_NAME_CHARACTER}){re.escape(symbol)}(?!{_NAME_CHARACTER}|,[\\w′])", text
            )
            is not None
        )
    return symbol in text
