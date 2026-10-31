"""The identity of a wire, a box, a definition and a condition.

An identity is one small frozen record, made by the constructor of `Identity`
and read by its attributes. Its printed form is its spelling: `cons:dcsn:c`
for a field wire, `cons:function:cntn:V` for a function wire,
`cons:g:dcsn_to_cntn` for a law of motion, `cntn_to_dcsn:Expectation:1` for a
primitive operator box. Where DisCoPy needs a string, the name of an `Ob` or
of a `Box`, it is given `str(identity)`, and no other code writes a spelling.
A reader takes the kind, the perch, the field, the occurrence or the owner of
an identity from its attributes and never splits its spelling, so that a
field named `result` or a stage name holding a colon cannot be misread. A
name that would collide with the spelling is refused here, under the rule
`identity-collision` of `refusals.RULES`.

The namespaces of the record are the wires, the boxes, the definitions and
the identities a condition names. The record also spells the two set names of
the typing pass whose second segment is one of its namespaces:
`<stage>:set:<address>:<position>`, the anonymous set written at a position
of the text, and `primitive:set:<name>`. The pass's other names,
`<identity>:domain`, `<identity>:domain-site:<n>`, `<identity>:subjects`,
`unresolved:<address>:…` and `opaque:<identity>`, name a set term and no
wire, box, definition or condition; their segments belong to no namespace of
the record, and they are plain strings.
"""

from __future__ import annotations

import dataclasses
import functools

from bellman.syntax import vocabulary

# The perches an identity may carry: the three perches of a stage and the
# token of a shock, which belongs to none.
PERCHES = vocabulary.PERCHES + (vocabulary.SHCK,)

# The kinds spelled `<stage>:<kind>:…`, the definitions and the wires of
# a stage.
STAGE_KINDS = (
    "field",  # <stage>:<perch>:<field>
    "function",  # <stage>:function:<perch>:<field>[:g][:<owner>]; <stage>:function:<name>
    "choice",  # <stage>:choice:<perch>:<field>[:<owner>]
    "measure",  # <stage>:measure:<perch>[:<label>][:<mark>][:<subjects>]
    "alias",  # <stage>:alias:<address>:<field>
    "set",  # <stage>:set:<name>
    "parameter",  # <stage>:parameter:<name>
    "multiplier",  # <stage>:multiplier:<name>
    "distribution",  # <stage>:distribution:<subjects>
    "correspondence",  # <stage>:correspondence:<name>
    "g",  # <stage>:g:<block>
    "G",  # <stage>:G:<block>
    "law",  # <stage>:law:<address>
    "unplaced",  # <stage>:<name>, a name the stage declares at no perch
)

# The kinds of a primitive operator box and of the wires it writes, spelled
# `<address>:<kind>[:<segment>][:<owner>][:<mark>]`. `Argmax` is the kind of
# the row an operative `argmax` line forms, the file's operator word
# capitalized, so that the table of definitions holds it apart from the
# operator head `argmax`.
OPERATOR_KINDS = (
    "Pullback",
    "Aggregation",
    "Expectation",
    "Evaluation",
    "Argmax",
    "DistributionExtension",
    "PolicyInsertion",
    "Pushforward",
    "distribution-extended-measure",
)

# The kinds spelled without a stage and without an address.
FREE_KINDS = (
    "external",  # external:<name>[:result]
    "primitive",  # primitive:real, primitive:set:<name>
    "block",  # <block>
    "line",  # <block>.<statement>
    "function-parameter",  # <function identity>:parameter:<n>:<name>
)

KINDS = STAGE_KINDS + OPERATOR_KINDS + FREE_KINDS

# The trailing tokens a reader tests for. An authored name equal to one of them
# would stand where the reader looks, so the constructor refuses it.
RESERVED_TAILS = ("result", "declared", "merged")

# The qualifier the spelling writes itself, by the kind that writes it. A kind
# absent from the table writes none, except `set`, whose mark is the position
# of the text at which an anonymous set of the typing pass is written, and is
# free text.
MARKS = {
    "function": ("g",),
    "choice": ("g",),
    "measure": ("with-policy", "with-distribution"),
    "external": ("result",),
    "primitive": ("set",),
}
# The words the spelling writes for itself. A name equal to one of them,
# written where the spelling writes its own, would spell two identities alike,
# so the constructor refuses it there: equality is by the spelling, which the
# constructor keeps injective on the fields it admits.
QUALIFIERS = ("g", "with-policy", "with-distribution") + RESERVED_TAILS

# The separator of the segments of a spelling. An authored name containing it
# would add a segment, so the constructor refuses it.
SEPARATOR = ":"


@functools.total_ordering
@dataclasses.dataclass(frozen=True, eq=False)
class Identity:
    """The identity of one wire, box, definition or condition.

    `kind` is the namespace, and it fixes how the other fields are spelled.
    `stage` is the stage's declared name, None for an identity that names no
    stage (`external:exp`). `address` is the block, the line address
    (`policy.InvEuler`) or the source address at which the identity is made:
    the first segment of an operator box's name, the last segment of a law
    of motion's, an aggregator's and an alias's.
    `perch` is the information set of a wire: `arvl`, `dcsn`, `cntn`, or
    `shck` for a shock. `field` is the name of the field, the parameter, the
    set or the function the identity carries, and on a measure the label of
    the branch it stands on (`keep`). `owner` holds a name, the block or the
    `!node` that reads an occurrence where several read one statement, or a
    nested identity, the function a formal parameter belongs to. `subjects`
    is the one tuple field: the shocks of a distribution or of an extended
    measure, spelled joined by `_`. `occurrence` numbers an expectation or an
    aggregation within its statement, or counts the merged boxes of one
    owner. `mark` is the last
    qualifier: `g` for a function composed with a law of motion,
    `with-policy` and `with-distribution` for a measure, and the three
    reserved words `result`, `declared` and `merged`. Rows write `result` on
    an occurrence's result wire and `merged` on a merged box, and readers
    test for both. No row writes `declared` and no module reads it since the
    `Selection` kind retired; the word stays in `RESERVED_TAILS` only because
    the identity-collision refusal text of `refuse_colliding_name` names the
    three words, and a refusal text changes only in a re-recording AAS
    approves (DR-0798).

    `str(identity)` is the spelling, and `repr` is the repr of the spelling,
    so that a message that prints an identity with `!r` prints its spelling
    in quotes. An identity equals another identity or a plain string that is
    spelled alike, and orders against either by its spelling. The constructor
    keeps the spelling injective on the fields it admits, so that equality is
    transitive and agrees with the hash.

    `mark` writes three things, which the constructor tells apart by the
    kind: the last qualifier of a wire or a box (`g`, `with-policy`,
    `with-distribution`, `result`, `declared`, `merged`); the segment after
    `primitive` of a primitive set, the `set` of `primitive:set:<name>`; and
    the position of the text at which an anonymous set of the typing pass is
    written, the `('domain', 'β')` of `<stage>:set:<address>:<position>`. The
    second and the third belong to that pass, and have no field of their
    own."""

    kind: str
    stage: str | None = None
    address: str | None = None
    perch: str | None = None
    field: str | None = None
    owner: str | Identity | None = None
    subjects: tuple = ()
    occurrence: int | None = None
    mark: str | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"Identity.kind is one of {', '.join(KINDS)}; got {self.kind!r}")
        if not isinstance(self.subjects, tuple):
            raise TypeError(
                f"Identity.subjects must be a tuple; got {type(self.subjects).__name__}"
            )
        if self.perch is not None and self.perch not in PERCHES:
            raise ValueError(
                f"Identity.perch is one of {', '.join(PERCHES)} or None; got {self.perch!r}"
            )
        for name in ("stage", "address", "field", "mark"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"Identity.{name} must be a name or None; got {value!r}")
        if self.owner is not None and not isinstance(self.owner, (str, Identity)):
            raise TypeError(
                f"Identity.owner must be a name, a nested identity or None; "
                f"got {type(self.owner).__name__}"
            )
        if self.occurrence is not None and (
            not isinstance(self.occurrence, int) or isinstance(self.occurrence, bool)
        ):
            raise TypeError(
                f"Identity.occurrence must be a whole number or None, since it writes a "
                f"segment of digits; got {self.occurrence!r}"
            )
        self._one_middle_segment()
        self._one_word_per_segment()
        if self.kind == "set" and self.field is None and not (self.address and self.mark):
            raise ValueError(
                "an anonymous set names the address and the position it is written at"
            )
        if self.kind in STAGE_KINDS and not self.stage:
            raise ValueError(
                f"an identity of kind {self.kind!r} names its stage; got {self.stage!r}"
            )
        if self.kind in OPERATOR_KINDS and not self.address:
            raise ValueError(
                f"an identity of kind {self.kind!r} names the address it is born at; "
                f"got {self.address!r}"
            )
        refuse_colliding_name(self.stage, "stage")
        refuse_colliding_name(self.field, "field")
        if self.kind != "set" or self.field is not None:
            # the anonymous set of the typing pass carries the position of the
            # text at which it is written, which is no authored name
            refuse_colliding_name(self.address, "address")
        for subject in self.subjects:
            refuse_colliding_name(subject, "shock")
        if isinstance(self.owner, str):
            refuse_colliding_name(self.owner, "block")

    # -- the spelling is injective on the fields admitted --------------------

    def _one_middle_segment(self):
        """A primitive operator box writes one of `field`, `occurrence` and
        `subjects` after its kind, so no two of them may be set: `field` and
        `occurrence` would otherwise spell alike, `dcsn_to_arvl:Pullback:1`
        standing for the field `1` and for the first box of the owner."""
        if self.kind not in OPERATOR_KINDS:
            return
        written = [
            name
            for name, value in (
                ("field", self.field),
                ("occurrence", self.occurrence),
                ("subjects", self.subjects or None),
            )
            if value is not None
        ]
        if len(written) > 1:
            raise ValueError(
                f"an identity of kind {self.kind!r} writes one segment after its kind, and "
                f"{' and '.join(written)} are given; "
                f"write the field, the occurrence or the subjects"
            )
        if isinstance(self.field, str) and self.field.isdigit():
            raise ValueError(
                f"the field {self.field!r} of an identity of kind {self.kind!r} is a number, "
                f"which is how an occurrence writes its own segment; a box of the field "
                f"{self.field!r} and the {self.field}th box of its owner would spell alike"
            )

    def _one_word_per_segment(self):
        """No field writes a word the spelling writes for itself. `mark` takes
        the qualifier of its kind and nothing else, and a name standing where a
        qualifier stands — the owner of a function wire, a subject of a
        measure — is refused, so that `<stage>:function:<perch>:<field>:g` is
        the composition with the law of motion and never a block named `g`."""
        admitted = RESERVED_TAILS if self.kind in OPERATOR_KINDS else MARKS.get(self.kind, ())
        if (
            self.mark is not None
            and self.mark not in admitted
            and not (self.kind == "set" and self.field is None)
        ):
            raise ValueError(
                f"Identity.mark of kind {self.kind!r} is one of {', '.join(admitted) or 'none'}; "
                f"got {self.mark!r}"
            )
        if isinstance(self.owner, str) and self.owner in QUALIFIERS:
            raise IdentityCollision(
                f"the block {self.owner!r} is one of the words {', '.join(QUALIFIERS)}, which the "
                f"spelling writes for itself where a block stands; "
                f"write another name for the block",
                name=self.owner,
            )
        for subject in self.subjects:
            if not subject:
                raise ValueError(
                    "Identity.subjects holds no empty name, the subjects being spelled joined"
                )
            if subject in QUALIFIERS:
                raise IdentityCollision(
                    f"the shock {subject!r} is one of the words {', '.join(QUALIFIERS)}, "
                    f"which the spelling writes for itself where a subject stands; "
                    f"write another name for the shock",
                    name=subject,
                )

    # -- the spelling -------------------------------------------------------

    def _segments(self):
        kind, mark = self.kind, self.mark
        if kind == "field":
            return (self.stage, self.perch, self.field)
        if kind in ("function", "choice"):
            head = (self.stage, kind) + ((self.perch, self.field) if self.perch else (self.field,))
            return (
                head + (("g",) if mark == "g" else ()) + ((str(self.owner),) if self.owner else ())
            )
        if kind == "measure":
            # a measure on one branch writes the branch's label after its
            # perch; a label is a name of the grammar and holds no hyphen, so
            # it never spells like `with-policy`
            return (
                (self.stage, "measure", self.perch)
                + ((self.field,) if self.field else ())
                + ((mark,) if mark else ())
                + ((_joined(self.subjects),) if self.subjects else ())
            )
        if kind == "alias":
            return (self.stage, "alias", self.address, self.field)
        if kind == "set" and self.field is None:
            # an anonymous set of the typing pass, named by the address and
            # the position of the text at which it is written
            return (self.stage, "set", self.address, self.mark)
        if kind in ("set", "parameter", "multiplier", "correspondence"):
            return (self.stage, kind, self.field)
        if kind == "primitive":
            return ("primitive",) + ((mark,) if mark else ()) + (self.field,)
        if kind == "unplaced":
            return (self.stage, self.field)
        if kind == "distribution":
            return (self.stage, "distribution", _joined(self.subjects))
        if kind in ("g", "G", "law"):
            return (self.stage, kind, self.address)
        if kind == "external":
            return ("external", self.field) + ((mark,) if mark else ())
        if kind in ("block", "line"):
            return (self.address,)
        if kind == "function-parameter":
            return (str(self.owner), "parameter", str(self.occurrence), self.field)
        # a primitive operator box and the wires it writes
        segment = (
            (self.field,)
            if self.field is not None
            else (str(self.occurrence),)
            if self.occurrence is not None
            else (_joined(self.subjects),)
            if self.subjects
            else ()
        )
        return (
            (self.address, kind)
            + segment
            + ((str(self.owner),) if self.owner else ())
            + ((mark,) if mark else ())
        )

    @functools.cached_property
    def _spelling(self):
        return SEPARATOR.join(self._segments())

    def __str__(self):
        return self._spelling

    def __repr__(self):
        return repr(str(self))

    def __format__(self, specification):
        return format(str(self), specification)

    # -- equality and order -------------------------------------------------

    def __eq__(self, other):
        # An identity equals what is spelled as it is: string equality read
        # through `str`, hence transitive and in agreement with the hash.
        # DisCoPy names a wire and a box by a string, so a table keyed by
        # identities is read with either.
        if isinstance(other, Identity):
            return self is other or self._spelling == other._spelling
        if isinstance(other, str):
            return self._spelling == other
        return NotImplemented

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other):
        if isinstance(other, (Identity, str)):
            return str(self) < str(other)
        return NotImplemented

    # -- the attributes a reader reads in place of the spelling ---------------

    @property
    def identity(self):
        """An identity is its own identity, so that a reader given either a
        wire's sort or the wire asks the same question."""
        return self

    @property
    def is_result(self):
        """True for the wire an occurrence writes,
        `<address>:<Kind>:<n>:result`."""
        return self.mark == "result"

    @property
    def is_merged(self):
        """True for a box made by merging the parallel boxes of one owner."""
        return self.mark == "merged"

    @property
    def carries_field(self):
        """True for a wire that carries a field of the file: a field wire, a
        function wire or a choice wire, and not an occurrence's result."""
        return self.kind == "field" or (
            self.kind in ("function", "choice") and self.perch is not None
        )

    @property
    def second_segment(self):
        """The word the spelling writes in its second segment: the kind of a
        function, a choice or a measure wire and of a definition, the perch of
        a field wire, the kind of the operator of a box.

        It reads the spelling by position, inside the record. Its one reader,
        `grains.kind_of`, answers with it for a box of the wiring, a
        spider, a swap, a cup or a cap, which DisCoPy names after the wires it
        joins and not by an identity: such a box reports as its kind the second
        segment of its first wire's spelling."""
        segments = self._segments()
        return segments[1] if len(segments) > 1 else None

    @property
    def stem(self):
        """The name this identity carries: the field, the parameter, the set or
        the function it names; the subjects of a distribution or a measure,
        joined as they are spelled; the spelling itself where it names none."""
        if self.field is not None:
            return self.field
        if self.subjects:
            return _joined(self.subjects)
        return str(self)

    @property
    def block(self):
        """The block of the identity's address: `policy` of the line address
        `policy.InvEuler`, the block itself for a builder's box; None where the
        identity has no address."""
        address = self.address
        return None if address is None else address.split(".", 1)[0]

    @property
    def statement(self):
        """The statement of the identity's address, `InvEuler` of
        `policy.InvEuler`; None where the address is a block alone or the
        identity has no address. Reading the dot reads the authored address the
        identity holds, not its spelling."""
        address = self.address
        if address is None or "." not in address:
            return None
        return address.split(".", 1)[1]

    @property
    def branch(self):
        """The label of the nested block of the identity's address, `keep` of
        the line `dcsn_to_cntn.keep.cash_on_hand`; None where the address names
        no nested block. A nested block is addressed by its label under its
        block, and its lines under it. Reading the dots reads the address, as
        `block` and `statement` read it."""
        parts = () if self.address is None else self.address.split(".")
        return parts[1] if len(parts) == 3 else None

    def key_within(self, holder):
        """The part of the spelling that stands after `holder`, the address of
        a piece that contains this identity, and None where this identity is
        not rooted at it: `cntn_to_dcsn:Pullback` within `cntn_to_dcsn` is
        `Pullback`, `policy.InvEuler:Expectation:1` within `policy` is
        `InvEuler:Expectation:1`, and the line `dcsn_to_cntn.keep.cash_on_hand`
        within its branch `dcsn_to_cntn.keep` is `cash_on_hand`. The segments
        are joined here and are read apart nowhere."""
        if self.address is None:
            return None
        rest = self._segments()[1:]
        if self.address == holder:
            return SEPARATOR.join(rest) or None
        if self.address.startswith(holder + "."):
            return SEPARATOR.join((self.address[len(holder) + 1 :],) + tuple(rest))
        return None


def refuse_colliding_name(name, what):
    """Refuse `name`, written as `what` (a stage, a block, a statement, a
    field, a shock, a parameter, a set or a function), when it would collide
    with the spelling of an identity. The construction calls it where it first
    reads a name that no identity yet carries — the stage's own name, a block
    id, a statement id — so that the refusal names the authored item; the
    constructor of `Identity` below calls it for every other name."""
    if not isinstance(name, str):
        return
    if SEPARATOR in name:
        raise IdentityCollision(
            f"the {what} {name!r} contains {SEPARATOR!r}, the separator of the segments of an "
            f"identity, so the identity it is written into would read as one segment more than "
            f"it has; write the {what} without a colon",
            name=name,
        )
    if name in RESERVED_TAILS:
        raise IdentityCollision(
            f"the {what} {name!r} is one of the reserved words {', '.join(RESERVED_TAILS)}, "
            f"by which a reader knows an occurrence's result wire, a declared wire "
            f"and a merged box from the last segment of an identity; "
            f"write another name for the {what}",
            name=name,
        )


# The rule of `refusals.RULES` under which a colliding name is refused.
COLLISION_RULE = "identity-collision"


class IdentityCollision(ValueError):
    """An authored name that would collide with the spelling of an identity: a
    name containing the separator, or a name equal to one of the reserved
    trailing tokens. It carries the rule name and the offending name, and the
    caller that has a source position turns it into a `ConstructionError` at
    that position."""

    def __init__(self, message, *, name, rule=COLLISION_RULE):
        super().__init__(message)
        self.message, self.name, self.rule = message, name, rule


def _joined(subjects):
    """The subjects joined by `_`, as the spelling writes them."""
    return "_".join(subjects)


def piece_identity(address):
    """The identity of a piece of a graph named by an authored address: a
    builder or a block for a bare block id, a sub-builder for the address of a
    `!node` line. Reading the dot reads the authored address, not the spelling
    of an identity. It reads a top-level block id or a line's address and
    nothing else: a nested block's address, `dcsn_to_cntn.keep`, holds one dot
    as a line's does, so its identity is held by its stored bubble and is not
    guessed here."""
    return Identity("line" if "." in address else "block", address=address)


def box_identity(box):
    """The identity a box of a constructed stage is named by."""
    try:
        return box.identity
    except AttributeError:
        raise AttributeError(
            f"the box {box.name!r} carries no identity: every box of a constructed stage is named "
            f"by one (AMD-SG-016 §3), and a box built outside the package is not read here"
        ) from None
