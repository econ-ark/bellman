"""The records a query answers with that print their own lines: the fields,
the diagnostics and the methods of a stage, and the listings, signatures,
obligations and tables of rows the stage and its pieces answer.

`fields()`, `diagnostics()` and `methods` answer read-only
mappings; each writes its own content, one entry to a line, the label in a
left column and the content in a right one. A listing and a table write their
columns, a signature the word and the typed wire of each entry. That is the
form the content takes outside a sheet; the stage sheet, written in
`stage/inventory.py`, sets the stage's fields and bindings inside one.
"""

from __future__ import annotations

from collections import namedtuple
from collections.abc import Mapping
from types import MappingProxyType

from bellman.display import sheets
from bellman.native.records import Refusal
from bellman.refusals import Diagnostic
from bellman.syntax import terms as T
from bellman.syntax.layout import LABEL_COLUMN
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import PERCH_SIGN, VALUE_ROLES
from bellman.typing import typed_expressions as S
from bellman.typing.typed_expressions import format_expression

# --- the read-only mappings that print their own lines ---


class _PrintedMapping(Mapping):
    """A read-only mapping that prints its own lines, which each record of this
    module that is a mapping writes (`_lines`). Its keys keep the order they
    were given in. Its representation is its lines, so that a reader who writes
    the bare expression sees the answer rather than a constructor call. A
    record with no entry prints the word `none`, as `Rows` and `Listing` do."""

    def __init__(self, entries):
        self._entries = dict(entries)

    def __getitem__(self, key):
        return self._entries[key]

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)

    # the read-only mapping the record holds, for the one caller that must see
    # the proxy itself: the check of `ElaboratedStage.__post_init__` that an
    # attribute was passed through `freeze`
    mapping = property(lambda self: MappingProxyType(self._entries))

    def _lines(self):
        raise NotImplementedError

    def __str__(self):
        return "\n".join(self._lines()) if self._entries else "none"

    __repr__ = __str__


class Fields(_PrintedMapping):
    """A read-only mapping from field identities to sorts, printed with each
    field's perch, role and declared set. A shock belongs to no perch:
    `edges` maps it to the pair of perches of the transition that draws it.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""

    def __init__(self, entries, edges=()):
        super().__init__(entries)
        self._edges = dict(edges)

    # the edge that draws each shock, as the pair of perch words of the block
    # that draws it; the stage sheet writes its own sentences from these pairs
    edges = property(lambda self: dict(self._edges))

    def _lines(self):
        entries = []
        for identity, sort in self._entries.items():
            said = [self._at(identity, sort), sort.role or "no role"]
            if sort.constant:
                said.append("constant")
            if sort.domain is not None:
                said.append(f"in {to_source(sort.domain)}")
            entries.append((identity, "  ".join(said)))
        return _two_columns(entries)

    def _at(self, identity, sort):
        """The second column of one line: the perch mark and the word of the
        perch for a field, and the edge for a shock."""
        edge = self._edges.get(identity)
        if edge is not None:
            return "→".join(PERCH_SIGN[perch] for perch in edge)
        if sort.perch in PERCH_SIGN:
            return f"{PERCH_SIGN[sort.perch]} {sort.perch}"
        return sort.perch or "no perch"


def _two_columns(entries):
    """Label and content in two columns with no wrapping, the form the records
    of this module print outside a sheet: each label in a column as wide as the
    widest and three spaces after it."""
    width = max(len(str(label)) for label, _ in entries) + 3
    return [f"{label!s:<{width}}{text}".rstrip() for label, text in entries]


class Diagnostics(_PrintedMapping):
    """The nine diagnostics of a stage's construction, `stage.diagnostics()`,
    displayed one per line: whether its inputs and outputs are complete, the
    missing builders, the exposed inputs, the unused outputs, the forward
    maps, the builder choices, the external calls, the value inputs a
    backward header lists and no line of its block reads, each as the block
    and the diagnostic's sentence, and whether it is ready for
    interpretation. A sequence displays its members, and an empty one `none`.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""

    def _lines(self):
        def item_text(item):
            if isinstance(item, Diagnostic):
                return f"{item.address}: {item.message}"
            return str(item)

        def text(value):
            if isinstance(value, (tuple, list)):
                return ", ".join(item_text(item) for item in value) if value else "none"
            return str(value)

        return _two_columns([(key, text(value)) for key, value in self._entries.items()])


class Methods(_PrintedMapping):
    """The read-only mapping from places to the components typed at them,
    empty where no signature carries a component. Each printed entry names
    the place and its components, the method word with its arguments, the
    grid and the handler; a piece answers only the places within it.

    See `docs/Bellman-Sym/API/stage/07-methods.md` §2."""

    def _lines(self):
        width = max(len(str(place)) for place in self._entries) + 3
        return [f"{place!s:<{width}}{held}" for place, held in self._entries.items()]


# --- the tables, the listings and the conditions ---


class Rows(tuple):
    """A tuple of read-only rows displayed as a table, with retained terms
    written as source. `heads` may supply a displayed heading different from
    the key: a parameter's `domain` key prints under `set`. `joined` names
    each key that has no column of its own, with the key whose column prints
    it and the sign written between the two cells: a derived parameter's
    `definition` prints under `set`, after the set and ` := `, and alone
    where the row holds no set.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §§1-2."""

    def __new__(cls, rows, heads=None, joined=None):
        made = super().__new__(cls, rows)
        made._heads = dict(heads or {})
        made._joined = dict(joined or {})
        return made

    def _printed(self, row, key):
        """The cell a row prints in the column of `key`: its own cell, then
        the cell of each key joined to that column, after the sign where
        both cells hold text."""
        text = _cell(row[key])
        for other, (column, sign) in self._joined.items():
            joined = _cell(row[other]) if column == key else ""
            if joined:
                text = f"{text}{sign}{joined}" if text else joined
        return text

    def __str__(self):
        if not self:
            return "none"
        keys = [key for key in self[0] if key not in self._joined]
        heads = [self._heads.get(key, key) for key in keys]
        cells = [[self._printed(row, key) for key in keys] for row in self]
        widths = [
            max([len(head)] + [len(row[index]) for row in cells])
            for index, head in enumerate(heads)
        ]
        lines = [heads] + cells
        return "\n".join(
            "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip()
            for row in lines
        )

    __repr__ = __str__


def _cell(value):
    """One cell of a printed table: a retained term as its source, None as an
    empty cell, anything else as it prints."""
    if value is None:
        return ""
    if hasattr(value, "__dataclass_fields__"):
        return to_source(value)
    return str(value)


ListingEntry = namedtuple("ListingEntry", "key name kind produced depth number")


class Listing(tuple):
    """The keys of the pieces inside a graph or a bubble, in order of
    application, printed as a tree with a kind column. Indexing
    returns the key; `entries` returns the records the display is printed
    from, one `(key, name, kind, produced, depth, number)` per row.

    `key` is what the handle that answered the listing accepts: the whole name
    at a graph, the part of the name after the holder's segment inside a
    bubble, and, for a piece inside a sub-builder, the tuple of keys that walks
    to it, one per level. `name` is the whole name of the box. `kind` is the
    kind column: `builder`, `block`, `sub-builder`, `primitive` or `line`.
    `produced` is what the piece produces, by name, or the empty string.
    `depth` is the depth in the tree. `number` is the position of a primitive
    in order of application among the primitives of its builder, the
    sub-builders opened, which is the number of its entry in the `Operations`
    section of the builder's card, or the position of a builder among the
    builders of its graph; a sub-builder, a block and a line carry none.

    The display prints the number right-aligned, the key indented two columns
    per level, the kind column and `→ produced` where there is one, each
    column sized to its longest entry plus two, as a card's columns are.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""

    def __new__(cls, entries):
        entries = tuple(ListingEntry(*entry) for entry in entries)
        made = super().__new__(cls, tuple(entry.key for entry in entries))
        made._entries = entries
        return made

    entries = property(lambda self: self._entries)

    # the whole name of each box, which the key reaches
    names = property(lambda self: tuple(entry.name for entry in self._entries))

    def __str__(self):
        if not self._entries:
            return "none"
        numbers = [str(entry.number) for entry in self._entries if entry.number is not None]
        width = max((len(number) for number in numbers), default=0)
        labels = ["  " * entry.depth + _key_text(entry.key) for entry in self._entries]
        at = max(len(label) for label in labels) + 2
        kinds = max(len(entry.kind) for entry in self._entries) + 2
        lines = []
        for entry, label in zip(self._entries, labels):
            number = "" if entry.number is None else str(entry.number)
            head = f"{number:>{width}}  " if width else ""
            arrow = f"→ {entry.produced}" if entry.produced else ""
            lines.append((head + f"{label:<{at}}" + f"{entry.kind:<{kinds}}" + arrow).rstrip())
        return "\n".join(lines)

    __repr__ = __str__


def _key_text(key):
    """The text a listing prints for a key: the key itself, or the last of a
    tuple of keys, whose earlier members are the rows it stands under."""
    return key[-1] if isinstance(key, tuple) else key


class NamedListing(_PrintedMapping):
    """A read-only mapping listing pieces by name, displayed one name to a
    line with what the listing holds for it: a block of the initial diagrams
    with its kind and direction, `block, backward`; a builder with the pair
    of perches it joins, or `policy`, and its direction word,
    `cntn → dcsn, bwd`, which `stage.builder.list()` answers; or a path of
    one perch with the pair it reads, `cntn → dcsn`, or `policy`, which
    `stage.dcsn.builder.list()` answers. The definitions table's listing,
    which prints as the definitions sheet, is `inventory.DefinitionsListing`,
    a record of this class that holds the stage.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §4."""

    def _lines(self):
        width = max(len(str(key)) for key in self._entries) + 3

        def text(value):
            if isinstance(value, tuple):
                return ", ".join(str(item) for item in value)
            return str(value)

        return [f"{key:<{width}}{text(value)}".rstrip() for key, value in self._entries.items()]


class SectionedListing(_PrintedMapping):
    """The stage's read-only mapping from each direction heading to that
    level's own listing, displayed one heading and listing after another.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §4."""

    def _lines(self):
        blocks = []
        for heading, listing in self._entries.items():
            body = "\n".join("  " + line for line in str(listing).splitlines())
            blocks.append(f"{heading}\n{body}")
        return blocks


class Obligations(tuple):
    """The ordered tuple of conditions, retaining identities, explanation,
    status and evidence. The display pairs the name of each condition with
    its term, or with its sentence where it holds no term, and shows the
    status when it is not `required`.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""

    def __str__(self):
        if not self:
            return "none"
        entries = []
        for item in self:
            status = "" if item.status == "required" else f"   [{item.status}]"
            # a condition prints as the term it holds; one that holds none
            # prints its sentence, since this listing is the complete record
            # of the stage's conditions
            text = (
                format_expression(item.predicate, width=None)
                if item.predicate is not None
                else item.explanation
            )
            entries.append((item.condition, text + status))
        return "\n".join(_two_columns(entries))

    __repr__ = __str__


# --- the signature ---


# The words of a signature's two sides, its inputs and its outputs, as the
# listing of a signature and every card print them.
SIDE_WORDS = {"in": "in", "out": "out"}


class Signature(tuple):
    """The immutable typed inputs and outputs of a piece, as two tuples of
    wires, with the components typed at the piece after them, `components`,
    the pairs of a place's address and its `Components`. Each wire unpacks as
    identity and type. The display writes value bundles as bundles, omits
    empty parts, and after the field component prints each method, grid and
    handler on a line of its own,
    with the object it is typed for where the place names one,
    `method   !Linear  [V[<]]`. A decision builder's signature is that of its
    operator at a policy; its free policy is typed at the policy builder's
    output. The same record is returned at each level. Equality and hashing
    compare the typed components as well as the wires; unpacking returns the
    two wire tuples alone.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""

    def __new__(cls, inputs=(), outputs=(), components=()):
        made = super().__new__(cls, (tuple(inputs), tuple(outputs)))
        object.__setattr__(made, "components", tuple(components))
        return made

    def __setattr__(self, name, value):
        raise AttributeError("a signature answer is immutable")

    def __delattr__(self, name):
        raise AttributeError("a signature answer is immutable")

    def __eq__(self, other):
        if isinstance(other, Signature):
            return tuple.__eq__(self, other) and self.components == other.components
        return False if isinstance(other, tuple) else NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal

    def __hash__(self):
        return hash((tuple(self), self.components))

    inputs = property(lambda self: self[0])
    outputs = property(lambda self: self[1])
    # each printed line as its word and its typed wire, so that a sheet setting
    # the signature in two columns takes the two parts rather than cutting the
    # line at its first space
    entries = property(
        lambda self: tuple(_wire_entries(self.inputs, self.outputs))
        + tuple(component_entries(self.components))
    )

    def __str__(self):
        return "\n".join(signature_lines(self.entries))

    __repr__ = __str__


def _wire_entries(inputs, outputs):
    """The `in` and `out` entries of a piece, one per bundle, each a word and a
    typed wire, with no column for the wire's identity."""
    sides = ((SIDE_WORDS["in"], inputs), (SIDE_WORDS["out"], outputs))
    return [
        (word, line)
        for word, wires in sides
        for group in wires_by_value_bundle(wires)
        for line in _bundle_lines(group)
    ]


def component_entries(components):
    """The printed entries of the components typed at a piece, after its
    wires: for each place, as `(address, Components)` pairs, its method, its
    grid and its handler where typed, each as the word of the component and
    its text, the object the place names after it in brackets where the
    place is one object of an Evaluation, `dcsn_to_arvl.evaluate[V[<]]`. A
    generated method is followed by the entry it is generated from,
    `!closed_form  generated from policy.method` (AMD-MT-003 build contract
    §5)."""
    entries = []
    for address, held in components:
        suffix = "  " + address[address.index("[") :] if "[" in address else ""
        if held.method is not None:
            text = to_source(T.Method(held.method)) + (
                f"  generated from {held.generated_from}"
                if held.generated_from is not None
                else ""
            )
            entries.append(("method", sheets.SetsLine(text + suffix)))
        if held.grid is not None:
            entries.append(("grid", sheets.SetsLine(to_source(T.Grid(held.grid)) + suffix)))
        if held.handler is not None:
            entries.append(("handler", sheets.SetsLine(f'"{held.handler}"' + suffix)))
    return entries


def _bundle_lines(group):
    """The typed lines of one bundle: one line where its wires are functions
    on one domain, the bundle typed as one function into the product of
    their codomains (`_bundle_carrier`), or where they carry one object under
    several names, as the controls of a joint choice are one policy, its set
    written once; one line per wire otherwise."""
    notes = ", ".join(dict.fromkeys(wire.note for wire in group if wire.note))
    carrier = _bundle_carrier(group)
    if carrier is not None:
        text = format_expression(carrier, width=None)
        return [
            sheets.SetsLine(f"{bundle_name(group)} : {text}" + (", " + notes if notes else ""))
        ]
    carriers = tuple(wire.mathematical_type.carrier for wire in group)
    if len(group) > 1 and all(
        S.alpha_equivalent(carrier, carriers[0]) for carrier in carriers[1:]
    ):
        return [
            sheets.SetsLine(
                f"{bundle_name(group)} : {group[0].type}" + (", " + notes if notes else "")
            )
        ]
    return [
        sheets.SetsLine(f"{wire.name} : {wire.type}" + (", " + wire.note if wire.note else ""))
        for wire in group
    ]


def _bundle_carrier(group):
    """The carrier of a bundle of two or more wires that are all functions,
    or all measurable maps, on one domain: one map of that domain into the
    product of their codomains, composed here from the carriers the wires
    hold; None for any other group."""
    carriers = tuple(wire.mathematical_type.carrier for wire in group)
    if (
        len(group) > 1
        and all(isinstance(carrier, (S.FunctionSet, S.MeasurableMapSet)) for carrier in carriers)
        and all(
            type(carrier) is type(carriers[0])
            and S.alpha_equivalent(carrier.domain, carriers[0].domain)
            for carrier in carriers[1:]
        )
    ):
        return type(carriers[0])(
            carriers[0].domain, T.Product(tuple(item.codomain for item in carriers))
        )
    return None


def wires_by_value_bundle(wires):
    """The wires of one side grouped into the value bundles they form, as
    `sorts_by_value_bundle` groups their sorts."""
    groups, place = [], 0
    for group in sorts_by_value_bundle(tuple(wire.sort for wire in wires)):
        groups.append(tuple(wires[place : place + len(group)]))
        place += len(group)
    return tuple(groups)


def sorts_by_value_bundle(sorts) -> list:
    """The sorts of one side's wires grouped into the bundles they form: two or
    more value functions next to each other at the same coordinates stand
    together, and so do the controls of one joint choice, which are one
    policy."""
    made = []
    for sort in sorts:
        role = getattr(sort, "role", None)
        previous = getattr(made[-1][-1], "role", None) if made else None
        together = (role in VALUE_ROLES and previous in VALUE_ROLES) or (
            role == "control" and previous == "control"
        )
        bundled = (
            made
            and getattr(sort, "kind", None) == "function"
            and together
            and getattr(made[-1][-1], "coordinates", None) == getattr(sort, "coordinates", None)
        )
        made[-1].append(sort) if bundled else made.append([sort])
    return made


def bundle_name(group):
    """The name of one bundle, a single wire's own name and a bundle's
    tuple."""
    return tuple_text(tuple(wire.name for wire in group))


def tuple_text(names):
    """One name bare, several in parentheses, none as `()`."""
    return names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"


def signature_lines(entries) -> tuple:
    """The printed lines of a signature, from its entries: the word in the
    label column of eleven characters, the stage sheet's, and the typed wire
    after it, on a composite as on an operator; a card sets its `Signature`
    section in its own columns. A wire wider than the line wraps under its own
    column, so that `str(signature())` is a contiguous block of the answer's
    lines."""
    return sheets.label_columns(
        entries, width=LABEL_COLUMN, separation=sheets.SEPARATION, indent=0
    )


# --- the kernels of a builder ---


class PieceKernel(
    namedtuple(
        "PieceKernel",
        "key relative_name name kind function arguments outputs parameters "
        "parameter_values reads writes kernel relation python integrated fallback",
        defaults=((), None),
    )
):
    """One primitive operator of a builder, as the record the builder's
    `kernels()` answers holds it: plain data that refers to no stage.

    `key` is the key that reaches the piece from its builder, the part of its
    name after the builder's or, for a piece inside a sub-builder,
    the tuple of keys that walks to it from the builder, one per
    level, as the builder's `list()` gives it and its `[]` accepts,
    and `name` the whole name of its box; `kind` is the kind of the
    operator, `Pullback`, `Aggregation` or `Evaluation` among them.
    `relative_name` is the part of its name after the builder's, which the
    identity of its box writes: `key` itself for a piece directly in the
    builder, and for a piece inside a sub-builder the key the builder's
    primitive grain accepts, `risk_ce:Pullback`; the printed form shows it.
    `function` is the function the piece's `compile_kernel()` answers:
    it takes the values of the kernel's arguments, whose printed names
    `arguments` gives in order, then the value of each parameter `parameters`
    names, `piece.function(x₁, …, xₙ, *piece.parameter_values)`, and returns
    one array for one name of `outputs` and a tuple of arrays for several.
    `parameter_values` holds the values the calibration of the version binds
    to those parameters, None on a symbolic version. `python` is the source
    text the function was made from; standard `pickle` saves it where it
    cannot save a function made in memory. `reads` and `writes` name the
    wires the piece reads and writes, as the stage names them, so that the
    composition of a builder's pieces can be read from the record.

    A piece with no explicit function holds None in `function` and `python`:
    a row that states a relation its output satisfies, the identification
    of the policy with its candidate among them, holds its printed relation
    in `relation`, which is None for every other piece; an Evaluation, an
    ordinary expectation and a choice hold neither. An extracted derivative
    expectation holds its integrand as `function` and its shocks as
    `integrated`. Its `writes` name the result after integration.
    `fallback` is an explicit kernel for the region where the local
    expectations are all inactive, or None where there is no such kernel.
    Every piece holds its printed kernel in `kernel`.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §5."""

    __slots__ = ()

    def __str__(self):
        return "\n".join(_piece_kernel_lines(self))

    __repr__ = __str__


class KernelGuard(
    namedtuple("KernelGuard", "subject predicate function arguments parameters parameter_values")
):
    """A predicate and callable selecting the points where a subject is needed.

    The subject is a native output or a derivative piece's explicit argument.
    The function takes the ordered arguments followed by the parameters and
    returns Boolean values. No field holds the stage.
    """

    __slots__ = ()


class BuilderKernels(
    namedtuple(
        "BuilderKernels",
        "builder inputs outputs pieces parameters parameter_values sets grids "
        "laws guards output_kernels grid_factors",
        defaults=(None, None, None, None, None),
    )
):
    """What a builder's `kernels()` answers: the record from which a
    numerical operator is constructed with no stage in hand.

    `builder` is the name of the builder's box, the block id the file gives
    it, or the dotted name of a sub-builder, `cntn_to_dcsn.risk_ce`. `inputs`
    and `outputs` name the wires of the builder's signature.
    `pieces` holds one `PieceKernel` for each primitive operator of the
    builder in order of application, numbered as the builder's `list()`
    numbers them, its sub-builders opened. `parameters` names the parameters
    the pieces read, in declaration order, and `parameter_values` holds the
    values the calibration of the version binds to them, in the same order,
    None on a symbolic version. `sets` pairs each argument of a piece's
    function with the set the stage declares for it, as the file writes it,
    and then each named set those sets name with its definition. `grids` is
    a read-only mapping from the address of each place within the builder
    that types a grid to its realized grid at the bound settings, a
    `RealizedGrid` of `stage/grids.py` with its coordinates and its finite
    points, or, where the construction cannot establish its points and every
    property it requires, the `Refusal` that says why; None on a version with
    no bound settings (AMD-MT-003 build contract §2). `laws` and `guards`
    give the distribution records and conditional guards by piece key.
    `output_kernels` maps each piece key to its explicit kernels by native
    output identity. An empty inner mapping has no per-output explicit kernel.
    `grid_factors` holds detached inputs for supported handler-owned grids
    by place. The handler places their points and checks the result.

    The record holds strings, tuples, numbers and functions made from source
    text in a namespace that holds NumPy alone, and no stage: cloudpickle
    saves it and loads it in another process, and standard `pickle` saves the
    source texts `python` of its pieces.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §5."""

    __slots__ = ()

    def __str__(self):
        head = f"kernels of {self.builder}: {', '.join(self.inputs)} → {', '.join(self.outputs)}"
        width = len(str(len(self.pieces)))
        lines = [head]
        for number, piece in enumerate(self.pieces, start=1):
            first, *rest = _piece_kernel_lines(piece)
            lines.append(f"{number:>{width}}  {first}")
            lines.extend(" " * (width + 2) + line for line in rest)
        lines.extend(
            _two_columns(
                [
                    ("parameters", _parameter_text(self.parameters, self.parameter_values)),
                    ("sets", _sets_text(self)),
                    *_grids_rows(self.grids),
                ]
            )
        )
        return "\n".join(lines)

    __repr__ = __str__


# the labels of the lines under one piece of a builder's kernels, set in one
# column as wide as the longest of them and two spaces
_PIECE_LABELS = ("function", "relation", "kernel", "wires")
_PIECE_LABEL_WIDTH = max(len(label) for label in _PIECE_LABELS) + 2


def _piece_kernel_lines(piece):
    """The lines of one piece of a builder's kernels: its name relative to
    the builder, `relative_name`, which for a piece inside a sub-builder is
    the key the builder's primitive grain accepts, `risk_ce:Pullback`; then
    under it the function with its arguments, its parameters after a
    semicolon and its outputs, or, for a piece with no function, its printed
    relation or its printed kernel; then the wires it reads and writes."""
    if piece.function is not None:
        called = ", ".join(piece.arguments) + (
            f"; {', '.join(piece.parameters)}" if piece.parameters else ""
        )
        said = ("function", f"{piece.function.__name__}({called}) → {', '.join(piece.outputs)}")
    elif piece.relation is not None:
        said = ("relation", "; ".join(piece.relation.splitlines()))
    else:
        said = ("kernel", "; ".join(piece.kernel.splitlines()))
    wires = ("wires", f"{', '.join(piece.reads)} → {', '.join(piece.writes)}")
    return [piece.relative_name] + [
        f"  {label:<{_PIECE_LABEL_WIDTH}}{text}".rstrip() for label, text in (said, wires)
    ]


def _parameter_text(names, values):
    """The parameters of a builder's kernels with the values bound to them,
    `ρ = 6.0`, or their names and the words that no value is bound."""
    if not names:
        return "none"
    if values is None:
        return f"{', '.join(names)}; no values bound"
    return ", ".join(f"{name} = {value}" for name, value in zip(names, values))


def _grids_rows(grids):
    """The rows of a builder's realized grids under the label `grids`, one
    per place, each the address and the realized grid or the reason its
    construction is refused; none where the version binds no settings or no
    place of the builder types a grid."""
    rows = []
    for address, grid in (grids or {}).items():
        shown = f"not constructed: {grid.reason}" if isinstance(grid, Refusal) else str(grid)
        rows.append(("grids" if not rows else "", f"{address}  {shown}"))
    return rows


def _sets_text(record):
    """The declared sets of a builder's kernels on one line: an argument of a
    piece's function with its set, `m_d ∈ Xm`, and a named set with its
    definition, `Xm := ℝ₊₊`."""
    arguments = {name for piece in record.pieces for name in piece.arguments}
    return (
        ", ".join(
            f"{name} {'∈' if name in arguments else ':='} {text}" for name, text in record.sets
        )
        or "none"
    )
