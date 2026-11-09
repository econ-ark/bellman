"""The records a stage and its construction hold.

A box of a graph of a constructed stage carries in its `data` a tuple of
references to authored content, each the identity of a record of the
definitions table or the address of an authored line, and `()` for a
builder, a sub-builder and a statement. A wire carries its whole type in one
`Sort`, the DisCoPy object of the wire's name. The sections of the module:

- the base `Record`, which gives a record equality, a hash and a
  repr read from its fields at every depth;
- the sort of a wire, `Sort`, with the table of typings that refuses a second
  sort of one identity;
- the entry of the definitions table, `Definition`;
- the stored graphs, `InitialDiagrams` and `Builders`, a `Refusal` in the
  place of a graph the construction could not build, and `Semgraph`, the
  record one graph is read into;
- the conditions, `Condition` and its entries, with
  `conditions_with_assumptions`, the conditions with a caller's assumptions
  in their place;
- the records of a version: `Bindings`, `Components`, `BoundBlock`,
  `MethodOption`, `Metadata` and `Provenance`;
- the records of the construction: a block (`BlockData`, `NodeData`,
  `BlockHeader`) and a line (`Line`, `OperatorOccurrence`, `ResolvedName`,
  `ExpressionType`);
- the validators and the equality of records.

Every record a stage holds is immutable, and its fields take part in its
equality, and so in the equality of the DisCoPy boxes and graphs that hold
it.
"""

from __future__ import annotations

import contextlib
import dataclasses
from collections.abc import Mapping
from contextvars import ContextVar
from types import MappingProxyType
from typing import Literal, NamedTuple

from discopy import cat, frobenius
from discopy.frobenius import Hypergraph

from bellman.native.frozen import freeze
from bellman.native.hypergraphs import (
    Immutable,
    comparison_answered_once,
    declare_frozen_class,
    freeze_native,
    is_frozen_record,
)
from bellman.native.identity import Identity
from bellman.native.predicates import Predicate
from bellman.refusals import CONDITIONS
from bellman.syntax import terms as T
from bellman.syntax.layout import WIDTH
from bellman.syntax.source import to_source

# --- the base of every record ---


class Record:
    """The base of the records that compare by their fields at every depth:
    equality by `values_equal`, the hash and the repr by
    `canonical_text`."""

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return values_equal(self, other)

    def __hash__(self):
        return hash(canonical_text(self))

    def __repr__(self):
        return canonical_text(self)


# --- the sort of a wire ---


# What a wire carries: a field, a function or a measure.
SORT_KINDS = ("field", "function", "measure")


class Sort(frobenius.Ob):
    """The type of one wire: `identity`, the wire's name, by which DisCoPy
    wires it; `kind`, what the wire carries, a field of the initial diagrams,
    a function of the backward builders graph or a measure of the forward
    builders graph; `perch`, the information set the object belongs to
    (`arvl`, `dcsn`, `cntn`; `shck` for a shock, which belongs to none; None
    for an object made on an edge); `role`, the field's role word (`state`,
    `control`, `value`, `marginal value`, `shock`) or the role of the value a
    function carries; `domain`, the immutable retained term of the set the
    wire's values lie in, the meet of the sets a field is declared with at
    its sites (a named-set reference, an inline interval or an intersection
    as written), None when no site declares one; and `coordinates`, the
    ordered identities of the coordinates a function is written in or a
    measure is on, `()` for a field wire; and `derivatives`, the ordered
    identities of the coordinates in which the block's derivative lines state
    a derivative of the value a function wire carries (AMD-MB-001 §5.1), `()`
    where none is stated. A
    function's input domain is given by the sorts of its coordinates, not by
    `domain`.

    A sort is a `discopy.frobenius.Ob`, so `Ty(sort)` is the type DisCoPy
    wires by; DisCoPy names an object by a string, so the sort's name is
    `str(identity)` and the record itself is `identity`. Two sorts are equal
    when their identities and their winding numbers are equal. A sort does not
    equal the plain library object of its name, since that equality would not
    be transitive. The typing is validated once, where a second sort of one
    identity is built with a different kind, perch, role, domain or
    coordinates."""

    def __init__(
        self, identity, kind, *, perch=None, role=None, domain=None, coordinates=(), derivatives=()
    ):
        if not isinstance(identity, Identity):
            raise TypeError(
                f"Sort.identity must be an Identity of bellman.native.identity; got {identity!r}"
            )
        if kind not in SORT_KINDS:
            raise ValueError(f"Sort.kind is one of {', '.join(SORT_KINDS)}; got {kind!r}")
        for name, value in (("perch", perch), ("role", role)):
            if value is not None and (not isinstance(value, str) or not value):
                raise TypeError(f"Sort.{name} must be a non-empty string or None; got {value!r}")
        if domain is not None and not is_frozen_record(domain):
            raise TypeError(
                f"Sort.domain must be a retained set term or None; got {type(domain).__name__}"
            )
        if not isinstance(coordinates, tuple) or not all(
            isinstance(a, Identity) for a in coordinates
        ):
            raise TypeError(f"Sort.coordinates must be a tuple of identities; got {coordinates!r}")
        if not isinstance(derivatives, tuple) or not all(
            isinstance(a, Identity) for a in derivatives
        ):
            raise TypeError(f"Sort.derivatives must be a tuple of identities; got {derivatives!r}")
        super().__init__(str(identity))
        self.identity = identity
        self.kind, self.perch, self.role, self.domain, self.coordinates = (
            kind,
            perch,
            role,
            domain,
            coordinates,
        )
        self.derivatives = derivatives
        _validate_typing(self)

    def _typing(self):
        """The kind, perch, role, domain, coordinates and derivatives of the sort."""
        return _Typing(
            kind=self.kind,
            perch=self.perch,
            role=self.role,
            domain=self.domain,
            coordinates=self.coordinates,
            derivatives=self.derivatives,
        )

    def __eq__(self, other):
        if not isinstance(other, Sort):
            return False
        return (self.identity, self.z) == (other.identity, other.z)

    def __hash__(self):
        # the identity and the winding number the equality decides by
        return hash((self.identity, self.z))

    def __repr__(self):
        declared = None if self.domain is None else to_source(self.domain)
        return (
            f"Sort({self.name!r}, {self.kind!r}, perch={self.perch!r}, role={self.role!r}, "
            f"domain={declared!r}, coordinates={self.coordinates!r}, "
            f"derivatives={self.derivatives!r})"
        )

    @classmethod
    def from_tree(cls, tree):
        raise NotImplementedError(
            "a Sort is encoded and decoded with the native encoder of "
            "bellman.native.hypergraphs, not with DisCoPy's from_tree"
        )


# The immutable subclass of `Sort`, declared here beside the class it freezes:
# `hypergraphs.py` stands beneath this module and cannot import it, and a
# subclass made on first use is absent from its module until the call that
# makes it, so a graph pickled in one process could not be loaded in a
# fresh one.
@declare_frozen_class
class _FrozenSort(Immutable, Sort):
    _native_class = Sort


# The typing of each identity of one construction: a table from identity to
# the kind, perch, role, domain and coordinates the first sort of that identity
# carried. `typing.context.type_stage` opens it while it types one stage, and
# it holds only for that call, since two stages of one name are two
# constructions.
# It is a `ContextVar` and no module global, as `hypergraphs._COMPARISONS` is,
# so that two constructions at once — two threads, two tasks — each read and
# write their own table.
_TYPINGS = ContextVar("bellman_typings_of_one_construction", default=None)


@contextlib.contextmanager
def construction_typing_table():
    """The table of typings of one construction, open while a stage is
    built."""
    table = {}
    token = _TYPINGS.set(table)
    try:
        yield table
    finally:
        _TYPINGS.reset(token)


class _Typing(NamedTuple):
    """The typing of a sort, which every sort of one identity carries alike."""

    kind: str
    perch: str | None
    role: str | None
    domain: object
    coordinates: tuple
    derivatives: tuple


def _validate_typing(sort):
    """Refuse a second sort of one identity that carries another typing, where
    it is built."""
    table = _TYPINGS.get()
    if table is None:
        return
    typing = sort._typing()
    held = table.setdefault(sort.identity, typing)
    if held != typing:
        differing = ", ".join(
            name for name, first, second in zip(_Typing._fields, held, typing) if first != second
        )
        raise ValueError(
            f"the identity {sort.identity!r} is given a second sort whose {differing} differs "
            f"from the first: an identity carries one typing, "
            f"validated where the second sort is built (AMD-SG-016 §3)"
        )


def with_identity(box, identity):
    """The box, carrying the identity it is named by. DisCoPy names a box by a
    string, so the name is `str(identity)`; the readers of a box's kind, its
    block and its field read the record, which every box of the package
    therefore carries."""
    box.identity = identity
    return box


# --- the definitions table ---


# The kinds of a record of the definitions table.
DEFINITION_KINDS_TABLE = (
    "set",
    "distribution",
    "parameter",
    "setting",
    "function",
    "function_alias",
    "correspondence",
    "g",
    "G",
    "line",
    "multiplier",
    "typing",
)


# The kinds whose record is made from a top-level item of the file, and whose
# `address` is therefore the file position `<path>:<line>` of that item. A
# `line` is addressed by its block and its id or ordinal and
# a `g` or a `G` by its block, each of which a reader of the stage follows.
DEFINITION_KINDS_AT_TOP_LEVEL = (
    "set",
    "distribution",
    "parameter",
    "setting",
    "function",
    "function_alias",
    "correspondence",
)


# The terminology's word for each kind of record, which a record's short form
# prints. The definitions sheet of `stage/inventory.py` holds the plurals its
# sections are headed by, `laws of motion` and `value aggregators`; the
# singulars are here because a record prints its own short form and this
# module holds the kinds.
DEFINITION_KIND_WORDS = {
    "set": "set",
    "distribution": "distribution",
    "parameter": "parameter",
    "setting": "setting",
    "function": "function",
    "function_alias": "function alias",
    "correspondence": "correspondence",
    "g": "law of motion",
    "G": "value aggregator",
    "line": "line",
    "multiplier": "multiplier",
    "typing": "typing entry",
}


@dataclasses.dataclass(frozen=True, slots=True)
class CategoryCodes:
    """The category map of a set marked `!categories`, the `categories` of
    its `Definition`, read once from the set's annotation by
    `typing.category_codes.category_codes`.

    `identifier` is the identifier written after the marker,
    `!categories household_status`, which asserts that every set marked with
    it has the same categories; None where the marker stands alone. `codes`
    holds the (code, category name) pairs in increasing code order,
    `((0, "newborn"), (1, "old"))`, and the codes are the members of the set.
    A code stands for the category (κ, name), κ the identifier or, without
    one, the stage text's digest with the set's name
    (`typing.category_codes.coded_meaning`). A category name is a string, not
    a term, so that no reader of terms takes it for a name of the stage."""

    identifier: str | None
    codes: tuple

    def __post_init__(self):
        if self.identifier is not None and (
            not isinstance(self.identifier, str) or not self.identifier
        ):
            raise ValueError(
                f"CategoryCodes.identifier is None or a nonempty string; got {self.identifier!r}"
            )
        require_tuple(self, "codes")
        if not self.codes:
            raise ValueError("CategoryCodes.codes holds at least one (code, name) pair")
        for pair in self.codes:
            if not (
                isinstance(pair, tuple)
                and len(pair) == 2
                and type(pair[0]) is int
                and isinstance(pair[1], str)
                and pair[1]
            ):
                raise TypeError(
                    "each entry of CategoryCodes.codes is a pair of an integer code and a "
                    f"nonempty category name; got {pair!r}"
                )
        codes = [code for code, _ in self.codes]
        if any(first >= second for first, second in zip(codes, codes[1:])):
            raise ValueError(
                f"the codes of CategoryCodes.codes increase strictly; got {tuple(codes)!r}"
            )
        names = sorted(name for _, name in self.codes)
        if any(first == second for first, second in zip(names, names[1:])):
            raise ValueError(
                f"the category names of CategoryCodes.codes are distinct; got {tuple(names)!r}"
            )


@dataclasses.dataclass(frozen=True, slots=True)
class Definition:
    """One entry of the definitions table: a name the stage file declares,
    once, in file order.

    `identity` names it (`cons:set:Xm`, `cons:parameter:ρ`,
    `cons:function:𝑢`, `ez_savings:correspondence:Γ`, `cons:g:dcsn_to_cntn`,
    or a line's address); its middle segment is the identity kind. `kind` is
    the definition kind, one of `set`, `distribution`, `parameter`,
    `function`, `function_alias`, `correspondence`, `g`, `G`, `line` and
    `multiplier` and `typing`, so a function alias has identity kind
    `function` and definition kind `function_alias`. A multiplier declared in
    a block body has the identity `<stage>:multiplier:<name>`, its one
    coordinate the multiplier with its declared set, its one equation the
    declaration with its clause as written, and the address of its line. A
    typing entry, `policy.method : !egm`, has the identity
    `<stage>:typing:<place>:<component>`, its one equation the method word,
    the grid or the handler's program, its one tag the subject as written,
    and the file position of the entry as its address (specification 0.7
    §4).

    `coordinates` holds the named coordinates of the definition as (name,
    retained set term or None) pairs, the fields and shocks a distribution's
    family expression reads with their declared sets, and `()` for a
    parameter, a set or a line. `equations` holds the retained terms: a set
    as one term, a parameter's declared set as its one term, and for a `g`
    or a `G` the ordered identities of the `line` records of the block's
    lines, so that a partial aggregator is printed from a slice and never
    stored. `tags` holds the entries of a line's annotation. `address` is the
    source address of the authored item, the block for a `g` or a `G`.
    `ordinal`, on a `line`, is the position of the line among the items of
    its block's body, counted from 1 as the construction counts it
    (`typing/declarations.py`, `read_block`; the lines of a branching block's
    branches are counted in turn, one count for the block), which outside a
    branch is the `n` of an unnamed line's address `<block>.<n>`; the version
    reads the number back from the record (`fold/stage_names.py`,
    `lines_of`), so that a line is numbered once. Every other kind holds None
    there. `categories`, on a set marked `!categories`, is its
    `CategoryCodes`, and None on every other record; the tags keep the
    annotation as written. The record's inputs, outputs and conditions are
    determined by its equations, and queries answer them."""

    identity: Identity
    kind: str
    _: dataclasses.KW_ONLY
    coordinates: tuple
    equations: tuple
    tags: tuple = ()
    address: str = ""
    ordinal: int | None = None
    categories: CategoryCodes | None = None

    def __post_init__(self):
        if self.kind not in DEFINITION_KINDS_TABLE:
            raise ValueError(
                f"Definition.kind is one of {', '.join(DEFINITION_KINDS_TABLE)}; got {self.kind!r}"
            )
        require_tuple(self, "coordinates", "equations", "tags")
        if self.categories is not None and (
            self.kind != "set" or not isinstance(self.categories, CategoryCodes)
        ):
            raise ValueError(
                "Definition.categories is a CategoryCodes on a set and None on every other "
                f"record; got {self.categories!r} on a {self.kind}"
            )
        if self.kind == "line":
            if (
                not isinstance(self.ordinal, int)
                or isinstance(self.ordinal, bool)
                or self.ordinal < 1
            ):
                raise ValueError(
                    "a line's Definition.ordinal is its position in the block's "
                    f"body, from 1; got {self.ordinal!r}"
                )
        elif self.ordinal is not None:
            raise ValueError(f"Definition.ordinal is None for a {self.kind}; got {self.ordinal!r}")

    def __repr__(self):
        """The short form: the identity by which the table reaches the record
        and the kind in the terminology's word, `Definition('cons:parameter:ρ',
        parameter)`. The record's content stands on its card
        and on its fields, and no reader takes this text apart."""
        return f"Definition({str(self.identity)!r}, {DEFINITION_KIND_WORDS[self.kind]})"


# --- the stored graphs ---


class _Graphs(Record):
    """What the two stored graph records of a stage share: each member is a
    `Hypergraph` or a `Refusal`, read by its name. The record keeps no
    reference to its stage: a field referring back to it would be a cycle,
    which `hypergraphs.copy_native` refuses. Reading the attribute of the
    version gives a navigation object of `pieces.py`, which is built from
    this record and the version.
    """

    # the members holding graphs, in the order they are listed
    MEMBERS: tuple = ()

    def __post_init__(self):
        for name in self.MEMBERS:
            value = getattr(self, name)
            if not isinstance(value, (Hypergraph, Refusal)):
                raise TypeError(
                    f"{type(self).__name__}.{name} must be a discopy.frobenius.Hypergraph "
                    f"or a Refusal; got {type(value).__name__}"
                )


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class InitialDiagrams(_Graphs):
    """The field-level graphs of a stage: the backward blocks on the fields
    they read and write, and the forward blocks likewise. They
    are two separate graphs and nothing else; each is drawn and printed on its
    own, and no drawing or listing puts the two directions in one picture. A
    box of either is a `hypergraphs.Block`.

    `refused_blocks` is empty except where the cut into the two directions was
    refused, as it is for the stage file of the tests' corpus
    `gourinchas-parker-2002/retire.bl`, whose blocks then stand in neither
    graph. It holds those blocks in file order, so that
    `block_lines.blocks_of`, and through it `fields`, `symbols` and the
    stage's sheet, still answer for such a stage.
    It is read by `block_lines.blocks_of` alone: it is no graph, and is never
    drawn or printed."""

    backward: Hypergraph = dataclasses.field(repr=False, hash=False)
    forward: Hypergraph = dataclasses.field(repr=False, hash=False)
    refused_blocks: tuple = dataclasses.field(default=(), repr=False, hash=False)

    MEMBERS = ("backward", "forward")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Builders(_Graphs):
    """The operator-level graphs of a stage: the backward builders on
    function wires and the forward builders on measure wires. A
    box of one of them is a `hypergraphs.Builder`, the operator the block of
    the same name denotes."""

    backward: Hypergraph = dataclasses.field(repr=False, hash=False)
    forward: Hypergraph = dataclasses.field(repr=False, hash=False)

    MEMBERS = ("backward", "forward")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Refusal(Record):
    """The refusal of a graph the construction could not build, held in that
    graph's place in the `InitialDiagrams` or the `Builders` record, so that
    the refusal is made at elaboration and raised when the graph is read.
    `reason` is the
    one sentence that says what happened and why, naming the rule;
    `diagnostic` the facts that place it, the stage, the authored address,
    the rule and the position (file, line, column, end_line, end_column, None
    for a term decoded without positions), from which
    `grains.graph_of` raises the `NotConstructed` the construction
    raised."""

    reason: str
    diagnostic: Mapping

    def __post_init__(self):
        if not isinstance(self.reason, str) or not self.reason:
            raise TypeError(f"Refusal.reason must be a non-empty sentence; got {self.reason!r}")
        if not isinstance(self.diagnostic, Mapping):
            raise TypeError("Refusal.diagnostic must be a mapping of the refusal's facts")
        missing = {"stage", "address", "rule"} - set(self.diagnostic)
        if missing:
            raise ValueError(f"Refusal.diagnostic lacks {sorted(missing)}")
        object.__setattr__(self, "diagnostic", freeze(dict(self.diagnostic)))


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Semgraph(Record):
    """The record of one graph that `semgraph.record` returns: the graph, the
    sorts of its input and output wires as `inputs` and `outputs`, its
    conditions, the sorts of the parameters its equations name as
    `parameters`, and the calibration of the version. The origins of its
    boxes are their data (`boxes.origins`), and the methods attached
    inside it are read from the stage's bindings by the piece's own `methods`
    (`boxes.methods_within`)."""

    graph: Hypergraph = dataclasses.field(repr=False, hash=False)
    _: dataclasses.KW_ONLY
    inputs: tuple[Sort, ...]
    outputs: tuple[Sort, ...]
    obligations: tuple[Condition, ...]
    parameters: tuple[Sort, ...] = ()
    calibration: Mapping | None = None

    def __post_init__(self):
        _require_functional_boundary(self, "graph")
        _require_entries(self, "obligations", Condition)
        _require_entries(self, "parameters", Sort)
        _require_distinct_identities(self, "parameters")
        if any(port.role != "parameter" for port in self.parameters):
            raise ValueError("Semgraph.parameters requires declared parameter records")
        if self.calibration is not None and not isinstance(self.calibration, Mapping):
            raise TypeError("Semgraph.calibration must be a mapping or None")
        object.__setattr__(self, "calibration", freeze(self.calibration))
        object.__setattr__(self, "graph", freeze_native(self.graph))


def _require_functional_boundary(record, graph_name):
    """Refuses a record whose `inputs` and `outputs` are not the sorts of
    the input and output wires of its graph, in order."""
    for name in ("inputs", "outputs"):
        _require_entries(record, name, Sort)
        _require_distinct_identities(record, name)
    _require_graph(record, graph_name)
    graph = getattr(record, graph_name)
    # the identities of the graph's input and output wires, not a type built
    # from identity strings: a sort does not equal the plain library object
    # of its name
    if (
        tuple(_identity_of(ob) for ob in graph.dom.inside),
        tuple(_identity_of(ob) for ob in graph.cod.inside),
    ) != (tuple(p.identity for p in record.inputs), tuple(p.identity for p in record.outputs)):
        raise ValueError(
            f"{type(record).__name__}.{graph_name} must match ordered inputs and outputs"
        )


def _identity_of(ob):
    """The identity of one input or output object of a graph: the record a
    sort carries, and the name of a plain object, which carries none."""
    return ob.identity if isinstance(ob, Sort) else ob.name


# --- the conditions ---


# The status of a condition: required of the stage, assumed by a caller, or
# established by a rule or evidence.
ObligationStatus = Literal["required", "assumed", "established"]


OBLIGATION_STATUSES = ("required", "assumed", "established")


# The heads of the arithmetic operations whose definedness a condition records,
# kind (iii) of the entries of `OBLIGATION_ENTRY_KINDS`.
ARITHMETIC_HEADS = ("Add", "Sub", "Mul", "Neg", "Div", "Pow")


@dataclasses.dataclass(frozen=True)
class ArithmeticHead:
    """The head of the arithmetic operation a `finite-real-arithmetic`
    condition is about, kind (iii) of the entries of a condition. The record
    holds the head
    alone and not the operation, so that two sums of one owner are one entry
    and are recorded once."""

    head: str

    def __post_init__(self):
        if self.head not in ARITHMETIC_HEADS:
            raise ValueError(
                f"ArithmeticHead.head is one of {', '.join(ARITHMETIC_HEADS)}; got {self.head!r}"
            )


@dataclasses.dataclass(frozen=True)
class UndeclaredSet:
    """The entry of a condition that stands where a set would, for a value
    the file declares no set for, kind (v) of the entries of a condition. It
    carries nothing: one record serves every such entry, and
    `typing/typed_expressions.py` writes the words a card prints for it."""


# the one record of kind (v); a writer names this rather than building its own
UNDECLARED_SET = UndeclaredSet()


# The five kinds an entry of a condition may be, told apart by their type and
# never by their text: (i) an identity, (ii) a retained term —
# a set, an expression or a statement, (iii) the head of an arithmetic
# operation, (iv) a predicate, and (v) the absence of a declared set. A plain
# string is none of them and is refused, so that an argument's index or a term
# position cannot stand where an identity is required.
OBLIGATION_ENTRY_KINDS = (
    Identity,
    T.setexpr,
    T.expr,
    T.stmt,
    ArithmeticHead,
    Predicate,
    UndeclaredSet,
)


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Condition(Record):
    """One condition of a stage and its status. `condition` names the
    condition, one of `refusals.CONDITIONS`; `entries` holds its entries,
    each of one of the kinds of `OBLIGATION_ENTRY_KINDS`; `status` is
    `required`, `assumed` or `established`; `evidence` names the rule or the
    evidence of an established condition; `explanation` is the sentence that
    states it."""

    condition: str
    entries: tuple
    _: dataclasses.KW_ONLY
    status: ObligationStatus
    evidence: tuple[str, ...] = ()
    explanation: str = ""

    @property
    def named_identities(self):
        """The retained identities to which the condition refers."""
        return tuple(item for item in self.entries if isinstance(item, Identity))

    @property
    def predicate(self):
        """The retained proposition, or None when only its wording is held."""
        return next(
            (
                item
                for item in reversed(self.entries)
                if isinstance(item, (Predicate, T.Rel, T.Equation))
            ),
            None,
        )

    @property
    def purpose(self):
        """Why the condition is retained, independently of its status."""
        return (
            "domain restriction"
            if self.condition == "feasibility"
            else "required by the exact operation"
        )

    @property
    def family(self):
        """The family of the condition, by which a printed form selects the
        conditions it shows."""
        return {"expectation-integrability": "integrability"}.get(self.condition, self.condition)

    def __post_init__(self):
        if not isinstance(self.condition, str) or not self.condition:
            raise TypeError(
                f"Condition.condition must be a non-empty string; got {self.condition!r}"
            )
        if self.condition not in CONDITIONS:
            raise ValueError(
                f"{self.condition!r} is no condition of the package; the "
                f"conditions are {', '.join(CONDITIONS)} (refusals.CONDITIONS)"
            )
        _require_obligation_entries(self, "entries")
        _require_strings(self, "evidence")
        if not isinstance(self.explanation, str):
            raise TypeError(f"Condition.explanation must be a string; got {self.explanation!r}")
        if self.status not in OBLIGATION_STATUSES:
            raise ValueError(
                f"Condition.status must be one of "
                f"{', '.join(OBLIGATION_STATUSES)}; got {self.status!r}"
            )
        if self.status == "established" and not self.evidence:
            raise ValueError(
                f"Condition.evidence must name the rule or evidence for an established condition"
            )


def _require_obligation_entries(record, name) -> None:
    """Refuses an entry of a condition that is of none of the kinds of
    `OBLIGATION_ENTRY_KINDS`."""
    require_tuple(record, name)
    for index, value in enumerate(getattr(record, name)):
        if not isinstance(value, OBLIGATION_ENTRY_KINDS):
            raise TypeError(
                f"{type(record).__name__}.{name}[{index}] must be an identity, a retained "
                f"term, the head of an arithmetic operation, a predicate or the record of "
                f"an undeclared set (AMD-SG-017 §4); got {value!r}"
            )


# The conditions a caller's assumption cannot discharge.
_STRUCTURAL = ("partial-field-stage", "unresolved-policy-evaluation")


def conditions_with_assumptions(obligations, assumptions):
    """The conditions of a stage with the caller's assumptions in place of the
    conditions they discharge: an assumption must match a condition of the
    stage, and a structural condition cannot be assumed away."""
    assumed = checked_assumptions(assumptions)
    required = {(item.condition, item.entries) for item in obligations}
    unmatched = set(assumed) - required
    if unmatched:
        raise ValueError(f"assumptions do not match retained requirements: {sorted(unmatched)!r}")
    for condition, _ in assumed:
        if condition in _STRUCTURAL:
            raise ValueError(f"assumptions cannot discharge structural requirement {condition}")
    return tuple(assumed.get((item.condition, item.entries), item) for item in obligations)


def checked_assumptions(assumptions):
    """The caller's assumptions by their condition and entries; each is a
    `Condition` of status `assumed`, given once, or is refused."""
    if not isinstance(assumptions, tuple) or any(
        not isinstance(item, Condition) for item in assumptions
    ):
        raise TypeError("assumptions must be a tuple of Condition records")
    if any(item.status != "assumed" for item in assumptions):
        raise ValueError("caller assumptions must have assumed status")
    assumed = {(item.condition, item.entries): item for item in assumptions}
    if len(assumed) != len(assumptions):
        raise ValueError("assumptions contain duplicate condition/identity entries")
    return assumed


# --- the records of a version: its bindings, metadata and provenance ---


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Bindings(Record):
    """This version's `calibration` and `settings` mappings, each None until
    bound and read-only afterwards, and `blocks`, the rows a solution
    method's lines add at the operative level, by the builder each opens.
    Calibration maps parameters
    to values and configuration maps settings to values; the methods of a
    version are no binding but the components of its signatures, read from
    the typing records of the definitions table. Each binding verb writes a new record into the
    stage it is called on.

    See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §1."""

    calibration: Mapping | None
    settings: Mapping | None
    blocks: Mapping | None = None

    def __post_init__(self):
        # the records hold the rows of the construction, which `freeze` does
        # not read, so the caller passes a read-only mapping
        if self.blocks is not None and (
            not isinstance(self.blocks, MappingProxyType)
            or not all(
                isinstance(key, str) and isinstance(item, BoundBlock)
                for key, item in self.blocks.items()
            )
        ):
            raise TypeError(
                "Bindings.blocks must be a read-only mapping from builder names to "
                "BoundBlock records"
            )
        for name in ("calibration", "settings"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, Mapping):
                raise TypeError(
                    f"Bindings.{name} must be a mapping or None; got {type(value).__name__}"
                )
            object.__setattr__(self, name, freeze(dict(value)))

    def __str__(self):
        """The two status lines, from the entries `entries` writes."""
        entries = [
            (label, (content,) if isinstance(content, str) else tuple(content))
            for label, content in self.entries()
        ]
        width = max(len(label) for label, _ in entries) + 3
        lines = []
        for label, content in entries:
            for index, text in enumerate(content):
                lines.append(
                    ((f"{label:<{width}}" if index == 0 else " " * width) + text).rstrip()
                )
        return "\n".join(lines)

    __repr__ = __str__

    def entries(self, readers=None, at=None):
        """The bindings as (label, content) entries: the calibration and the
        settings of one version, an absent one naming the verb that supplies
        it and a bound one listing what it binds in full, one entry per line.
        The stage sheet sets them in its two columns, with the methods line it
        writes from the components between them.

        `readers` maps each setting name to the pairs of the place and the
        components that read it (`stage_answers.settings_readers`), so that a
        setting a method reads stands once per reader; without it a setting
        stands with its value alone. `at` is the column the section's content
        begins at: with it, a settings entry too wide for one line is broken
        under its own third column, at the one width of every printed form,
        `layout.WIDTH`.

        See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §1."""
        return [
            ("calibration", _calibration_lines(self.calibration)),
            ("settings", _setting_lines(self.settings, readers or {}, at)),
        ]


def _calibration_lines(calibration):
    """The content of the calibration entry: each parameter with its value,
    or the verb that binds a calibration."""
    if calibration is None:
        return "none   calibrate(stage, source)"
    return [f"{name} = {value!r}" for name, value in calibration.items()] or ["none bound"]


def method_lines(components):
    """The content of the methods entry of a stage sheet: each place with
    the components typed at it on one line, which the sheet breaks at its
    spaces where it is too wide, or the verb that binds the methods where no
    place carries a component."""
    if not components:
        return "none   methodize(stage, source)"
    column = max([3] + [len(str(place)) for place in components]) + 3
    return [f"{place!s:<{column}}{held}" for place, held in components.items()]


def _setting_lines(settings, readers, at):
    """The content of the settings entry: each setting with its value, once
    for each place whose components name it, with that place and the method
    word there; or the verb that binds the settings. With `at`, the column
    the content begins at, a line too wide for `layout.WIDTH` is broken under
    its third column."""
    if settings is None:
        return "none   configure(stage, source)"
    named = [
        (name, value, place, held)
        for name, value in settings.items()
        for place, held in (readers.get(name) or (("", None),))
    ]
    column = max([3] + [len(name) for name, _, _, _ in named]) + 3
    wide = max([3] + [len(repr(value)) for _, value, _, _ in named]) + 3
    made = []
    for name, value, place, held in named:
        head = f"{name:<{column}}{repr(value):<{wide}}"
        by = held.word if held is not None else ""
        tail = f"{place}   {by}".rstrip()
        if not tail:
            made.append(head.rstrip())
            continue
        room = None if at is None else WIDTH - at - len(head)
        if room is None or len(tail) <= room:
            made.append(head + tail)
            continue
        broken = _broken_at_spaces(tail, room)
        made.append(head + broken[0])
        made.extend(" " * len(head) + line for line in broken[1:])
    return made or ["none bound"]


def _broken_at_spaces(text, room):
    """`text` broken at its spaces into lines of at most `room` characters; a
    word longer than `room` stands on a line of its own."""
    broken, current = [], ""
    for word in text.split(" "):
        candidate = f"{current} {word}" if current else word
        if current and len(candidate) > room:
            broken.append(current)
            current = word
        else:
            current = candidate
    broken.append(current)
    return broken


def setting_names(term):
    """The names of the settings a component's term reads, in written order:
    the names among the keyword arguments of a method word, at any depth of
    its tuples and nested words; the bounds and the counts of a grid's
    spaced factors, with the arguments of their spacing words, and the count
    of a feasible factor, where they are names; and the node set of a listed
    factor, which is a setting a methods file declares, a set the stage
    defines or an expectation operator, told apart by the reader
    (specification 0.7 D1, D5)."""
    if isinstance(term, Components):
        for held in (term.method, term.grid):
            yield from setting_names(held)
    elif isinstance(term, T.Word):
        for keyword in term.arguments:
            yield from setting_names(keyword.value)
    elif isinstance(term, T.Name):
        yield term.name
    elif isinstance(term, T.Values):
        for item in term.items:
            yield from setting_names(item)
    elif isinstance(term, T.Nested):
        yield from setting_names(term.word)
    elif isinstance(term, T.Cartesian):
        for factor in term.factors:
            yield from setting_names(factor)
    elif isinstance(term, T.Spaced):
        for argument in (term.lower, term.upper, term.count):
            yield from setting_names(argument)
        yield from setting_names(term.spacing)
    elif isinstance(term, T.Feasible):
        yield from setting_names(term.count)
    elif isinstance(term, T.Listed):
        yield term.nodes


def typing_text(record):
    """A typing record as an entry of the stage, `policy.method : !egm`,
    `policy.handler : "cons-port:egm"`: the place and the component, the
    absolute spelling of a subject the union may have read relative to its
    block, and the method word, the grid or the program."""
    subject = f"{record.identity.address}.{record.identity.field}"
    value = record.equations[0]
    if isinstance(value, T.Word):
        return f"{subject} : {to_source(T.Method(value))}"
    if isinstance(value, T.Cartesian):
        return f"{subject} : {to_source(T.Grid(value))}"
    return f'{subject} : "{value}"'


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Components(Record):
    """The components typed at one place of a stage: `method`, the method component, the
    `Word` of the typing entry `<place>.method : !egm(tol=tol_v)` with its
    keyword arguments; `grid`, the grid component, the `Cartesian` of
    `<place>.grid : !Cartesian(a=(a_min, a_max, n_a))`; and `handler`, the
    program the binding `<place>.handler : "cons-port:egm"` names, which
    realizes the operator and is no classifier. Each is None where the place
    carries no entry for it; a place carries at least one. The record is
    read from the typing records of the definitions table and stored
    nowhere else (`stage.places`)."""

    method: object = None
    grid: object = None
    handler: str | None = None

    def __post_init__(self):
        if self.method is not None and not isinstance(self.method, T.Word):
            raise TypeError(f"Components.method must be a method word or None; got {self.method!r}")
        if self.grid is not None and not isinstance(self.grid, T.Cartesian):
            raise TypeError(f"Components.grid must be a grid or None; got {self.grid!r}")
        if self.handler is not None and (not isinstance(self.handler, str) or not self.handler):
            raise TypeError(
                f"Components.handler must be a program name or None; got {self.handler!r}"
            )

    @property
    def word(self):
        """The method word as written, `!egm`, with no arguments; the empty
        text where the place carries no method component."""
        return f"!{self.method.name}" if self.method is not None else ""

    @property
    def parts(self):
        """The printed parts, in order: the method word with its arguments,
        the grid and the handler in quotes, each where present."""
        parts = []
        if self.method is not None:
            parts.append(to_source(T.Method(self.method)))
        if self.grid is not None:
            parts.append(to_source(T.Grid(self.grid)))
        if self.handler is not None:
            parts.append(f'"{self.handler}"')
        return tuple(parts)

    def __str__(self):
        """One line: the parts three spaces apart."""
        return "   ".join(self.parts)

    __repr__ = __str__


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class BoundBlock(Record):
    """What a solution method's rows add to a stage at its operative level
    (specification 0.6 §§4.1, 7; specification 0.7 D8): the `builder` the
    method component stands on, the `method` word, the `condition` the
    method's row of the catalogue requires, listed among the stage's
    obligations and checked by nothing; the `rows` the lines fold to at the
    primitive and the sub-builder grain, which stand in the operative
    builder in place of the builder's declared rows; the `definitions` the
    rows write into the stage's table, new or in place of the builder's own,
    and the declared records those replace (`replaced`); the `obligations`
    of the rows; and the addresses of the builder's `declared_lines`, which
    its card prints under `Declared`."""

    builder: str
    method: str
    condition: str | None
    rows: tuple
    sub_builder_rows: tuple
    definitions: tuple
    replaced: tuple
    obligations: tuple
    declared_lines: tuple


@dataclasses.dataclass(frozen=True)
class MethodOption:
    """One typed option of a method: the kind of value the option
    takes, whether the method requires it, and the conditions on it. The
    method table of `stage/method_table.py` declares one for each option of
    each method it admits, and a bound method's card prints them."""

    kind: str
    required: bool = False
    conditions: tuple = ()

    def __str__(self):
        return self.kind + (" (required)" if self.required else "")

    __repr__ = __str__


class _ReadOnlyEntries:
    """The mapping protocol of a record that holds its entries in the
    read-only mapping `entries`: lookup, iteration and length read it."""

    def __getitem__(self, key):
        return self.entries[key]

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __contains__(self, key):
        return key in self.entries

    def get(self, key, default=None):
        return self.entries.get(key, default)

    def keys(self):
        return self.entries.keys()

    def values(self):
        return self.entries.values()

    def items(self):
        return self.entries.items()


@dataclasses.dataclass(frozen=True, repr=False)
class Metadata(_ReadOnlyEntries):
    """The authored `@` annotations other than the stage name, in file order.
    The read-only `entries` mapping supports lookup and displays one entry
    per line, or `none` when empty.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""

    entries: object

    def __str__(self):
        if not self.entries:
            return "none"
        width = max(len(str(key)) for key in self.entries) + 3
        return "\n".join(
            f"{key!s:<{width}}{value}".rstrip() for key, value in self.entries.items()
        )

    __repr__ = __str__


@dataclasses.dataclass(frozen=True, repr=False)
class Provenance(_ReadOnlyEntries):
    """How this stage version was built, retained in a read-only `entries`
    mapping: source path or origin, text, digest, trellis position, binding
    sources and package and grammar versions. Lookup retains every entry;
    the display shows the source location and digest, not the source text.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""

    entries: object

    def __str__(self):
        if not self.entries:
            return "none"
        said = [(key, self.entries[key]) for key in ("path", "origin") if key in self.entries]
        if "sha256" in self.entries:
            said.append(("sha256", self.entries["sha256"]))
        if not said:
            return "source not recorded"
        width = max(len(key) for key, _ in said) + 3
        return "\n".join(f"{key:<{width}}{value}".rstrip() for key, value in said)

    __repr__ = __str__


# --- the construction's records ---


@dataclasses.dataclass(frozen=True, eq=False, repr=False, kw_only=True)
class BlockData(Record):
    """The data of a builder box while the stage is constructed: one authored
    block. The box's name identifies the block. `perch_from` and `perch_to`
    are the perch words of its input and output sides (`arvl`, `dcsn`,
    `cntn`; None for a side written without one); `statements_outside_nodes`
    are the records the builder keeps at its own level, in textual order: its
    output statements, the ones that define an output field of its block,
    the aliases no node follows, and its `!doc` lines; `nodes` are the
    builder's authored nodes, each a `NodeData` record holding its address,
    its records and the identities it reads and writes, and empty for an
    atomic builder, one with no `!node` line; `branch_labels` are the labels
    of a branching block's nested blocks in source order, empty otherwise,
    from which the branches are derived; `unread_inputs` are the sorts of the
    value inputs a backward block's header lists and no line of the block
    reads, which the box's dom leaves out and the stage records as
    diagnostics (AAS, 17 October 2026), empty otherwise. The constructed
    builder is a `Builder` bubble whose data is `()`."""

    perch_from: str | None
    perch_to: str | None
    statements_outside_nodes: tuple
    nodes: tuple
    branch_labels: tuple
    unread_inputs: tuple = ()

    def __post_init__(self):
        require_tuple(self, "statements_outside_nodes", "nodes", "branch_labels", "unread_inputs")
        for node in self.nodes:
            if not isinstance(node, NodeData):
                raise TypeError(
                    f"BlockData.nodes are the builder's authored nodes, each a "
                    f"NodeData record, and are empty for an atomic builder; got "
                    f"{type(node).__name__}"
                )


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class NodeData(Record):
    """One authored node of a builder: what a `!node` line is inside its
    block, the grain at which a modeler says "this is a separate function of
    the implementation". `node_id` is the line's term address;
    `block_id` the builder it is in; `statements` the alias records folded
    into the node, in textual order, followed by the node's own record;
    `marks` the marks the line carries (`node`); `branch` the label of the
    branch the node belongs to in a branching block, None in an ordinary
    stage, and None in a branching one too, since the construction builds no
    `!node` inside a branch; `inputs` the ordered local identities the
    dependency walk of the construction resolved as the node's inputs, and
    `outputs` the identities its own line defines. A record of the
    construction, held by the builder's `BlockData`: the constructed node is
    a `Builder` bubble whose data is `()`."""

    node_id: str
    _: dataclasses.KW_ONLY
    block_id: str
    statements: tuple
    marks: tuple
    branch: str | None
    inputs: tuple = ()
    outputs: tuple = ()

    def __post_init__(self):
        require_tuple(self, "statements", "marks", "inputs", "outputs")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class BlockHeader(Record):
    """The inputs the author wrote in a block's header, held on the block's
    box of an initial diagram. `inputs` holds
    the sorts of the declared input fields in the order the header writes them.
    A control a header names among its inputs is the coordinate at which the
    block's lines are read and is no wire of an initial diagram, so the box's
    own inputs are fewer than the header's and the declared inputs are authored
    information the graph no longer determines. The declared outputs are the
    box's own wires on every block, so they are read from the box and are not
    held here (`block_lines.header_of`). Its readers are the `header` line of
    a block's and a builder's card, the block lines of the stage's sheet, the
    fields table and the perch rule. `unread` holds the sorts of the value
    inputs the header lists and no line of the block reads, in header order:
    they are no inputs of the block, and the stage records each as a
    diagnostic (`block_lines.unread_inputs_of`; AAS, 17 October 2026)."""

    inputs: tuple
    unread: tuple = ()

    def __post_init__(self):
        require_tuple(self, "inputs", "unread")


# The roles of a statement record: a node (a box of its own inside the
# builder), an output statement (one that defines an output field of its
# block), an alias (an intermediate name folded into the line that follows),
# and documentation (a `!doc` line).
ROLES = ("node", "output", "alias", "doc")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Line(Record):
    """An authored line as the construction and the queries read it: its
    address, its ordinal in the block (from 1), its role (`output`, `alias`,
    `doc` or `node`), the entries of its annotation (`tags`), its operator
    occurrences (`operators`, a tuple of `OperatorOccurrence`, the implicit
    `solve` included) and its retained term (`core`). During construction the
    typing pass adds the kind of its equation (`equation_kind`: `definition`,
    `relation` or `documentation`), its unknowns and its typed inputs and
    outputs. After construction a line is a `line` record of the definitions
    table keyed by its address, and `stage_names.lines_of` computes this
    reading of it; the record is never stored on the stage."""

    address: str
    _: dataclasses.KW_ONLY
    ordinal: int
    role: str
    tags: tuple
    operators: tuple
    core: object = dataclasses.field(default=None, hash=False, repr=False)
    equation_kind: str | None = None
    unknowns: tuple = ()
    inputs: tuple[ResolvedName, ...] = ()
    outputs: tuple[ResolvedName, ...] = ()

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(f"a line's role is one of {', '.join(ROLES)}; got {self.role!r}")
        require_tuple(self, "tags", "operators")
        if self.core is not None and not is_frozen_record(self.core):
            raise TypeError("Line.core must be a retained (frozen) term")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class OperatorOccurrence(Record):
    """One numerical operator inside an authored line: the expectation over
    the shocks in `V = E_{Ψ,θ}(V[>])`, the root-finding `solve` that defines
    the portfolio share in `ς = solve_{ς}(E_{Ψ,θ}(dV[>]*(Ψ - R)))`, the
    `solve` that an implicit statement such as `c = c[>]` records, an
    `argmax`, an `upper_env`, an authored `evaluate`, the derivative operator
    in a definition `𝑑𝑢 := D_{c}(𝑢)`. A methods file names it by its operator
    (`on: E_Ψ_θ`, one method for every occurrence in the stage) or by the line
    it is in (`on: policy.foc.solve`), so the record is the place a method is
    attached. `head` is the operator name as written (`E`, `argmax`, `solve`,
    `upper_env`, `evaluate`, `D`); `subscripts` its shock or binder names (the
    binder: the variable named in the operator's subscript, over which the
    argmax or solve ranges, ς in `solve_{ς}(…)`) in the authored order, never
    sorted; `position` is the path of term fields
    from the statement's equation (the `core` of a slack statement, the
    statement itself otherwise) to the occurrence — `("rhs",)` when the
    occurrence is the whole right side, `("rhs", "args", 0)` when it is the
    first argument of the right side's operator, `("value",)` or `("body",)`
    for a definition's body, a list field's index following its name — and
    `()` for the `solve` an implicit statement records, which is the
    statement itself and no sub-expression; `unknown` names the coordinate
    solved for. The actual residual is part of the containing equation;
    its original printed form is a stage presentation annotation.
    `target` says what kind of solution a
    `solve`, `argmax`, or `upper_env` seeks: `interior_root`,
    `constrained_optimum`, or `selection`, None for the other operators."""

    head: str
    _: dataclasses.KW_ONLY
    subscripts: tuple
    position: tuple
    unknown: str | None = None
    target: str | None = None

    def __post_init__(self):
        require_tuple(self, "subscripts", "position")

    @property
    def stage_wide_name(self) -> str:
        """The name under which a methods file governs every occurrence of
        this operator in the stage: `E_` followed by the
        shock names joined by `_`, in the authored order (`E_Ψ_θ`, `E_θ`),
        for an expectation; the head itself for every other operator."""
        if self.head == "E":
            return "_".join(("E",) + self.subscripts)
        return self.head


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class ResolvedName(Record):
    """One input or output of a line, resolved: its identity, its
    mathematical type (`value_type`), its role and its perch."""

    identity: Identity | str
    _: dataclasses.KW_ONLY
    value_type: ExpressionType
    role: str
    perch: str | None

    def __post_init__(self):
        if isinstance(self.identity, Identity):
            pass
        elif not isinstance(self.identity, str) or not self.identity:
            raise TypeError(
                f"ResolvedName.identity must be a non-empty string; got {self.identity!r}"
            )
        if not isinstance(self.value_type, ExpressionType):
            raise TypeError(
                f"ResolvedName.value_type must be a ExpressionType; got "
                f"{type(self.value_type).__name__}"
            )
        if not isinstance(self.role, str) or not self.role:
            raise TypeError(f"ResolvedName.role must be a non-empty string; got {self.role!r}")
        if self.perch is not None and (not isinstance(self.perch, str) or not self.perch):
            raise TypeError(
                f"ResolvedName.perch must be a non-empty string or None; got {self.perch!r}"
            )


# The kinds of a mathematical type.
TypeKind = Literal["scalar", "state", "set", "function", "relation", "distribution", "opaque"]


TYPE_KINDS = ("scalar", "state", "set", "function", "relation", "distribution", "opaque")


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class ExpressionType(Record):
    """The mathematical type of an expression, as the typing pass reads it:
    its kind; the set of a scalar, a state, a distribution or an opaque
    value (`domain`); and the argument and result types of a function or a
    relation."""

    kind: TypeKind
    domain: object | None
    _: dataclasses.KW_ONLY
    arguments: tuple["ExpressionType", ...] = ()
    results: tuple["ExpressionType", ...] = ()

    def __post_init__(self):
        if self.kind not in TYPE_KINDS:
            raise ValueError(
                f"ExpressionType.kind must be one of {', '.join(TYPE_KINDS)}; got {self.kind!r}"
            )
        if self.domain is not None and not (
            isinstance(self.domain, Identity) or isinstance(self.domain, str) and self.domain
        ):
            raise TypeError(
                f"ExpressionType.domain must be a non-empty set name, an identity or None; got "
                f"{self.domain!r}"
            )
        _require_entries(self, "arguments", ExpressionType)
        _require_entries(self, "results", ExpressionType)
        if self.kind in ("scalar", "state", "distribution", "opaque"):
            if self.domain is None:
                raise ValueError(f"ExpressionType.domain is required for {self.kind!r}")
            if self.arguments:
                raise ValueError(f"ExpressionType.arguments must be empty for {self.kind!r}")
            if self.results:
                raise ValueError(f"ExpressionType.results must be empty for {self.kind!r}")
        if self.kind in ("function", "relation") and self.domain is not None:
            raise ValueError(
                f"ExpressionType.domain must be None for {self.kind!r}; its ordered "
                f"arguments and results carry the boundary"
            )


# --- the validators and the equality of records ---


def require_tuple(record, *names) -> None:
    """Refuses a field among `names` that is not a tuple, so that the record
    hashes."""
    for name in names:
        value = getattr(record, name)
        if not isinstance(value, tuple):
            raise TypeError(
                f"{type(record).__name__}.{name} must be a tuple, so that the "
                f"record hashes; got {type(value).__name__}"
            )


def _require_entries(record, name: str, expected_type: type) -> None:
    """Refuses a field that is not a tuple of `expected_type`."""
    require_tuple(record, name)
    for index, value in enumerate(getattr(record, name)):
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{type(record).__name__}.{name}[{index}] must be a "
                f"{expected_type.__name__}; got {type(value).__name__}"
            )


def _require_strings(record, *names, nonempty: bool = True) -> None:
    """Refuses a field among `names` that is not a tuple of identities and
    strings, empty strings refused where `nonempty` is set."""
    for name in names:
        require_tuple(record, name)
        for index, value in enumerate(getattr(record, name)):
            if isinstance(value, Identity):
                continue
            if not isinstance(value, str) or (nonempty and not value):
                raise TypeError(
                    f"{type(record).__name__}.{name}[{index}] must be a "
                    f"{'non-empty ' if nonempty else ''}string; got {value!r}"
                )


def _require_graph(record, name: str, *, optional: bool = False) -> None:
    """Refuses a field that is not a graph, or None where it is optional."""
    value = getattr(record, name)
    if optional and value is None:
        return
    if not isinstance(value, Hypergraph):
        raise TypeError(
            f"{type(record).__name__}.{name} must be a "
            f"discopy.frobenius.Hypergraph; got {type(value).__name__}"
        )


def _require_distinct_identities(record, name: str) -> None:
    """Refuses a field whose entries repeat an identity."""
    identities = tuple(value.identity for value in getattr(record, name))
    if len(identities) != len(set(identities)):
        raise ValueError(
            f"{type(record).__name__}.{name} identities must be distinct; got {identities!r}"
        )


# The scalars a record compares and writes by value.
_FINITE_SCALARS = (str, bytes, int, float, complex, bool, type(None))


@comparison_answered_once
def values_equal(left, right):
    """Whether two values a record holds are equal: two graphs by their parts,
    and by DisCoPy's graph equality where the parts differ; a type by
    DisCoPy's equality; a scalar, a mapping, a sequence, a set and a frozen
    record by their contents, a frozen record by all its fields, whatever
    equality its class defines; any other value, a subclass of a scalar
    included, by identity.
    """
    if isinstance(left, Hypergraph) or isinstance(right, Hypergraph):
        if not isinstance(left, Hypergraph) or not isinstance(right, Hypergraph):
            return False
        # Graphs with equal parts are equal, and need no search for a
        # correspondence of their wires.
        if (
            left.dom == right.dom
            and left.cod == right.cod
            and left.wires == right.wires
            and left.spider_types == right.spider_types
            and left.boxes == right.boxes
        ):
            return True
        return left == right
    if isinstance(left, cat.Ob) or isinstance(right, cat.Ob):
        # a wire's type (a `Sort`, a `Ty`): DisCoPy's own equality
        return isinstance(left, cat.Ob) and isinstance(right, cat.Ob) and left == right
    if left is right:
        return True
    if type(left) in _FINITE_SCALARS or type(right) in _FINITE_SCALARS:
        return type(left) in _FINITE_SCALARS and type(right) in _FINITE_SCALARS and left == right
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        return (
            isinstance(left, Mapping)
            and isinstance(right, Mapping)
            and _unordered_equal(tuple(left.items()), tuple(right.items()), values_equal)
        )
    if isinstance(left, (tuple, list)) or isinstance(right, (tuple, list)):
        return (
            type(left) is type(right)
            and len(left) == len(right)
            and all(values_equal(a, b) for a, b in zip(left, right))
        )
    if isinstance(left, (set, frozenset)) or isinstance(right, (set, frozenset)):
        return (
            isinstance(left, (set, frozenset))
            and isinstance(right, (set, frozenset))
            and _unordered_equal(left, right, values_equal)
        )
    if is_frozen_record(left) or is_frozen_record(right):
        return type(left) is type(right) and values_equal(
            tuple(_record_items(left)), tuple(_record_items(right))
        )
    return left is right


def _unordered_equal(left, right, equal):
    """Whether two collections hold equal entries in any order, each matched
    by `equal`, without their hashes."""
    if len(left) != len(right):
        return False
    unmatched = list(right)
    for item in left:
        for index, candidate in enumerate(unmatched):
            if equal(item, candidate):
                unmatched.pop(index)
                break
        else:
            return False
    return True


def _record_items(value):
    """Each field of a frozen record, by name, with its value."""
    for field in dataclasses.fields(value):
        yield field.name, getattr(value, field.name)


def canonical_text(value):
    """The canonical text of a value a record holds, which the record's hash
    and repr read, as does the hash of a DisCoPy box that holds the record.

    A graph is written `<Hypergraph>`, so two different graphs share a text;
    equality compares graphs by `values_equal`. An object of another type
    is written by its id.
    """
    if isinstance(value, Hypergraph):
        return "<Hypergraph>"
    if isinstance(value, cat.Ob):
        return repr(value)
    if type(value) in _FINITE_SCALARS:
        if isinstance(value, complex) and value.imag == 0:
            value = value.real
        if isinstance(value, bool) or isinstance(value, float) and value.is_integer():
            value = int(value)
        return repr(value)
    if isinstance(value, Mapping):
        entries = sorted((canonical_text(k), canonical_text(v)) for k, v in value.items())
        return "{" + ", ".join(f"{k}: {v}" for k, v in entries) + "}"
    if isinstance(value, (tuple, list)):
        content = ", ".join(canonical_text(item) for item in value)
        if isinstance(value, tuple):
            return "(" + content + ("," if len(value) == 1 else "") + ")"
        return "[" + content + "]"
    if isinstance(value, (set, frozenset)):
        return "frozenset({" + ", ".join(sorted(canonical_text(item) for item in value)) + "})"
    if is_frozen_record(value):
        content = ", ".join(
            f"{name}={canonical_text(item)}" for name, item in _record_items(value)
        )
        return f"{type(value).__qualname__}({content})"
    return f"<identity:{id(value)}>"
