"""The declaration pass of the construction: every top-level item and every
block header of one stage file, read in textual order, checked, and held as
the working records the construction of the builder boxes and the typing walk
read.

`make_stage` calls the pass in ten steps, which stand below in that order
after `__init__`, which makes the records: the file is read (`read`); the
identities are checked for collisions and the names for the rules of the
language (`check_identity_collisions`, `check_names`); the fields and the
block signatures are derived (`fields_and_header_sides`); the distributions,
the definitions and the branches are checked (`check_distributions`,
`resolve_definitions`, `check_branches`); the forms the package does not
construct are refused (`refuse_unconstructed`); the statements of every block
are checked (`check_statements`); and, after the typing call, the annotation
the working stage keeps is written (`declarations_record`). The methods each
of the nine checks calls stand after it; the lookups the construction and the
walk read stand after the ninth check, and the tenth step stands last. A
declaration or statement that breaks a construction rule raises a
`ConstructionError` where it is met, carrying the rule and the position of the
item.
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from bellman.distributions.edges import DistributionDeclaration, dependency_order, shock_builders
from bellman.distributions.families import label_weights
from bellman.native.identity import (
    COLLISION_RULE,
    Identity,
    IdentityCollision,
    refuse_colliding_name,
)
from bellman.refusals import ConstructionError, NotConstructed, construction_error
from bellman.syntax import terms
from bellman.syntax.source import to_source
from bellman.syntax.walk import nodes
from bellman.syntax.vocabulary import (
    ARRIVAL,
    CONTINUATION,
    CONTROL,
    DECISION,
    DOC,
    MULTIPLIER,
    PERCH_OF_SIDE,
    PERCHES,
    PRIMITIVE_SETS,
    ROLE_WORD,
    SHCK,
    SHOCK,
    STATE,
    VALUE,
    VALUE_ROLES,
)
from bellman.typing import sets
from bellman.typing.line_unknowns import (
    BOUND_OPERATORS,
    derivative_left_side,
    INPUT,
    OPERATOR_MEANINGS,
    OPERATOR_VOCABULARY,
    OUTPUT,
    annotation_entries,
    bound_expressions,
    check_selections_and_calls,
    classifier_set,
    classifier_text,
    converse_bound,
    coordinate_text,
    expectations_over,
    field_spelling,
    forward_blocks_between,
    free_names,
    free_names_with_shocks,
    group_coordinates,
    is_number_alone,
    item_kind,
    listed_identity,
    named_sets,
    names_fields,
    occurrence_paths,
    outputs_and_unknowns,
    perch_of_spelling,
    position_text,
    role_word,
    selection_positions,
    selection_tuples,
    span_of,
    spelling_text,
    statement_id,
    subscript_binder,
    unreadable_form_refusal,
)

# --- the working records of the declaration pass ---

# These records exist during construction only.
# `Declarations.declarations_record` turns them into the plain mappings and
# tuples `freeze` copies onto the stage, and the construction of the builder
# boxes reads them to make the boxes.


@dataclasses.dataclass
class _HeaderEntry:
    """One entry of a block's header as written, with the field's identity
    once perches are known: the field `stem`; its mark, the perch word its
    bracket names (`arvl` for `[<]`, `dcsn` for `[~]`, `cntn` for `[>]`) and
    None where the field is bare; its own perch word if it carries one; its
    role word and printed set if it carries them; where it stands; and its
    wire type."""

    stem: str
    mark: str | None
    own_perch: str | None
    role: str | None
    domain: str | None
    domain_term: object
    block_id: str
    side: str
    side_perch: str | None  # the perch word written on the side, None when omitted
    address: str
    text: str  # the coordinate as written, `V[>]`, for messages
    wire_type: Identity | None = None


@dataclasses.dataclass(frozen=True)
class _Multiplier:
    """One multiplier a block body declares with its clause, `μ[>] : ℝ₊ ⟂ a
    >= 0`: the name `stem`, the block that declares it, the address of the
    declaration, its printed and its retained declared set, and the bound
    after ⟂ as written."""

    stem: str
    block: str
    address: str
    domain: str
    domain_term: object
    bound: object


class _TopLevelDeclaration(NamedTuple):
    """One name a top-level declaration declares: its printed set, its role
    word, the address of the declaration and the set term it is declared
    with, each None where the declaration writes none."""

    domain: str | None
    role: str | None
    address: str
    domain_term: object


class _Classified(NamedTuple):
    """What the classifiers of one typed coordinate state: its role word,
    its printed set, its set term and its own perch word, each None where
    no classifier states it."""

    role: str | None
    domain: str | None
    domain_term: object
    perch: str | None


class _SidePerches(NamedTuple):
    """The perch words of a block's input side and its output side."""

    input: str | None
    output: str | None


class _Deferred(NamedTuple):
    """The refusal of an item the construction does not read, held until the
    declaration pass ends: the item's place in the file, its address, the
    rule and the message."""

    order: int
    address: str
    rule: str
    message: str


class _DistributionStatement(NamedTuple):
    """One distribution declaration: its distribution as printed and its
    address."""

    printed: str
    address: str


class _AuthoredLine(NamedTuple):
    """One line of a block: its address and its right side."""

    address: str
    rhs: object


@dataclasses.dataclass
class _Field:
    """One wire type: a field at a perch, or a shock at no perch."""

    stem: str
    perch: str
    sites: list  # (where, side) in textual order
    domain_terms: list  # the set terms behind the sites' printed domains


@dataclasses.dataclass
class _Definition:
    """One top-level definition before the annotation is made: a function in
    closed form (`FuncDef`), a correspondence with a set body (`CorrDef`), or
    an assignment whose value is an expression (`𝑑𝑢 := D_{c}(𝑢)`). `params`
    are (name, printed set) pairs; `body` the body term; `slot` the term
    field that holds the body (`body` or `value`), the first step of an
    occurrence's position; `references` the defined functions the body
    mentions, filled by `resolve_definitions`."""

    name: str
    params: tuple
    body: object
    printed: str
    slot: str
    address: str
    operators: tuple = ()
    references: tuple = ()
    domains: tuple = ()


# The kind a stage without branches carries; the other kind is "branching".
STANDARD = "standard"
# The symbol groups in the order the language's specification lists them.
# Every group is present on every stage, an undefined one as the empty tuple.
SYMBOL_GROUPS = (
    "spaces",
    "arvl_states",
    "dcsn_states",
    "cntn_states",
    "controls",
    "exogenous",
    "values",
    "parameters",
    "settings",
    "functions",
)
TOP_LEVEL = "top level"
# What a block's body holds, which the refusal of another form inside a block
# names beside that form.
_STANDARD_FORMS = (
    "a block's body holds its equations and inequalities, the multipliers it "
    "declares and, in a branching block, its labeled nested blocks"
)


# --- the declaration pass ---
# the nine checks in `make_stage`'s order, the lookups, the annotation


class Declarations:
    """The declaration pass over one file term: every top-level item and every
    block signature, in textual order, with the body lines of each block
    collected for the box construction; construction errors are raised as
    they are met, and the items this module does not construct are collected
    and refused after the pass."""

    # -- the records, made before the file is read --

    def __init__(self, stage: str, items, spans):
        self.stage = stage
        self.items = items
        self.spans = spans
        self.address_of = {id(item): address for address, item in items}
        self.order = {address: n for n, (address, _) in enumerate(items)}
        self.metadata = {}  # key -> (value, address)
        self.spaces = {}  # name -> the address of its definition
        self.space_terms = {}
        self.functions = {}  # name -> _Definition, in source order
        self.scalars = {}  # name -> _TopLevelDeclaration
        self.scalar_keys = {}  # name -> (item order, place in its declaration's subject)
        self.laws = {}  # subjects tuple -> _DistributionStatement
        self.law_of = {}  # shock name -> the address of its distribution declaration
        self.shocks = {}  # shock name -> (item order, place) of its first mention
        self.listings = []  # _HeaderEntry, in textual order
        self.blocks = []  # (block id, address)
        self.written_perches = {}  # block id -> (input perch word, output perch word), as written
        self.side_perches = {}  # block id -> the same, inferred where omitted
        self.bodies = {}  # block id -> [(ordinal, address, Statement)]
        self.branch_labels = {}  # block id -> the labels of its nested blocks, in source order
        self.branch_fields = {}  # (block id, label) -> the stems the nested block writes
        self.value_branches = {}  # the wire type of a branch value -> its branch's label
        self.multipliers = {}  # stem -> _Multiplier, in textual order
        self.deferred = []  # _Deferred, in the order the items are met
        self.definition_order = ()
        self.law_terms = []

    # -- 1. the file, read item by item --

    def read(self, term) -> None:
        for item in term.items:
            address = self.address_of[id(item)]
            if isinstance(item, terms.Metadata):
                self.read_metadata(item, address)
            elif isinstance(item, terms.Declare):
                self.read_declaration(item.declaration, address)
            elif isinstance(item, terms.Statement):
                self.read_statement(item, address)
            elif isinstance(item, terms.Block):
                self.read_block(item, address)
            else:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"no construction rule reads a {type(item).__name__} item; "
                        f"a stage file holds metadata lines, declarations, "
                        f"definitions, distribution declarations, and blocks"
                    ),
                )
        self.check_multipliers_unlisted()

    def check_multipliers_unlisted(self) -> None:
        """No header lists a multiplier: a multiplier a block body declares
        is a coordinate of its declaring block alone and is listed by no
        header. Every block is read before the check, so a header written
        after the declaration is refused as one written before it."""
        for listing in self.listings:
            multiplier = self.multipliers.get(listing.stem)
            if multiplier is None:
                continue
            body = (
                "the body of that block"
                if multiplier.block == listing.block_id
                else f"the body of block {multiplier.block!r}"
            )
            raise self.error(
                "multiplier-declaration",
                listing.address,
                (
                    f"the header of block {listing.block_id!r} lists {listing.text}, and "
                    f"{listing.stem!r} is declared as a multiplier in {body}, at "
                    f"{self.where(multiplier.address)}; a multiplier is a coordinate of its "
                    f"declaring block alone and is listed by no header (AMD-SG-035 D3). Remove "
                    f"{listing.text} from the header, or give the multiplier a name no field of "
                    f"the stage has"
                ),
            )

    def error(
        self, rule: str, address, message: str, error_class=ConstructionError
    ) -> ConstructionError:
        """The refusal of the item at `address`, carrying its position, its
        term address, and the rule it does not satisfy (`bellman.refusals`)."""
        return construction_error(
            message,
            stage=self.stage,
            address=address,
            span=span_of(address, self.spans),
            rule=rule,
            error_class=error_class,
        )

    def where(self, address: str) -> str:
        """The position of one item as a message names a *second* item: the
        position of the item a refusal is raised at is a field of the refusal
        itself and is not written into its sentence."""
        return position_text(address, self.spans)

    def read_metadata(self, item, address) -> None:
        if item.key == "stage":
            return
        if item.key in self.metadata:
            _, first = self.metadata[item.key]
            raise self.error(
                "declared-once",
                address,
                (
                    f"a second metadata line carries the key '@{item.key}'; the "
                    f"first is at {self.where(first)}. A key is written once: "
                    f"delete this line or give it another key"
                ),
            )
        self.metadata[item.key] = (item.value, address)

    def read_declaration(self, declaration, address) -> None:
        if isinstance(declaration, terms.Handler) or isinstance(declaration.subject, terms.Path):
            # a typing entry or a handler binding the union left at file
            # level, the component of a definition or of a stage-wide
            # operator, which the semantics reads (specification 0.7, unit U3)
            return
        if declaration.value is not None:
            names = ", ".join(coordinate_text(c) for c in declaration.subject.coordinates)
            raise self.error(
                "readable-form",
                address,
                (
                    f"the declaration of {names} carries a value; a stage file "
                    f"declares what a name is, not what it equals: calibration "
                    f"supplies the value, and the stage reads it through "
                    f"`.calibration`"
                ),
            )
        subject = declaration.subject
        if declaration.classifiers and len(subject.coordinates) != 1:
            subject = terms.Subject((terms.Group(subject, declaration.classifiers),))
        coordinates = tuple(group_coordinates(subject, self, address))
        for place, c in enumerate(coordinates):
            if not isinstance(c, terms.Coordinate):
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"this declaration nests a tuple inside its subject; no "
                        f"construction rule reads one. A declaration lists names, "
                        f"`(Ψ : ℝ₊₊, θ : ℝ₊₊)`"
                    ),
                )
            classifiers = list(c.classifiers) + (
                list(declaration.classifiers) if len(declaration.subject.coordinates) == 1 else []
            )
            if c.at is not None:
                raise self.error(
                    "field-perch",
                    address,
                    (
                        f"the top-level declaration of {coordinate_text(c)} "
                        f"carries a perch mark; a name is marked for a perch only "
                        f"where a block header lists it, since the block's side "
                        f"says which information set the field belongs to"
                    ),
                )
            role, domain, _, perch = self.classify(classifiers, c, address)
            if perch is not None:
                raise self.error(
                    "field-perch",
                    address,
                    (
                        f"the top-level declaration of {c.stem!r} carries a perch "
                        f"word; a name is placed at a perch only where a block "
                        f"header lists it"
                    ),
                )
            if c.stem in self.scalars:
                raise self.error(
                    "declared-once",
                    address,
                    (
                        f"{c.stem!r} is declared a second time; its first "
                        f"declaration is at {self.where(self.scalars[c.stem].address)}. "
                        f"A name is declared once"
                    ),
                )
            self.scalars[c.stem] = _TopLevelDeclaration(
                domain=domain, role=role, address=address, domain_term=classifier_set(classifiers)
            )
            self.scalar_keys[c.stem] = (self.order[address], place)
            if role == SHOCK:
                self.note_shock(c.stem, address, place)

    def classify(self, classifiers, coordinate, address, block_id=None):
        """The role word, printed domain, domain term, and own perch word of
        one typed coordinate."""
        role = domain = domain_term = perch = None
        place = f"block {block_id!r}" if block_id else "the top level"
        for cl in classifiers:
            if isinstance(cl, terms.Domain):
                if domain is not None:
                    raise self.error(
                        "readable-form",
                        address,
                        (
                            f"{coordinate_text(coordinate)} in {place} carries two "
                            f"sets; no construction rule reads their conjunction. "
                            f"Write the one set the field takes its values in"
                        ),
                    )
                domain, domain_term = to_source(cl.space), cl.space
            elif isinstance(cl, terms.Role):
                word = role_word(cl.kind)
                if word is None:
                    raise self.error(
                        "readable-form",
                        address,
                        (
                            f"{coordinate_text(coordinate)} in {place} carries the "
                            f"role {type(cl.kind).__name__}, which no construction "
                            f"rule reads; the roles are `!state`, `!ctrl`, `!vlu`, "
                            f"`!mrgnvl`, `!sndmrgnvl`, and `!shck`"
                        ),
                    )
                if role is not None and role != word:
                    raise self.error(
                        "one-name-one-meaning",
                        address,
                        (
                            f"{coordinate_text(coordinate)} in {place} carries two "
                            f"roles, {role!r} and {word!r}; a field has one role"
                        ),
                    )
                role = word
            elif isinstance(cl, terms.Infoset):
                perch = self.perch_token(
                    cl.side, address, f"{coordinate_text(coordinate)} in {place}"
                )
            else:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"no construction rule reads the classifier "
                        f"{type(cl).__name__} on {coordinate_text(coordinate)}; a "
                        f"listed field carries a set, a role word, and a perch "
                        f"word"
                    ),
                )
        return _Classified(role=role, domain=domain, domain_term=domain_term, perch=perch)

    def perch_token(self, side, address, what: str) -> str:
        """The token of a perch word or of a mark (`arvl`, `dcsn`, `cntn`).
        A term whose perch is another constructor names no perch of the
        stage; only a term decoded from a saved AST can carry one, since the
        grammar writes the three words and the three marks."""
        token = PERCH_OF_SIDE.get(type(side))
        if token is None:
            raise self.error(
                "field-perch",
                address,
                (
                    f"{what} names the perch {type(side).__name__}, which is no "
                    f"perch of a stage; the perches are arrival (`!arvl`, `[<]`), "
                    f"decision (`!dcsn`, `[~]`), and continuation (`!cntn`, "
                    f"`[>]`)"
                ),
            )
        return token

    def note_shock(self, name, address, place=0) -> None:
        """Records a shock at its first mention: the place is where it stands
        among the coordinates of its declaration or the subjects of its
        distribution, so that `exogenous` lists shocks in declaration order."""
        self.shocks.setdefault(name, (self.order[address], place))

    def read_statement(self, item, address) -> None:
        """A top-level statement: a space assignment, a definition (a
        function, a correspondence, or an assignment of an expression), or a
        distribution declaration."""
        core = item.core
        if isinstance(core, terms.Assignment):
            if not isinstance(core.target, terms.Constant):
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"this assignment has a {type(core.target).__name__} as "
                        f"its target; no construction rule reads one. An "
                        f"assignment names a space or a function on its left "
                        f"(`Xa := ℝ₊`, `𝑑𝑢 := D_{{c}}(𝑢)`)"
                    ),
                )
            if isinstance(core.value, terms.Space):
                self.read_space(core, address)
            else:
                self.read_definition(core.target.name, [], core.value, "value", address)
        elif isinstance(core, terms.FuncDef):
            self.read_definition(core.name, core.params, core.body, "body", address)
        elif isinstance(core, terms.CorrDef):
            self.read_definition(core.name, core.params, core.body, "body", address)
        elif isinstance(core, terms.Law):
            self.read_distribution(core, address)
        else:
            raise self.error(
                "readable-form",
                address,
                (
                    f"no construction rule reads a {item_kind(item)} at the top level; "
                    f"a top-level statement defines a space, a function, or a "
                    f"correspondence, or declares the distribution of a shock"
                ),
            )

    def read_space(self, assignment, address) -> None:
        name = assignment.target.name
        if name in self.spaces:
            raise self.error(
                "declared-once",
                address,
                (
                    f"the space {name!r} is defined a second time; the first "
                    f"definition is at {self.where(self.spaces[name])}. A "
                    f"space is defined once"
                ),
            )
        self.spaces[name] = address
        self.space_terms[name] = assignment.value.set

    def read_definition(self, name, params, body, slot, address) -> None:
        if name in self.functions:
            raise self.error(
                "declared-once",
                address,
                (
                    f"the function {name!r} is defined a second time; the first "
                    f"definition is at {self.where(self.functions[name].address)}. "
                    f"A function is defined once"
                ),
            )
        typed = []
        domain_terms = []
        for p in params:
            if not isinstance(p, terms.Coordinate) or p.at is not None:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"no construction rule reads the argument "
                        f"{coordinate_text(p)} of the function {name!r}; an "
                        f"argument is a bare name with its set, `𝑢(c : ℝ₊₊)`"
                    ),
                )
            domains = [c for c in p.classifiers if isinstance(c, terms.Domain)]
            if len(domains) != len(p.classifiers) or len(domains) > 1:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"no construction rule reads the typing of the argument "
                        f"{p.stem!r} of the function {name!r}; an argument carries "
                        f"one set and no role or perch word"
                    ),
                )
            if any(name == p.stem for name, _ in typed):
                raise self.error(
                    "declared-once", address, f"function {name!r} repeats parameter {p.stem!r}"
                )
            typed.append((p.stem, to_source(domains[0].space) if domains else None))
            domain_terms.append((p.stem, domains[0].space if domains else None))
        self.functions[name] = _Definition(
            name=name,
            params=tuple(typed),
            body=body,
            printed=to_source(body),
            slot=slot,
            address=address,
            domains=tuple(domain_terms),
        )

    def read_distribution(self, law, address) -> None:
        """A distribution declaration names its subjects as shocks and is
        recorded under them in the authored order; a shock has one
        distribution."""
        subjects = law.subjects
        if not subjects or not all(isinstance(s, str) for s in subjects):
            named = ", ".join(type(s).__name__ for s in subjects) or "no subject"
            raise self.error(
                "readable-form",
                address,
                (
                    f"this distribution declaration has {named} as its subject; no "
                    f"construction rule reads one. A distribution declaration names "
                    f"its shocks and their distribution, `y ~ LogNormal(μ_y, σ_y)`"
                ),
            )
        key = tuple(subjects)
        if key in self.laws:
            raise self.error(
                "declared-once",
                address,
                (
                    f"a second distribution is declared for {', '.join(subjects)}; the "
                    f"first is at {self.where(self.laws[key].address)}. A shock has one "
                    f"distribution"
                ),
            )
        for place, subject in enumerate(subjects):
            if subject in self.law_of:
                raise self.error(
                    "declared-once",
                    address,
                    (
                        f"{subject!r} is the subject of a second distribution "
                        f"declaration; its first is at {self.where(self.law_of[subject])}. "
                        f"A shock has one distribution"
                    ),
                )
            self.law_of[subject] = address
            self.note_shock(subject, address, place)
        self.laws[key] = _DistributionStatement(printed=to_source(law.law), address=address)
        self.law_terms.append((law.law, address))

    def read_block(self, block, address) -> None:
        block_id, signature = self.block_header(block, address)
        self.check_block_id(block_id, address)
        self.blocks.append((block_id, address))
        self.written_perches[block_id] = _SidePerches(
            input=self.read_side(
                signature.source, signature.source_types, block_id, INPUT, address
            ),
            output=self.read_side(
                signature.target, signature.target_types, block_id, OUTPUT, address
            ),
        )
        self.bodies[block_id] = []
        nested = [item for item in block.body if isinstance(item, terms.Block)]
        self.check_branch_form(block_id, nested, address)
        ordinal = 0
        for n, item in enumerate(block.body, 1):
            item_address = self.address_of[id(item)]
            if isinstance(item, terms.Block):
                ordinal = self.read_branch(block_id, item, item_address, ordinal)
            elif nested and isinstance(item, (terms.Statement, terms.Declare)):
                raise self.error(
                    "branch-form",
                    item_address,
                    (
                        f"this line stands in block {block_id!r} beside its nested blocks; a "
                        f"branching block holds its branches alone, so move the line into a branch"
                    ),
                )
            elif isinstance(item, terms.Statement):
                self.read_body_statement(block_id, n, item, item_address)
            elif isinstance(item, terms.Declare):
                # the multiplier of a bound
                self.read_multiplier(block_id, item, item_address)
            else:
                raise self.error(
                    "readable-form",
                    item_address,
                    (
                        f"no construction rule reads a {type(item).__name__} inside "
                        f"block {block_id!r}; the body of a block holds its "
                        f"statements"
                    ),
                )
        if len(nested) == 1:
            raise self.error(
                "branch-form",
                address,
                (
                    f"block {block_id!r} holds one nested block; a branching "
                    f"block holds at least two, one for each label of its label "
                    f"coordinate; write a nested block for each missing label"
                ),
            )

    def block_header(self, block, address) -> tuple:
        """The id and the signature a block's header writes, each written once:
        a header with no `id=` entry, with no signature or with two is refused
        under `readable-form`."""
        block_id = None
        signature = None
        for entry in block.tag.entries:
            if isinstance(entry, terms.KeyValue) and entry.key == "id":
                block_id = entry.value
            elif isinstance(entry, terms.Typer) and isinstance(entry.typing, terms.Signature):
                if signature is not None:
                    raise self.error(
                        "readable-form",
                        address,
                        (
                            "this block header carries two signatures; a block has "
                            "one, `(inputs) : !perch -> (outputs) : !perch`"
                        ),
                    )
                signature = entry.typing
        if not isinstance(block_id, str) or not block_id:
            raise self.error(
                "readable-form",
                address,
                (
                    "this block header has no `id=` entry; every block is named by "
                    "its id, `[id=policy, …]`, and a methods file names the block "
                    "by it (D06)"
                ),
            )
        if signature is None:
            raise self.error(
                "readable-form",
                address,
                (
                    f"the header of block {block_id!r} has no signature "
                    f"`(...) : !perch -> (...) : !perch`; a block declares the "
                    f"fields it reads and the fields it writes in its header (spec "
                    f"0.3c §3.2)"
                ),
            )
        return block_id, signature

    def check_block_id(self, block_id, address) -> None:
        """A block's id names one block. A block is read by its id as a key
        of the graph that holds it and never as an attribute, so an id may be
        any name the grammar admits, the name of a verb included."""
        earlier = next((a for b, a in self.blocks if b == block_id), None)
        if earlier is not None:
            raise self.error(
                "declared-once",
                address,
                (
                    f"two blocks carry the id {block_id!r}: the block at "
                    f"{self.where(earlier)} and this one. A methods file names a "
                    f"block by its id and a method must reach one block, so give "
                    f"each block its own id"
                ),
            )

    def check_branch_form(self, block_id, nested, address) -> None:
        """A block that holds nested blocks, its branches, reads its inputs at
        the decision perch and lists no field on its own output side."""
        if nested and self.written_perches[block_id].input != DECISION:
            raise self.error(
                "branch-form",
                self.address_of[id(nested[0])],
                (
                    f"this nested block stands in block {block_id!r}, whose "
                    f"input side is not at the decision perch; a branch stands "
                    f"in the forward block from the decision perch alone"
                ),
            )
        if nested and self.side_entries(block_id, OUTPUT):
            raise self.error(
                "branch-form",
                address,
                (
                    f"block {block_id!r} lists fields on its own output side beside its nested "
                    f"blocks; a branching block's own output side is empty, `-> ()`"
                ),
            )

    def read_side(self, subject, side_types, block_id, side, address) -> str | None:
        """Records the listings of one side and returns its written perch
        word, None when the side has none."""
        side_perch = None
        for t in side_types:
            if isinstance(t, terms.Infoset) and side_perch is None:
                side_perch = self.perch_token(
                    t.side, address, f"the {side} side of block {block_id!r}"
                )
            else:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"the {side} side of block {block_id!r} is typed by a "
                        f"{classifier_text(t)}; a side carries one perch word and "
                        f"nothing else (a set on a side is a joint constraint, "
                        f"which no construction rule reads)"
                    ),
                )
        for place, c in enumerate(group_coordinates(subject, self, address)):
            if not isinstance(c, terms.Coordinate):
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"the {side} side of block {block_id!r} nests a tuple; a "
                        f"side lists its fields, `(V[>] : ℝ @ !vlu, c)`"
                    ),
                )
            role, domain, domain_term, own_perch = self.classify(
                c.classifiers, c, address, block_id
            )
            mark = self.perch_of_mark(c.at, address, coordinate_text(c))
            self.listings.append(
                _HeaderEntry(
                    stem=c.stem,
                    mark=mark,
                    own_perch=own_perch,
                    role=role,
                    domain=domain,
                    domain_term=domain_term,
                    block_id=block_id,
                    side=side,
                    side_perch=side_perch,
                    address=address,
                    text=coordinate_text(c),
                )
            )
            if role == SHOCK:
                self.note_shock(c.stem, address, place)
        return side_perch

    def perch_of_mark(self, at, address, text: str) -> str | None:
        """The perch a coordinate's mark names: `[<]` arrival, `[~]` decision,
        `[>]` continuation; None for a bare name."""
        if at is None:
            return None
        if isinstance(at, terms.At):
            return self.perch_token(at.side, address, f"the mark on {text}")
        raise self.error(
            "readable-form",
            address,
            (
                f"no construction rule reads the index {type(at).__name__} on "
                f"{text}; a field is marked `[<]`, `[~]`, or `[>]`"
            ),
        )

    def side_entries(self, block_id: str, side: str) -> list:
        """The listings of one side of one block, in header order."""
        return [l for l in self.listings if l.block_id == block_id and l.side == side]

    def read_branch(self, block_id, block, address, ordinal) -> int:
        """One nested block of a branching block: its label, its outputs
        read as outputs of `block_id` at the continuation perch, its lines
        as lines of `block_id` at that label with the block's next ordinals;
        returns the last ordinal given."""
        entries = {e.key: e.value for e in block.tag.entries if isinstance(e, terms.KeyValue)}
        signature = next(
            (
                e.typing
                for e in block.tag.entries
                if isinstance(e, terms.Typer) and isinstance(e.typing, terms.Signature)
            ),
            None,
        )
        label = entries.get("label")
        if not isinstance(label, str) or "id" in entries or signature is None:
            raise self.error(
                "branch-form",
                address,
                (
                    f"this nested block of block {block_id!r} is not named by a `label=` entry "
                    f"alone; a branch is named by its label, "
                    f"`[label=keep, () -> (w : ℝ₊₊) : !cntn]`"
                ),
            )
        try:
            refuse_colliding_name(label, "branch label")
        except IdentityCollision as collision:
            raise self.error(COLLISION_RULE, address, collision.message) from None
        if label in self.branch_labels.get(block_id, ()):
            raise self.error(
                "branch-labels",
                address,
                (
                    f"block {block_id!r} holds two branches "
                    f"labeled {label!r}; a label names one branch"
                ),
            )
        if signature.source.coordinates or signature.source_types:
            raise self.error(
                "branch-form",
                address,
                (
                    f"the branch {label!r} lists fields on its input side; a branch reads its "
                    f"block's inputs, so its input side is empty, "
                    f"`[label={label}, () -> (…) : !cntn]`"
                ),
            )
        earlier = {
            listing.stem: listing.address for listing in self.side_entries(block_id, OUTPUT)
        }
        perch = self.read_side(signature.target, signature.target_types, block_id, OUTPUT, address)
        if perch != CONTINUATION or not signature.target.coordinates:
            raise self.error(
                "branch-form",
                address,
                (
                    f"the branch {label!r} writes no field at the continuation perch; its fields "
                    f"name its part of the continuation space, "
                    f"`[label={label}, () -> (w : ℝ₊) : !cntn]`"
                ),
            )
        for listing in self.side_entries(block_id, OUTPUT):
            if listing.address == address and listing.stem in earlier:
                first = earlier[listing.stem].split(".", 1)[1]
                raise self.error(
                    "declared-once",
                    address,
                    (
                        f"the field {listing.stem!r} is written by the branches "
                        f"{first!r} and {label!r}; each branch writes fields of "
                        f"its own, so rename one, `{listing.stem}_{label}`"
                    ),
                )
        self.branch_labels.setdefault(block_id, []).append(label)
        self.branch_fields[(block_id, label)] = tuple(
            listing.stem
            for listing in self.side_entries(block_id, OUTPUT)
            if listing.address == address
        )
        for item in block.body:
            item_address = self.address_of[id(item)]
            if not isinstance(item, terms.Statement):
                raise self.error(
                    "branch-form",
                    item_address,
                    (
                        f"the branch {label!r} holds a "
                        f"{type(item).__name__}; a branch holds lines alone"
                    ),
                )
            ordinal += 1
            self.read_body_statement(block_id, ordinal, item, item_address)
        return ordinal

    def read_body_statement(self, block_id, ordinal, item, address) -> None:
        """A body line is kept for the box construction when its core is an
        equation, with or without a slack clause; a function definition, a
        distribution declaration, or another statement form inside a block
        has no construction rule in this module."""
        core = item.core
        if isinstance(core, terms.Slack):
            if not isinstance(core.core, (terms.Equation, terms.Inequality)):
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"this slack clause follows a {type(core.core).__name__}; "
                        f"the clause `⟂ a >= 0` is written after an equality or an inequality "
                        f"(grammar rule `statement`)"
                    ),
                )
            core = core.core
        if isinstance(core, (terms.Equation, terms.Inequality)):
            # An inequality statement is kept like an equation: the box
            # it defines is the same operation, and the statement term carried
            # by the record keeps the relation.
            self.bodies[block_id].append((ordinal, address, item))
        else:
            described = {
                terms.FuncDef: "a function definition",
                terms.CorrDef: "a correspondence definition",
                terms.Law: "a distribution declaration",
                terms.Assignment: "an assignment",
            }.get(type(core), f"a {type(core).__name__} statement")
            self.defer(
                address,
                "not-constructed",
                (
                    f"{described} inside block {block_id!r} is a form the construction does "
                    f"not read: {_STANDARD_FORMS}. Write {described} at the top level of the "
                    f"file"
                ),
            )

    def defer(self, address, rule, message) -> None:
        """Collects the refusal of an item this module does not construct;
        the textually first is raised after the declaration pass."""
        self.deferred.append(
            _Deferred(order=self.order[address], address=address, rule=rule, message=message)
        )

    def read_multiplier(self, block_id, item, address) -> None:
        """A declaration in a block body, the multiplier of a bound: one
        coordinate marked `[>]`, one declared set and no role word, one
        bound of one relation written with the bounded quantity first;
        registered once, in `multipliers` and not in `bodies`, whose readers
        read a statement's core. The bound's names are checked in
        `check_block`, where every block's roles are known."""
        typer = item.declaration
        if not isinstance(typer, terms.Complementary):
            raise self.error(
                "readable-form",
                address,
                (
                    f"no construction rule reads a {type(typer).__name__} inside block "
                    f"{block_id!r}; a declaration in a block body declares the multiplier of "
                    f"a bound with its clause, `μ[>] : ℝ₊ ⟂ a >= 0`"
                ),
            )
        declaration, bound = typer.declaration, typer.bound
        coordinates = (
            declaration.subject.coordinates
            if isinstance(declaration, terms.Declaration) and declaration.value is None
            else ()
        )
        if len(coordinates) != 1 or not isinstance(coordinates[0], terms.Coordinate):
            raise self.error(
                "multiplier-declaration",
                address,
                (
                    f"the declaration in block {block_id!r} does not declare one name: a "
                    f"multiplier belongs to one bound, and a declaration in a block body "
                    f"declares one, `μ[>] : ℝ₊ ⟂ a >= 0`. Write one declaration for each "
                    f"multiplier"
                ),
            )
        stem, at = coordinates[0].stem, coordinates[0].at
        if not (
            isinstance(at, terms.At)
            and self.perch_token(at.side, address, f"the mark on {stem!r}") == CONTINUATION
        ):
            written = coordinate_text(coordinates[0])
            raise self.error(
                "multiplier-declaration",
                address,
                (
                    f"the declaration in block {block_id!r} writes {written}, which is not "
                    f"marked `[>]`; a multiplier is a coordinate of the continuation perch of "
                    f"the functions its block defines (AMD-SG-035 D3). Write `{stem}[>]`"
                ),
            )
        domains = [c for c in declaration.classifiers if isinstance(c, terms.Domain)]
        if len(domains) != 1 or len(declaration.classifiers) != 1 or coordinates[0].classifiers:
            raise self.error(
                "multiplier-declaration",
                address,
                (
                    f"the declaration of {stem}[>] in block {block_id!r} is not typed by one "
                    f"set alone; a multiplier is typed by one declared set and carries no role "
                    f"or perch word, `{stem}[>] : ℝ₊ ⟂ a >= 0`"
                ),
            )
        if isinstance(bound, terms.Between):
            raise self.error(
                "multiplier-declaration",
                address,
                (
                    f"the clause of {stem}[>] carries two bounds, `{to_source(bound)}`; a "
                    f"declared multiplier belongs to one bound (AMD-SG-035 §4). Write one "
                    f"declaration for each bound, each with its own multiplier"
                ),
            )
        if is_number_alone(bound.left):
            raise self.error(
                "readable-form",
                address,
                (
                    f"the clause of {stem}[>] writes `⟂ {to_source(bound)}`, a number or `inf` "
                    f"alone before its relation sign; a one-bound clause is written with the "
                    f"bounded quantity first, on a declaration as on a line, since the slack and "
                    f"the sign of a clause are read from the relation as written (AMD-SG-035 §2, "
                    f"E33, E37). Write `⟂ {to_source(converse_bound(bound))}`"
                ),
            )
        if stem in self.multipliers:
            raise self.error(
                "multiplier-declaration",
                address,
                (
                    f"the multiplier {stem!r} is declared a second time; its first "
                    f"declaration is at {self.where(self.multipliers[stem].address)}. A "
                    f"multiplier is declared once: delete this line, or give the second bound "
                    f"a multiplier of its own name"
                ),
            )
        self.multipliers[stem] = _Multiplier(
            stem=stem,
            block=block_id,
            address=address,
            domain=to_source(domains[0].space),
            domain_term=classifier_set([domains[0]]),
            bound=bound,
        )

    # -- 2. the identities --

    def check_identity_collisions(self) -> None:
        """No authored name collides with the spelling of an identity: a name
        containing the colon that separates the segments of a spelling, or a
        name equal to one of the words a reader tests for in the last segment —
        `result`, `declared`, `merged`. The check stands here, before the first
        identity is built, so that the refusal names the authored item and its
        position rather than the identity the constructor was about to build.

        It also refuses the one ambiguity the constructor cannot see. The
        subjects of a distribution, of an extended measure and of the
        measure they extend are spelled joined by `_`, a separator a shock
        name may contain, so two declarations whose subjects join alike
        would spell one identity. Here both declarations have been read, and
        the second is refused."""
        written = [(self.stage, "stage name", self.stage_line_address())]
        written += [(block_id, "block id", address) for block_id, address in self.blocks]
        written += [
            (address.split(".", 1)[1], "statement id", address)
            for address in self.order
            if "." in address and address.split(".", 1)[0] in dict(self.blocks)
        ]
        written += [(listing.stem, "field", listing.address) for listing in self.listings]
        written += [
            (name, "name declared at the top level", declared.address)
            for name, declared in self.scalars.items()
        ]
        written += [
            (name, "function", definition.address) for name, definition in self.functions.items()
        ]
        written += [(name, "named space", address) for name, address in self.spaces.items()]
        for name, what, address in written:
            try:
                refuse_colliding_name(name, what)
            except IdentityCollision as collision:
                raise self.error(collision.rule, address, collision.message) from None
        joined = {}
        for subjects, declaration in self.laws.items():
            spelling = "_".join(subjects)
            first = joined.setdefault(spelling, tuple(subjects))
            if first != tuple(subjects):
                raise self.error(
                    COLLISION_RULE,
                    declaration.address,
                    (
                        f"the subjects {', '.join(subjects)} of this declaration are "
                        f"spelled {spelling!r} joined, as the subjects {', '.join(first)} "
                        f"of an earlier one are; the subjects of a distribution are "
                        f"joined by '_' in its identity, so the two declarations would "
                        f"carry one identity. Rename a subject of one of them"
                    ),
                )

    def stage_line_address(self):
        """The address of the file's `@stage` line, where a refusal of the
        stage's own name is placed."""
        return next(
            (
                address
                for address, item in self.items
                if isinstance(item, terms.Metadata) and item.key == "stage"
            ),
            None,
        )

    # -- 3. the names --

    def check_names(self) -> None:
        """One name has one meaning in a stage: a field, a function, a named
        space, a shock, or a parameter; and no function and no field takes a
        numerical operator's name.

        What a top-level scalar declaration is, and where the two readings
        conflict. A top-level declaration whose name a block header lists is
        that field's declaration site: it gives the field's set where the
        header lists it bare (`k : ℝ₊₊` above `[id=b, (k) : !arvl → …]`),
        and the name is a field, not a parameter. A shock is written this
        way too, with its distribution beside it (`y` in
        cons_savings_iid.bl, `Ψ` and `θ` in port.bl). A top-level
        declaration whose name no block header lists is a parameter, a
        number that calibration binds. The conflict is a declaration that
        says "field" while no block header lists the name: a role word
        (`!ctrl`, `!vlu`, `!mrgnvl`) belongs to a field, and a field is a
        name a block reads or writes, so the file must either list the name
        on a side or drop the role word and leave it a parameter (`roles`,
        below). One ambiguity remains: a shock declared without its
        distribution and listed nowhere is read as a parameter, and no check
        can tell the two apart."""
        first_listing = {}
        for listing in self.listings:
            first_listing.setdefault(listing.stem, listing.address)
        for name, address in first_listing.items():
            self.check_one_meaning(
                name, address, "a field, first listed here", ("function", "named space")
            )
            self.check_operator_name(name, address, "field", "first listed here")
        for name, definition in self.functions.items():
            self.check_one_meaning(
                name, definition.address, "a function, defined here", ("named space",)
            )
            self.check_operator_name(name, definition.address, "function", "defined here")
        for name, declaration in self.scalars.items():
            if name in first_listing:
                continue  # a field's top-level declaration
            for kind in ("function", "named space"):
                defined_at = self.definition_address(name, kind)
                if defined_at is not None:
                    raise self.error(
                        "one-name-one-meaning",
                        declaration.address,
                        (
                            f"{name!r} is declared as a scalar here and defined as a "
                            f"{kind} at {self.where(defined_at)}; a name has one "
                            f"meaning in a stage"
                        ),
                    )
        for name in self.shocks:
            self.check_one_meaning(
                name,
                self.shock_address(name),
                "a shock, first written here",
                ("function", "named space"),
            )

    def check_set_names(self) -> None:
        """Every set a typing names is a named set the stage defines or a set
        of the language: the set of a top-level declaration, `n_m : Foo`, of
        a header coordinate, `c : Foo`, of a function's argument,
        `𝑑𝑢(c : Foo)`, of a multiplier, `μ[>] : Foo`, and a set the definition
        of a named set reads, `Xq := Xm × Foo`. A name that is neither is
        refused under `name-in-scope` with the sets in scope, as a bare name
        a line mentions is (F35 of the case studies of specification 0.7); a
        function or a correspondence of the stage written where a set stands,
        `n_m : 𝑑𝑢`, is refused under the same rule naming it. A set the stage
        defines may be defined after the typing that names it. An assignment
        whose right side is no function of the stage, `XH := linspace(H_min,
        H_max, n_H)`, is refused by the typing walk under `not-constructed`,
        and a typing that names it is left to that refusal."""
        sites = [
            (declaration.domain_term, declaration.address, f"the declaration of {name!r}")
            for name, declaration in self.scalars.items()
        ]
        sites.extend(
            (
                listing.domain_term,
                listing.address,
                f"the header of block {listing.block_id!r}, which types {listing.text}",
            )
            for listing in self.listings
        )
        sites.extend(
            (term, definition.address, f"the argument {stem!r} of the function {definition.name!r}")
            for definition in self.functions.values()
            for stem, term in definition.domains
        )
        sites.extend(
            (self.space_terms[name], address, f"the definition of the set {name!r}")
            for name, address in self.spaces.items()
        )
        sites.extend(
            (
                multiplier.domain_term,
                multiplier.address,
                f"the declaration of the multiplier {multiplier.stem!r}",
            )
            for multiplier in self.multipliers.values()
        )
        for term, address, what in sites:
            for name in named_sets(term):
                if name in self.spaces or name in PRIMITIVE_SETS:
                    continue
                definition = self.functions.get(name)
                if definition is not None and not self.defines_a_function(definition):
                    continue
                if definition is not None:
                    correspondence = isinstance(definition.body, terms.setexpr)
                    kind = "correspondence" if correspondence else "function"
                    raise self.error(
                        "name-in-scope",
                        address,
                        (
                            f"{what} names the set {name!r}, which the stage defines as a "
                            f"{kind} at {self.where(definition.address)} and as no set; a "
                            f"typing names a set. Write one of the sets in scope here: "
                            f"{self.sets_in_scope_text()}"
                        ),
                    )
                raise self.error(
                    "name-in-scope",
                    address,
                    (
                        f"{what} names the set {name!r}, which the stage does not define: it is "
                        f"no named set of the stage and no set of the language. Define it, "
                        f"`{name} := …`, or write one of the sets in scope here: "
                        f"{self.sets_in_scope_text()}"
                    ),
                )

    def defines_a_function(self, definition) -> bool:
        """Whether the typing walk reads `definition` as a function or a
        correspondence: a definition with a parameter list, `𝑑𝑢(c : ℝ₊₊) :=
        c^(-ρ)`, or an assignment whose right side is the derivative of a
        function, `𝑑𝑢 := D_{c}(𝑢)`, the inverse of a function, `𝑑𝑢𝑖𝑛𝑣 :=
        Inv(𝑑𝑢)`, or the name of a function of the stage. An assignment
        whose right side is any other expression, `XH := linspace(H_min,
        H_max, n_H)` or `Xa := (0, ā)`, is refused by the typing walk under
        `not-constructed` (F5 of the case studies of specification 0.7)."""
        if definition.slot != "value":
            return True
        body = definition.body
        if isinstance(body, terms.Operator):
            return body.head == "D"
        if isinstance(body, terms.Call):
            return body.fun == "Inv"
        return (
            isinstance(body, terms.Sym)
            and isinstance(body.symbol, terms.Constant)
            and body.symbol.name in self.functions
        )

    def sets_in_scope_text(self) -> str:
        """The sets a typing may name, for a refusal: the named sets the stage
        defines, in definition order, then the sets of the language, each by
        its glyph once."""
        names = list(self.spaces)
        for primitive in PRIMITIVE_SETS.values():
            if primitive.glyph not in names:
                names.append(primitive.glyph)
        return ", ".join(names)

    def check_one_meaning(self, name, address, meaning, kinds) -> None:
        """Refuse `name`, which has `meaning` at `address`, where it is also
        a function or a named space, the first of `kinds` it is."""
        for kind in kinds:
            defined_at = self.definition_address(name, kind)
            if defined_at is not None:
                raise self.error(
                    "one-name-one-meaning",
                    address,
                    (
                        f"{name!r} is {meaning}, and a {kind}, defined at "
                        f"{self.where(defined_at)}; a name has one meaning in a stage"
                    ),
                )

    def definition_address(self, name, kind) -> str | None:
        """The address of the definition of `name` as a function or as a
        named space, as `kind` says; None where it has no such definition."""
        if kind == "function":
            return self.functions[name].address if name in self.functions else None
        return self.spaces[name] if name in self.spaces else None

    def check_operator_name(self, name, address, kind, placed) -> None:
        """Refuse a field or a function, as `kind` says, that takes the name
        of an operator a methods file names."""
        if name in OPERATOR_VOCABULARY:
            raise self.error(
                "one-name-one-meaning",
                address,
                (
                    f"the {kind} {name!r}, {placed}, has the name of "
                    f"the operator {name} ({OPERATOR_MEANINGS[name]}); a "
                    f"methods file names that operator by it, so no {kind} may "
                    f"take it. Rename the {kind}"
                ),
            )

    def shock_address(self, name: str) -> str:
        """The address of a shock's distribution declaration, else of its
        first declaration or listing."""
        if name in self.law_of:
            return self.law_of[name]
        if name in self.scalars and self.scalars[name].role == SHOCK:
            return self.scalars[name].address
        for listing in self.listings:
            if listing.stem == name and listing.role == SHOCK:
                return listing.address
        raise KeyError(name)

    # -- 4. the fields and the block signatures --

    def fields_and_header_sides(self):
        """The fields table (wire type -> _Field) in first-listing order and
        each block's two side products of wire-type names; each listing
        receives its wire type, and each side without a perch word its
        inferred perch."""
        roles = self.roles()
        # the roles stand on the record from here: the check of a state listed
        # on a backward header reads them before any perch is placed
        self.field_roles = roles
        fields = {}
        sides = {block_id: ([], []) for block_id, _ in self.blocks}
        for listing in self.listings:
            self.check_header_coordinate(listing)
            perch = self.perch_of(listing, roles)
            if perch is None:
                raise self.error(
                    "field-perch",
                    listing.address,
                    (
                        f"the field {listing.text} on the {listing.side} side of "
                        f"block {listing.block_id!r} is listed on a side without a "
                        f"perch word and nothing places it: it carries no perch "
                        f"mark, is not a control, and is not a shock. Write the "
                        f"side's perch word after the parenthesis (`: !arvl`, "
                        f"`: !dcsn`, or `: !cntn`) or mark the field"
                    ),
                )
            wire_type = Identity("field", stage=self.stage, perch=perch, field=listing.stem)
            listing.wire_type = wire_type
            field = fields.setdefault(
                wire_type, _Field(stem=listing.stem, perch=perch, sites=[], domain_terms=[])
            )
            product = sides[listing.block_id][0 if listing.side == INPUT else 1]
            if wire_type in product:
                raise self.error(
                    "declared-once",
                    listing.address,
                    (
                        f"the field {listing.text} is listed twice on the "
                        f"{listing.side} side of block {listing.block_id!r}: two "
                        f"coordinates of one side are the one field "
                        f"{wire_type!r}. List it once"
                    ),
                )
            product.append(wire_type)
            # A listing that carries a set or a role word is a declaration
            # site of its field; a bare listing is not.
            if listing.domain is not None or listing.role is not None:
                field.sites.append((listing.block_id, listing.side))
                field.domain_terms.append(listing.domain_term)
        for stem, multiplier in self.multipliers.items():
            # a multiplier is a field of the continuation perch no side lists:
            # in the fields table and in no side product, so no wire
            wire_type = Identity("field", stage=self.stage, perch=CONTINUATION, field=stem)
            fields.setdefault(
                wire_type,
                _Field(
                    stem=stem,
                    perch=CONTINUATION,
                    sites=[(multiplier.block, None)],
                    domain_terms=[multiplier.domain_term],
                ),
            )
        for stem, declaration in self.scalars.items():
            for field in fields.values():
                if field.stem == stem and (
                    declaration.domain is not None or declaration.role is not None
                ):
                    field.sites.append((TOP_LEVEL, None))
                    field.domain_terms.append(declaration.domain_term)
        signatures = {
            block_id: (tuple(inputs), tuple(outputs))
            for block_id, (inputs, outputs) in sides.items()
        }
        self.field_roles = roles
        self.side_perches = {
            block_id: _SidePerches(
                input=self.side_perch(block_id, INPUT), output=self.side_perch(block_id, OUTPUT)
            )
            for block_id, _ in self.blocks
        }
        return fields, signatures

    def check_one_builder_per_output(self) -> None:
        """One block writes a field between two perches: a second block whose
        sides join the same perches and whose output side lists a field the
        first writes is the same builder written twice, and is refused under
        `one-builder-per-output` naming both blocks (F17 of the case studies
        of specification 0.7). Read after the perches of the sides are placed.
        Two blocks between the same perches that write different fields are
        the question of `forward-composite`."""
        writers = {}  # (input perch, output perch, field) -> the block that writes it
        for block_id, address in self.blocks:
            perch_in, perch_out = self.side_perches[block_id]
            for listing in self.side_entries(block_id, OUTPUT):
                first = writers.setdefault((perch_in, perch_out, listing.stem), block_id)
                if first == block_id:
                    continue
                raise self.error(
                    "one-builder-per-output",
                    address,
                    (
                        f"block {block_id!r} writes {listing.stem} at the {perch_out} perch from "
                        f"the {perch_in} perch, which block {first!r} already writes; one builder "
                        f"writes a field between two perches (rule one-builder-per-output). Write "
                        f"the lines of the two blocks in one block, or make block {block_id!r} "
                        f"write another field"
                    ),
                )

    def check_header_coordinate(self, listing) -> None:
        """A backward block's header lists the value fields it reads and
        writes and the controls at which its lines are read, and no state
        (AAS, 12 October 2026, extending the policy block's rule of AMD-SG-017
        §2 to every backward block). A state listed on the input side of a
        backward block is refused under `header-coordinate` before `perch_of`
        places it, so that a listing without a perch word meets this rule and
        not `field-perch`. The refusal names the field, the perch its
        declaration on a forward block gives it, and the header without the
        listing: a state of the perch at which the block's output stands is a
        coordinate of the output function, so its listing would assert a wire
        of state sort that the backward builder does not have; a state of the
        block's input perch is reached through the law of motion alone; a
        state of any other perch is at no perch the block stands at or reads
        from. A listed state is refused and not read with the state removed,
        since the written header would then no longer determine the kind of
        operator the block denotes (Appendix C R1)."""
        if self.field_roles.get(listing.stem) != STATE:
            return
        block_id = listing.block_id
        if not self.block_is_backward(block_id):
            return
        actual = self.state_perch(listing)
        perch_in, perch_out = self.backward_perches(block_id)
        header = self.header_without(block_id, (listing.stem, listing.mark), listing.side)
        if listing.side == OUTPUT:
            raise self.error(
                "header-coordinate",
                listing.address,
                (
                    f"the header of backward block {block_id!r} lists {listing.text} on its "
                    f"output side, but a backward block writes value fields or controls, not "
                    f"a state; {listing.text} is a state of the {actual or 'unplaced'} perch. "
                    f"Remove the state output, `{header}`"
                ),
            )
        if actual is not None and actual == perch_out:
            reason = (
                f"{listing.text} is a state of the {actual} perch, the perch at which the "
                f"block's output stands, so it is a coordinate of the output function and "
                f"no input of the block"
            )
        elif actual is not None and actual == perch_in:
            reason = (
                f"{listing.text} is a state of the {actual} perch, the perch the block reads "
                f"its value fields at, and a backward block reaches a state of its input "
                f"perch through the forward law of motion alone"
            )
        elif actual is not None:
            reason = (
                f"{listing.text} is a state of the {actual} perch, a perch the block neither "
                f"stands at nor reads from"
            )
        else:
            reason = (
                f"{listing.text} is a state whose perch the listing does not determine, the "
                f"stem standing at more than one perch or at none"
            )
        raise self.error(
            "header-coordinate",
            listing.address,
            (
                f"the header of block {block_id!r} lists {listing.text} on its input side, "
                f"and the block is a backward block, whose header lists the value fields it "
                f"reads and writes and the controls at which its lines are read, and no "
                f"state (rule header-coordinate). {reason}. Remove the listing, "
                f"`{header}`; a line of the block may still mention a state of the "
                f"{perch_out or 'output'} perch, which is a coordinate of what it defines"
            ),
        )

    def block_is_backward(self, block_id: str) -> bool:
        """Whether a block is a backward block, `cntn_to_dcsn`, `dcsn_to_arvl`
        or a policy block. A backward direction identifies one even if its
        output side incorrectly mixes a state with value fields or controls;
        an output value field or control identifies one when the input header
        gives no perch. The header check refuses the mixed state output
        (AAS, 12 October 2026)."""
        outputs = self.side_entries(block_id, OUTPUT)
        perch_in, perch_out = self.backward_perches(block_id)
        return bool(outputs) and (
            (perch_in in PERCHES and perch_out in PERCHES and _precedes(perch_out, perch_in))
            or any(
                self.field_roles.get(l.stem) in VALUE_ROLES
                or self.field_roles.get(l.stem) == CONTROL
                for l in outputs
            )
        )

    def backward_perches(self, block_id: str) -> tuple:
        """The input perch and the output perch of a backward block as its
        header writes them: a side's perch word; else the perch a mark on a
        value field of the side names; else, for an output side of controls
        alone, the decision perch; None where the side determines none. Read
        before the perches of the listings are placed, so it reads no wire
        type."""
        written = self.written_perches[block_id]

        def side(entries, word):
            if word is not None:
                return word
            marks = {
                l.mark
                for l in entries
                if l.mark is not None and self.field_roles.get(l.stem) in VALUE_ROLES
            }
            if len(marks) == 1:
                return next(iter(marks))
            if entries and all(self.field_roles.get(l.stem) == CONTROL for l in entries):
                return DECISION
            return None

        return (
            side(self.side_entries(block_id, INPUT), written.input),
            side(self.side_entries(block_id, OUTPUT), written.output),
        )

    def state_perch(self, listing) -> str | None:
        """The perch a state's declaration gives it: the perch at which a
        forward block's side places the stem, read from the listing's wire
        type where that is placed and from its own words otherwise. A stem
        placed at two perches, `a` at arrival and `a[>]` at continuation in
        `disc.bl`, is one of two fields, and the listing's own mark, perch
        word or side word says which; a listing that names a perch where no
        forward block places the stem is read by that perch; None where
        nothing places the stem and the listing names no perch, or where two
        perches place it and the listing names neither."""
        placed = []
        for other in self.listings:
            if other.stem != listing.stem or other is listing:
                continue
            if self.block_is_backward(other.block_id):
                continue
            if other.wire_type is not None:
                perch = other.wire_type.perch
            else:
                try:
                    perch = self.perch_of(other, self.field_roles)
                except ConstructionError:
                    continue
            if perch is not None and perch not in placed:
                placed.append(perch)
        own = listing.mark or listing.own_perch or listing.side_perch
        if own is not None and (own in placed or not placed):
            return own
        if len(placed) == 1:
            return placed[0]
        return None

    def roles(self) -> dict:
        """The role of every field name: the word of its role classifier,
        every occurrence of which must agree (a field has one role in a
        stage), "shock" for the subject of a distribution declaration, or
        "state" for a field that carries no role word. A top-level declaration
        of a field contributes its role word too, and a multiplier a block body
        declares has the role "multiplier"."""
        roles = {}
        for listing in self.listings:
            if listing.role is not None:
                self.note_role(roles, listing.stem, listing.role, listing.address)
        for stem, multiplier in self.multipliers.items():
            self.note_role(roles, stem, MULTIPLIER, multiplier.address)
        field_names = set(self.field_names())
        for stem, declaration in self.scalars.items():
            role, address = declaration.role, declaration.address
            if role is not None:
                if stem not in field_names and role != SHOCK:
                    raise self.error(
                        "parameter-or-field",
                        address,
                        (
                            f"the top-level declaration of {stem!r} carries the "
                            f"role word for {role!r}, but no block header lists "
                            f"{stem!r}: a role belongs to a field, and a field is "
                            f"a name a block reads or writes, while a top-level "
                            f"declaration that no header lists is a parameter, a "
                            f"number calibration binds. List {stem!r} on a "
                            f"side of the block that uses it, or drop the role "
                            f"word and leave it a parameter"
                        ),
                    )
                self.note_role(roles, stem, role, address)
        for name, address in self.law_of.items():
            self.note_role(roles, name, SHOCK, address)
        first_roles = {stem: first_role for stem, (first_role, _) in roles.items()}
        return {stem: first_roles.get(stem, STATE) for stem in self.field_names()}

    def note_role(self, roles, stem, role, address) -> None:
        first_role, first_address = roles.get(stem, (role, address))
        if first_role != role:
            raise self.error(
                "one-name-one-meaning",
                address,
                (
                    f"the field {stem!r} is listed with two roles: {role!r} here "
                    f"and {first_role!r} at {self.where(first_address)}; a field "
                    f"has one role in a stage"
                ),
            )
        roles.setdefault(stem, (role, address))

    def field_names(self) -> list:
        """The field names in the order of their first listing, then the
        multipliers the block bodies declare, which no side lists."""
        out = []
        for listing in self.listings:
            if listing.stem not in out:
                out.append(listing.stem)
        for stem in self.multipliers:
            if stem not in out:
                out.append(stem)
        return out

    def perch_of(self, listing, roles) -> str | None:
        """The perch of one listing: a shock is at no perch (its token is
        `shck`); a control is at the decision perch wherever a header lists
        it, so a perch word on a control's own listing places nothing and is
        admitted in two cases alone — where it names the decision perch, on
        any side whatever word the side carries, which is the one case in
        which a mark need not agree with its side's perch word, and where it
        names a perch of its side. Any other perch word on a control is
        refused under `field-perch`, and so is a perch mark on a control
        that names any perch but the decision perch, since a mark names the
        field at the perch it marks and a control has no field at another
        perch. For every other coordinate a mark or the coordinate's own
        perch word places it, and must agree with the side's perch word;
        otherwise the side's perch word does; None when the side has no
        perch word and nothing places the coordinate."""
        if roles.get(listing.stem) == SHOCK:
            return self.shock_perch(listing)
        explicit = self.explicit_perch(listing)
        if roles.get(listing.stem) == CONTROL:
            return self.control_perch(listing, explicit, roles)
        if explicit is not None:
            if listing.side_perch is not None and listing.side_perch != explicit:
                raise self.error(
                    "field-perch",
                    listing.address,
                    (
                        f"the mark on {listing.text} places the field at the "
                        f"{explicit} perch, but the {listing.side} side of block "
                        f"{listing.block_id!r} is marked `: !{listing.side_perch}`; "
                        f"a mark agrees with its side's perch word (D06)"
                    ),
                )
            return explicit
        return listing.side_perch

    def shock_perch(self, listing) -> str:
        """The token `shck` of a shock, which is listed bare: a shock placed at
        a perch by a mark or a perch word is refused under `field-perch`."""
        if listing.mark is not None or listing.own_perch is not None:
            placed = listing.mark or listing.own_perch
            raise self.error(
                "field-perch",
                listing.address,
                (
                    f"{listing.text} on the {listing.side} side of block "
                    f"{listing.block_id!r} is a shock placed at the {placed} "
                    f"perch by its {'mark' if listing.mark else 'perch word'}; "
                    f"a shock is drawn on the edge between two perches and "
                    f"belongs to no perch, so list it bare"
                ),
            )
        return SHCK

    def explicit_perch(self, listing) -> str | None:
        """The perch a listing's mark or its own perch word names, None where
        it carries neither; a mark and a word that name two perches are
        refused under `field-perch`."""
        explicit = listing.mark
        if listing.own_perch is not None:
            if explicit is not None and explicit != listing.own_perch:
                raise self.error(
                    "field-perch",
                    listing.address,
                    (
                        f"{listing.text} on the {listing.side} side of block "
                        f"{listing.block_id!r} is marked for the {explicit} perch "
                        f"and carries the perch word for {listing.own_perch}; the "
                        f"mark and the word name one perch"
                    ),
                )
            explicit = listing.own_perch
        return explicit

    def control_perch(self, listing, explicit, roles) -> str:
        """The decision perch of a control, in two cases: a control that
        names no perch or the decision perch, and a control whose own perch
        word names a perch of its side; a control placed at any other perch
        is refused under `field-perch`."""
        # the second case reads the perch word alone: a mark is no word, so a
        # control with a mark names no perch there
        admitted = (
            explicit is None
            or explicit == DECISION
            or (
                listing.own_perch is not None
                and listing.own_perch in self.perches_of_side(listing, roles)
            )
        )
        if not admitted:
            raise self.error(
                "field-perch",
                listing.address,
                (
                    f"{listing.text} on the {listing.side} side of block "
                    f"{listing.block_id!r} is a control placed at the "
                    f"{explicit} perch; a control is at the decision perch "
                    f"wherever it is listed, being an argument of the later "
                    f"blocks and not a member of their information sets. List it "
                    f"bare"
                ),
            )
        return DECISION

    def perches_of_side(self, listing, roles) -> set:
        """The perches the listing's side names: the perch word written
        after the side's parenthesis, or, where none is written, every perch
        at which another field of the same side is placed by its own perch
        word or its perch mark. A control places nothing by its word and a
        shock stands at no perch, so neither is read here."""
        if listing.side_perch is not None:
            return {listing.side_perch}
        return {
            other.mark or other.own_perch
            for other in self.side_entries(listing.block_id, listing.side)
            if other is not listing
            and (other.mark is not None or other.own_perch is not None)
            and roles.get(other.stem) not in (CONTROL, SHOCK)
        }

    def side_perch(self, block_id, side) -> str | None:
        """The perch of one side: its written perch word, or, when the word is
        omitted, the one perch its non-shock coordinates share, from which the
        side's perch is inferred; None when they share none."""
        perches = self.written_perches[block_id]
        written = perches.input if side == INPUT else perches.output
        if written is not None:
            return written
        perches = {
            l.wire_type.perch for l in self.side_entries(block_id, side) if l.wire_type is not None
        } - {SHCK}
        return next(iter(perches)) if len(perches) == 1 else None

    # -- 5. the distributions --

    def check_distributions(self) -> None:
        """The owners of the shocks and the edge each shock is drawn on: a
        declaration reading one of its own subject components, a cycle of
        declarations and a parent shock without a declaration are refused,
        and so are two forward builders claiming one shock or connected
        declarations on two edges. The assignment, shock name → forward
        builder, is kept for `shock_edge`."""

        def refuse(rule, address, message):
            raise self.error(rule, address, message)

        def names(term):
            found = []
            pending = [term]
            while pending:
                node = pending.pop(0)
                if isinstance(node, terms.Sym) and isinstance(
                    node.symbol, (terms.Constant, terms.Variable)
                ):
                    if node.symbol.name not in found:
                        found.append(node.symbol.name)
                elif dataclasses.is_dataclass(node) and not isinstance(node, type):
                    pending[:0] = [getattr(node, f.name) for f in dataclasses.fields(node)]
                elif isinstance(node, (list, tuple)):
                    pending[:0] = list(node)
            return found

        owners = []
        for subjects, declaration in self.laws.items():
            term = next(body for body, at in self.law_terms if at == declaration.address)
            arguments = tuple(
                name
                for name in names(term)
                if self.declared_as(name) in ("shock", "field") or name in self.law_of
            )
            owners.append(
                DistributionDeclaration(
                    identity=Identity("distribution", stage=self.stage, subjects=tuple(subjects)),
                    address=declaration.address,
                    subjects=tuple(subjects),
                    term=term,
                    parents=tuple(
                        name
                        for name in arguments
                        if name in self.law_of or self.declared_as(name) == "shock"
                    ),
                    arguments=arguments,
                )
            )
        dependency_order(tuple(owners), refuse)
        forward = []
        for block_id, _ in self.blocks:
            perch_from, perch_to = self.side_perches[block_id]
            outputs = self.side_entries(block_id, OUTPUT)
            if (
                perch_from in PERCHES
                and perch_to in PERCHES
                and _precedes(perch_from, perch_to)
                and outputs
                and all(self.field_roles.get(l.stem) == STATE for l in outputs)
            ):
                forward.append(
                    (
                        block_id,
                        tuple(
                            l.stem
                            for l in self.side_entries(block_id, INPUT)
                            if self.field_roles.get(l.stem) == SHOCK
                        ),
                    )
                )
        self.shock_edges = shock_builders(tuple(owners), tuple(forward), refuse)

    def declared_as(self, name: str) -> str | None:
        """What a name is declared as — a function, a space, a shock, a field,
        or a parameter — or None when the stage does not declare it."""
        if name in self.functions:
            return "function"
        if name in self.spaces:
            return "space"
        if name in self.shocks:
            return "shock"
        if name in self.field_names():
            return "field"
        if name in self.scalars:
            return "parameter"
        return None

    # -- 6. the definitions --

    def resolve_definitions(self) -> None:
        """Fills each definition's operator occurrences and references, and
        the dependency order: every definition after those it references,
        source order otherwise. A cycle, the derivative operator applied to a
        name that is not a defined function, and a call to a declared name
        that is not a function are refused."""
        for definition in self.functions.values():
            definition.operators = tuple(occurrence_paths(definition.body, (definition.slot,)))
            definition.references = tuple(self.check_definition_body(definition))
        order, done, active = [], set(), []

        def visit(name):
            if name in done:
                return
            if name in active:
                cycle = active[active.index(name) :] + [name]
                chain = " references ".join(
                    f"{n} ({self.where(self.functions[n].address)})" for n in cycle
                )
                raise self.error(
                    "definition-order",
                    self.functions[name].address,
                    (
                        f"the function definitions form a cycle: {chain}. No "
                        f"dependency order exists, so no definition can be "
                        f"expanded; break the cycle"
                    ),
                )
            active.append(name)
            for referenced in self.functions[name].references:
                visit(referenced)
            active.pop()
            done.add(name)
            order.append(name)

        for name in self.functions:
            visit(name)
        self.definition_order = tuple(order)
        for body, address in self.law_terms:
            self.check_definition_body(
                _Definition(
                    name="law",
                    params=(),
                    body=body,
                    printed=to_source(body),
                    slot="law",
                    address=address,
                )
            )
        for definition in self.functions.values():
            free_names_with_shocks(
                definition.body,
                definition.address,
                self,
                bound=frozenset(p for p, _ in definition.params),
            )

    def check_definition_body(self, definition) -> list:
        """The defined functions a definition's body mentions, each once, in
        reading order: a call to one, or its name as a value (`Inv(𝑑𝑢)`,
        `D_{c}(𝑢)`). Every other name the body mentions must be in scope
        where the definition stands: one of the definition's own arguments, a
        name bound by an operator's subscript (the `c` of `D_{c}(𝑢)`), or a
        name the stage declares — a parameter, a shock, a named space, a
        field, or another defined function. `inf` is admitted as the infinite
        endpoint the printer writes."""
        out = []
        params = {p for p, _ in definition.params}
        address = definition.address
        where = self.where(address)

        def note(name):
            if name in self.functions and name not in out:
                out.append(name)

        def visit(e, bound=frozenset()):
            if isinstance(e, terms.Call):
                self.check_definition_call(definition, e)
                note(e.fun)
                for a in e.args:
                    visit(a, bound)
            elif isinstance(e, terms.Operator):
                self.check_definition_operator(definition, e, params)
                names = set(bound)
                for s in e.subs:
                    if isinstance(s, terms.In):
                        visit(s.set, bound)
                        names.add(s.var)
                    elif isinstance(s, terms.Var):
                        names.add(s.name)
                if e.head == "E":
                    self.check_expectation_subjects(definition, e)
                for a in e.args:
                    visit(a, frozenset(names))
            elif isinstance(e, terms.Sym):
                self.check_definition_name(definition, e, bound, params)
                if (
                    isinstance(e.symbol, terms.Constant)
                    and e.symbol.name not in params
                    and e.symbol.name not in bound
                ):
                    note(e.symbol.name)
            elif isinstance(e, (terms.Add, terms.Sub, terms.Mul, terms.Div)):
                visit(e.left, bound)
                visit(e.right, bound)
            elif isinstance(e, terms.Neg):
                visit(e.operand, bound)
            elif isinstance(e, terms.Pow):
                visit(e.base, bound)
                visit(e.exponent, bound)
            elif isinstance(e, terms.Tuple):
                for item in e.items:
                    visit(item, bound)
            elif isinstance(e, terms.Select):
                visit(e.family, bound)
            elif isinstance(e, terms.Interval) and isinstance(e.bounds, terms.Range):
                visit(e.bounds.lower, bound)
                visit(e.bounds.upper, bound)
            elif isinstance(e, terms.Product):
                for f in e.factors:
                    visit(f, bound)
            elif isinstance(e, terms.Comprehension):
                # `{c : ℝ₊₊ | c < x}`: the base is read outside the binder; the
                # conditions read the binder c and the definition's arguments
                if e.base is not None:
                    visit(e.base, bound)
                binders = frozenset(bound) | {
                    c.stem for c in e.bound.coordinates if isinstance(c, terms.Coordinate)
                }
                for condition in e.conds:
                    visit(condition.left, binders)
                    visit(condition.right, binders)
            elif isinstance(e, terms.IntegerRange):
                visit(e.lower, bound)
                visit(e.upper, bound)
            elif isinstance(e, terms.Points):
                for member in e.members:
                    visit(member, bound)
                if e.superset is not None:
                    visit(e.superset, bound)
            elif isinstance(e, terms.Functions):
                visit(e.domain, bound)
                visit(e.codomain, bound)
            elif isinstance(e, (terms.Number, terms.Space, terms.Named, terms.FiniteSet)):
                return
            else:
                raise self.error(
                    "readable-form",
                    address,
                    (
                        f"no construction rule reads the {type(e).__name__} in the "
                        f"definition of {definition.name!r} ({where})"
                    ),
                )

        check_selections_and_calls(definition.body, address, self, dict(definition.domains))
        visit(definition.body)
        return out

    def check_definition_call(self, definition, call) -> None:
        """A call in a definition's body names a function or a name the stage
        does not declare; a call to a declared value is refused under
        `definition-order`."""
        declared = self.declared_as(call.fun)
        if declared not in (None, "function"):
            raise self.error(
                "definition-order",
                definition.address,
                (
                    f"the definition of {definition.name!r} calls {call.fun!r}, "
                    f"which is a {declared} of the stage, not a function"
                ),
            )

    def check_definition_operator(self, definition, operator, params) -> None:
        """An operator in a definition's body is one whose binders the
        construction reads, and a derivative differentiates a defined function
        or an argument of the definition."""
        if operator.head not in BOUND_OPERATORS:
            raise self.error(
                "not-constructed",
                definition.address,
                f"no construction rule determines the "
                f"information used by operator {operator.head!r}",
                error_class=NotConstructed,
            )
        if operator.head != "D":
            return
        for a in operator.args:
            if (
                isinstance(a, terms.Sym)
                and isinstance(a.symbol, terms.Constant)
                and a.symbol.name not in self.functions
                and a.symbol.name not in params
            ):
                defined = ", ".join(n for n in self.functions if n != definition.name) or "none"
                raise self.error(
                    "definition-order",
                    definition.address,
                    (
                        f"the derivative operator {to_source(operator)} in the "
                        f"definition of {definition.name!r} is applied "
                        f"to {a.symbol.name!r}, which is not a defined "
                        f"function of the stage (the defined functions "
                        f"are {defined}); D_{{x}}(f) differentiates a "
                        f"defined function f with respect to x "
                        f"(D03 (ii))"
                    ),
                )

    def check_expectation_subjects(self, definition, operator) -> None:
        """Each name an expectation in a definition's body integrates over has
        a declared distribution."""
        for sub in operator.subs:
            name = sub.var if isinstance(sub, terms.In) else sub.name
            if name not in self.law_of:
                raise self.error(
                    "not-constructed",
                    definition.address,
                    f"the expectation over {name!r} needs a declared distribution",
                    error_class=NotConstructed,
                )

    def check_definition_name(self, definition, symbol, bound, params) -> None:
        """A name a definition's body reads is in scope where the definition
        stands: one of its arguments, a name an operator binds, `inf`, or a
        name the stage declares; a marked field is one the stage lists."""
        if isinstance(symbol.symbol, terms.Constant):
            name = symbol.symbol.name
            if not (
                name in params
                or name in bound
                or name == "inf"
                or self.declared_as(name) is not None
            ):
                raise self.error(
                    "name-in-scope",
                    definition.address,
                    (
                        f"the definition of {definition.name!r} mentions "
                        f"{name!r}, which the stage does not declare "
                        f"and which is not an argument of "
                        f"{definition.name!r}. Declare it at the top level, "
                        f"or write an argument of the definition. The names "
                        f"in scope here are {self.names_in_scope_text(params)}"
                    ),
                )
        elif (
            isinstance(symbol.symbol, terms.Variable)
            and listed_identity(
                field_spelling(symbol, definition.address, self), self.listings, self
            )
            is None
        ):
            raise self.error(
                "name-in-scope",
                definition.address,
                (
                    f"the definition of {definition.name!r} mentions the "
                    f"field {symbol.symbol.name!r}, which the stage does not declare. "
                    f"The names in scope here are "
                    f"{self.names_in_scope_text(params)}"
                ),
            )

    def names_in_scope_text(self, params=()) -> str:
        """The names a top-level definition may mention, for a refusal: the
        definition's own arguments, then the names the stage declares, each
        once, in declaration order."""
        names = []
        for name in (
            list(params)
            + list(self.functions)
            + list(self.spaces)
            + list(self.scalars)
            + self.field_names()
        ):
            if name not in names:
                names.append(name)
        return ", ".join(names) or "none"

    # -- 7. the branches --

    def check_branches(self) -> None:
        """Each branching block against its label coordinate, the control
        its header names or, where it names none, the shock over a finite
        set it names. Deferred under `not-constructed`: a relation among the
        branch lines, a second control beside a label control, a branch a
        shock selects in a stage that chooses a control. Otherwise the
        branches carry the members of the coordinate's set in its order; a
        drawn label has a distribution giving each label one probability
        (`check_draw`) and is read under the expectation over it
        (`check_expectations`); a chosen one is selected and maximized over
        one tuple (`check_branch_selection`); each branch value stands at one
        position of the tuples (`check_positions`)."""
        for block_id, labels in self.branch_labels.items():
            address = next(a for b, a in self.blocks if b == block_id)
            inputs = self.side_entries(block_id, INPUT)
            domain = lambda listing: listing.domain_term or self.declared_set_of(listing.stem)
            controls = [l for l in inputs if self.field_roles.get(l.stem) == CONTROL]
            shocks = [
                l
                for l in inputs
                if self.field_roles.get(l.stem) == SHOCK and isinstance(domain(l), terms.FiniteSet)
            ]
            drawn = bool(shocks) and not any(
                isinstance(domain(l), terms.FiniteSet) for l in controls
            )
            chosen = (
                (
                    [l.stem for l in controls]
                    + [
                        l.stem
                        for b, _ in self.blocks
                        for l in self.side_entries(b, OUTPUT)
                        if self.field_roles.get(l.stem) == CONTROL
                    ]
                )
                if drawn
                else []
            )
            relations = [
                a
                for _, a, item in self.bodies[block_id]
                if not isinstance(item.core, terms.Equation)
            ]
            if relations or (drawn and chosen) or (not drawn and len(controls) > 1):
                met = (
                    f"holds the line {relations[0]}, which states no equation, in a branch"
                    if relations
                    else f"holds branches the shock {shocks[0].stem!r} selects, "
                    f"and the stage chooses {chosen[0]!r}"
                    if drawn
                    else f"lists the controls {', '.join(repr(l.stem) for l in controls)} "
                    f"beside its branches"
                )
                self.defer(
                    address,
                    "not-constructed",
                    (
                        f"block {block_id!r} {met}; this version of the package constructs a "
                        f"branching block whose branches state equations alone and whose label "
                        f"coordinate is its one control, or a shock over a finite set in a stage "
                        f"that chooses nothing (docs/Bellman-Sym/05-branching.md)"
                    ),
                )
                continue
            key = shocks[0] if drawn else (controls[0] if controls else None)
            if key is None or not isinstance(domain(key), terms.FiniteSet):
                raise self.error(
                    "branch-labels",
                    address,
                    (
                        f"block {block_id!r} holds branches and lists neither a control nor a "
                        f"shock over a finite set of labels on its input side; a choice lists the "
                        f"control `d : !ctrl @ {{{', '.join(labels)}}}`, and a draw by nature "
                        f"lists a shock declared on the labels, `s : {{{', '.join(labels)}}}`, "
                        f"with its distribution `s ~ Categorical((…))`"
                    ),
                )
            members = tuple(domain(key).members)
            if len(members) < 2:
                raise self.error(
                    "branch-labels",
                    address,
                    (
                        f"the label coordinate {key.stem!r} of block {block_id!r} takes "
                        f"{len(members)} label; a branching block selects among at least two"
                    ),
                )
            unknown = next((label for label in labels if label not in members), None)
            if unknown is not None:
                raise self.error(
                    "branch-labels",
                    f"{block_id}.{unknown}",
                    (
                        f"the label {unknown!r} is not a member of {{{', '.join(members)}}}, the "
                        f"set of the label coordinate {key.stem!r}; write one nested block for "
                        f"each member, in the set's order"
                    ),
                )
            if tuple(labels) != members:
                raise self.error(
                    "branch-labels",
                    address,
                    (
                        f"the branches of block {block_id!r} stand in the order "
                        f"{', '.join(labels)}, and the label coordinate {key.stem!r} takes "
                        f"{{{', '.join(members)}}}; they stand in the set's order"
                    ),
                )
            if drawn:
                self.check_draw(block_id, key.stem, tuple(labels))
                self.check_expectations(block_id, key.stem, tuple(labels))
            else:
                self.check_branch_selection(block_id, key.stem, tuple(labels))
            self.check_positions(key.stem, tuple(labels))

    def check_positions(self, key, labels) -> None:
        """Every tuple indexed by `key` has one entry for each label, and
        each continuation value stands at one position of those tuples, the
        position of its branch."""
        for b, _ in self.blocks:
            for _, a, item in self.bodies[b]:
                for items in selection_tuples(item.core, key):
                    if len(items) != len(labels):
                        raise self.error(
                            "branch-tuple-mismatch",
                            a,
                            (
                                f"the tuple indexed by {key!r} has {len(items)} entries, and "
                                f"{key!r} takes the {len(labels)} labels {{{', '.join(labels)}}}; "
                                f"write one entry for each label, in that order"
                            ),
                        )

        def resolve(line, name, side):
            mark = None if side is None else self.perch_token(side, line, name)
            wire = listed_identity(
                (name, mark), self.side_entries(line.split(".", 1)[0], INPUT), self
            )
            return (
                wire
                if wire is not None
                and wire.perch == CONTINUATION
                and self.field_roles.get(name) in VALUE_ROLES
                else None
            )

        positions = selection_positions(
            [(a, item.core) for b, _ in self.blocks for _, a, item in self.bodies[b]], key, resolve
        )
        for listing in self.listings:
            wire = listing.wire_type
            if (
                wire is None
                or wire.perch != CONTINUATION
                or self.field_roles.get(listing.stem) not in VALUE_ROLES
            ):
                continue
            held = positions.get(wire, [])
            places = sorted({position for position, _ in held})
            if len(places) > 1:
                raise self.error(
                    "branch-value-position",
                    next(a for p, a in held if p == places[1]),
                    (
                        f"{listing.stem}[>] is read at the position of {labels[places[0]]!r} and "
                        f"at the position of {labels[places[1]]!r}; a branch value stands at one "
                        f"position in every tuple, the position of its branch; write each branch "
                        f"value at its own branch's position alone"
                    ),
                )
            if not places:
                raise self.error(
                    "branch-value-position",
                    listing.address,
                    (
                        f"{listing.stem}[>] is read in no selection tuple indexed by {key!r}, so "
                        f"no branch names its fields; read it at its branch's position"
                    ),
                )
            self.value_branches[wire] = labels[places[0]]

    def branch_of_value(self, stem: str):
        """The branch a continuation value is the value of and the states that
        branch writes, `("work", ("y_f_wk", "y_p_wk"))` for `V_wk[>]`, read
        from the value's position in the selection tuples (`check_positions`);
        None for a value that stands in no branch. A derivative of the value,
        `D_{x}V_wk[>]`, names one of these states and not a state of another
        branch of the same perch."""
        wire = Identity("field", stage=self.stage, perch=CONTINUATION, field=stem)
        label = self.value_branches.get(wire)
        if label is None:
            return None
        block_id = next(b for b, labels in self.branch_labels.items() if label in labels)
        states = tuple(
            field
            for field in self.branch_fields[(block_id, label)]
            if self.field_roles.get(field) == STATE
        )
        return label, states

    def check_draw(self, block_id, key, labels) -> None:
        """A label a shock selects: the shock has a distribution giving one
        probability to each label in the set's order
        (`families.label_weights`); otherwise `branch-law`, at the block for
        a missing distribution and at the declaration's item for a malformed
        one."""
        address = next(a for b, a in self.blocks if b == block_id)
        if key not in self.law_of:
            raise self.error(
                "branch-law",
                address,
                (
                    f"the shock {key!r} selects the branches of block {block_id!r} and has no "
                    f"distribution; the branches are weighted by the distribution of the shock, "
                    f"so write `{key} ~ Categorical(("
                    f"{', '.join('p_' + label for label in labels)}))`, one probability for "
                    f"each label in the order {{{', '.join(labels)}}}"
                ),
            )
        law = next(body for body, at in self.law_terms if at == self.law_of[key])
        weights = label_weights(law)
        if weights is None or len(weights) != len(labels):
            given = (
                f"gives {len(weights)} probabilities"
                if weights is not None
                else f"is `{key} ~ {to_source(law)}`, which writes no probability for each label"
            )
            raise self.error(
                "branch-law",
                self.law_of[key],
                (
                    f"the distribution of the label shock {key!r} of block {block_id!r} "
                    f"{given}, and the block draws one of {len(labels)} labels, "
                    f"{{{', '.join(labels)}}}; the distribution gives one probability to "
                    f"each label, in the set's order, `{key} ~ Categorical((p_1, …, p_n))`, "
                    f"or `{key} ~ Bernoulli(p)` on two labels"
                ),
            )

    def check_expectations(self, block_id, key, labels) -> None:
        """A drawn label: every tuple indexed by the shock `key` stands
        under an expectation over `key` alone, `E_{key}((…)[key])`; an
        expectation over `key` reads such a tuple; and the value line of the
        block from the continuation to the decision perch reads one."""
        value = None
        for b, _ in self.blocks:
            for _, a, item in self.bodies[b]:
                core = item.core
                if not isinstance(core, terms.Equation):
                    continue
                averaged = expectations_over(core.rhs, key)
                if any(not selection_tuples(node.args[0], key) for node in averaged):
                    raise self.error(
                        "branch-tuple-mismatch",
                        a,
                        (
                            f"the line takes the expectation over the shock {key!r} of "
                            f"no tuple indexed by it; nature draws {key!r} among the "
                            f"labels {{{', '.join(labels)}}}, so the expectation reads "
                            f"the tuple of the branch values, `E_{{{key}}}((…)[{key}])`, "
                            f"one entry for each label in that order"
                        ),
                    )
                inside = [
                    items for node in averaged for items in selection_tuples(node.args[0], key)
                ]
                if len(inside) != len(selection_tuples(core.rhs, key)):
                    raise self.error(
                        "branch-tuple-mismatch",
                        a,
                        (
                            f"the line selects by the shock {key!r} outside an expectation over "
                            f"it alone; nature draws {key!r} after the decision, so a line "
                            f"averages the branch values under its distribution, "
                            f"`E_{{{key}}}((…)[{key}])`"
                        ),
                    )
                if (
                    inside
                    and self.side_perches[b] == (CONTINUATION, DECISION)
                    and names_fields(core.lhs)
                    and any(
                        self.field_roles.get(stem) == VALUE
                        for stem, _ in outputs_and_unknowns(core.lhs, a, self, core.rhs)
                    )
                ):
                    value = a
        if value is None:
            raise self.error(
                "branch-tuple-mismatch",
                block_id,
                (
                    f"no value line takes the expectation over the shock "
                    f"{key!r} of a tuple indexed by it; the value of a branch "
                    f"{key!r} selects is `V = E_{{{key}}}((…)[{key}])`, one "
                    f"entry for each label in the order {{{', '.join(labels)}}}"
                ),
            )

    def check_branch_selection(self, block_id, key, labels) -> None:
        """A chosen label: the value line of the block from the continuation
        to the decision perch selects by one tuple indexed by the chosen
        label `key`, and the policy's `argmax` over `key` maximizes over
        that tuple; `check_positions` then places each continuation value."""
        value = policy = None
        for b, _ in self.blocks:
            for _, a, item in self.bodies[b]:
                core = item.core
                if not isinstance(core, terms.Equation):
                    continue
                if (
                    self.side_perches[b] == (CONTINUATION, DECISION)
                    and names_fields(core.lhs)
                    and any(
                        self.field_roles.get(stem) == VALUE
                        for stem, _ in outputs_and_unknowns(core.lhs, a, self, core.rhs)
                    )
                ):
                    value = _AuthoredLine(address=a, rhs=core.rhs)
                if (
                    isinstance(core.rhs, terms.Operator)
                    and core.rhs.head == "argmax"
                    and len(core.rhs.subs) == 1
                    and subscript_binder(core.rhs.subs[0]) == key
                ):
                    policy = _AuthoredLine(address=a, rhs=core.rhs)
        tuples = selection_tuples(value.rhs, key) if value else []
        chosen = selection_tuples(policy.rhs, key) if policy else []
        if not tuples or not chosen or tuples[0] != chosen[0]:
            written = lambda items: "(" + ", ".join(to_source(item) for item in items) + ")"
            read = (
                f"selects from {written(tuples[0])} by {key!r}"
                if tuples
                else f"selects by no tuple indexed by {key!r}"
            )
            maximized = (
                f"the policy line {policy.address} maximizes over {written(chosen[0])}"
                if chosen
                else f"no policy line maximizes over the label coordinate {key!r}"
            )
            write = (
                "write the policy's maximand as the value line's tuple, in its order"
                if tuples
                else f"write the value line as the tuple of the branch values indexed by {key!r}, "
                f"and the policy's maximand as that tuple, in its order"
            )
            raise self.error(
                "branch-tuple-mismatch",
                value.address if value else block_id,
                (f"the value line {read}, and {maximized}; {write}"),
            )

    def declared_set_of(self, name: str):
        """The set term a name is declared with: at a listing that carries a
        set, in textual order, or at its top-level declaration; None when no
        declaration carries a set."""
        for listing in self.listings:
            if listing.stem == name and listing.domain_term is not None:
                return listing.domain_term
        if name in self.scalars:
            return self.scalars[name].domain_term
        return None

    # -- 8. the forms the package does not construct --

    def refuse_unconstructed(self) -> None:
        """The refusal `NotConstructed` of the textually first item this
        module does not construct, raised after the whole declaration pass."""
        if self.deferred:
            first = min(self.deferred, key=lambda deferred: deferred.order)
            raise self.error(first.rule, first.address, first.message, error_class=NotConstructed)

    # -- 9. the statements of every block --

    def check_statements(self) -> None:
        """Every line of every block, in textual order: the lines of one
        block carry distinct ids, every selection takes a coordinate of a
        declared family, every name a line mentions is in scope where it
        stands, and its dependencies satisfy the information rules of its
        operators and its left side."""
        for block_id, _ in self.blocks:
            self.check_block(block_id)

    def unread_value_inputs(self) -> dict:
        """The input listings of each backward block that list a value field
        no line of the block reads, by block id and in header order (AAS, 17
        October 2026): the inputs the block's box and its builder leave out,
        which the stage records as diagnostics under `unread-input`. A line
        reads the names of its right side, of its clause after `⟂` and of a
        left side that names no field, as `check_names_in_scope` reads them,
        a `!doc` line and a property line among the lines, so the listings
        answered here are exactly the ones `signature-complete` does not
        require. A block whose lines read no listed value input keeps its
        listings, since the kernel of a statement with no value dependency
        takes one as its formal input (rule `value-input-role`), and is not
        in the answer. Called after `check_statements`, so every line has
        been read under the scope rules."""
        found = {}
        for block_id, _ in self.blocks:
            if not self.block_is_backward(block_id):
                continue
            listings = self.side_entries(block_id, INPUT)
            values = [l for l in listings if self.field_roles.get(l.stem) in VALUE_ROLES]
            if not values:
                continue
            read = set()
            for _, address, item in self.bodies[block_id]:
                core = item.core
                equation = core.core if isinstance(core, terms.Slack) else core
                reads = [equation.rhs] + self.clause_reads(core, equation, address)
                if not names_fields(equation.lhs):
                    reads.append(equation.lhs)
                for term in reads:
                    for spelling in free_names(term, address, self):
                        identity = listed_identity(spelling, listings, self)
                        if identity is not None:
                            read.add(identity)
            unread = tuple(l for l in values if l.wire_type not in read)
            if unread and len(unread) < len(values):
                found[block_id] = unread
        return found

    def check_block(self, block_id: str) -> None:
        listings = self.side_entries(block_id, INPUT) + self.side_entries(block_id, OUTPUT)
        out_listings = self.side_entries(block_id, OUTPUT)
        # line address -> the line's place in the block; a line's address holds
        # its branch, so one id in two branches is two lines
        ids = {}
        aliases = {}  # lhs spelling -> the right side of an earlier alias
        # every spelling an earlier line defines, in order; a multiplier the
        # block declares is in scope on every line of it
        defined = [
            (stem, CONTINUATION)
            for stem, multiplier in self.multipliers.items()
            if multiplier.block == block_id
        ]
        definitions = {}  # lhs spelling -> the address of its operative equation
        stated = {}  # (coordinate, value spelling) -> the address of the derivative line
        candidates = []  # (candidate spelling, address, place in the block) of each candidate line
        reads_of = []  # (place in the block, the spellings the line reads) of each line
        envelope_reads = self.envelope_reads(block_id)
        for ordinal, address, item in self.bodies[block_id]:
            core = item.core
            equation = core.core if isinstance(core, terms.Slack) else core
            marks, _ = annotation_entries(item.annot, address, self)
            self.check_line_id(block_id, item, ordinal, address, ids)
            check_selections_and_calls(equation.rhs, address, self, local_values=aliases)
            if isinstance(equation, terms.Equation) and derivative_left_side(equation.lhs):
                # a derivative line, `D_{k_d}V = E_{θ}(D_{m}V[>]*R)`, is a statement
                # about the value its term names, read at that value's perch; it
                # defines no field and states no candidate (AMD-MB-001 §4.3)
                left_fields = [field_spelling(equation.lhs.args[0], address, self)]
                if DOC not in marks:
                    self.check_stated_once(block_id, equation.lhs, left_fields[0], address, stated)
            else:
                left_fields = outputs_and_unknowns(
                    equation.lhs,
                    address,
                    self,
                    equation.rhs,
                    relation=not isinstance(equation, terms.Equation),
                )
            if (
                isinstance(equation, terms.Equation)
                and DOC not in marks
                and names_fields(equation.lhs)
            ):
                self.check_defined_once(block_id, left_fields, address, definitions)
            if len(left_fields) > 1 and any(
                listed_identity(lhs, out_listings, self) is None for lhs in left_fields
            ):
                raise unreadable_form_refusal(
                    self,
                    address,
                    "a joint-choice tuple must name declared output "
                    "fields; local tuple aliases are not constructed",
                )
            reads = [equation.rhs] + self.clause_reads(core, equation, address)
            for term in reads:
                self.check_names_in_scope(block_id, term, defined, listings, address)
            read_terms = list(reads)
            if not names_fields(equation.lhs):
                self.check_names_in_scope(block_id, equation.lhs, defined, listings, address)
                read_terms.append(equation.lhs)
            reads_of.append(
                (
                    ordinal,
                    {spelling for term in read_terms for spelling in free_names(term, address, self)},
                )
            )
            if names_fields(equation.lhs) and DOC not in marks:
                for lhs in left_fields:
                    if self.policy_candidate_spelling(block_id, lhs):
                        self.check_candidate_coordinate(block_id, lhs, address, envelope_reads)
                        candidates.append((lhs, address, ordinal))
            if self.block_is_backward(block_id):
                output_perch = self.backward_perches(block_id)[1]
                # a candidate written as an inequality,
                # `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`, is read at the perch
                # of its left side, as the same candidate written as an
                # equation is
                line_perches = (
                    [self.backward_line_perch(block_id, lhs, output_perch) for lhs in left_fields]
                    if left_fields and isinstance(equation, (terms.Equation, terms.Inequality))
                    else [output_perch]
                )
                for line_perch in line_perches:
                    for term in [equation.lhs, *reads]:
                        self.check_input_perch_state(
                            block_id, line_perch, term, aliases, address
                        )
            for lhs in left_fields:
                lhs_type = listed_identity(lhs, out_listings, self)
                for read in reads:
                    self.check_known_at_perch(
                        block_id, lhs, lhs_type, read, aliases, address
                    )
                if lhs not in defined:
                    defined.append(lhs)
                if lhs_type is None and DOC not in marks:
                    aliases[lhs] = equation.rhs
        for multiplier in self.multipliers.values():
            if multiplier.block == block_id:
                self.check_bound_names(block_id, multiplier)
        self.check_candidates_read(block_id, candidates, reads_of)

    def backward_line_perch(self, block_id, spelling, output_perch):
        """The perch for checking a backward line's state reads. A named
        arrival line uses its marked perch; a continuation-marked line uses
        continuation only when it defines a policy candidate. An unmarked
        local name uses the block's output perch."""
        perch = perch_of_spelling(spelling, block_id, self)
        if perch not in PERCHES:
            return output_perch
        if perch == CONTINUATION and not self.policy_candidate_spelling(block_id, spelling):
            return output_perch
        return perch

    def check_line_id(self, block_id, item, ordinal, address, ids) -> None:
        """The id a line carries names one line of its block; `ids` holds the
        address of each line read so far with its place in the block, and a
        line's address holds its branch, so one id in two branches is two
        lines."""
        written_id = statement_id(item.annot)
        if written_id is None:
            return
        # Two lines with one id have one term address. A fresh parse
        # refuses them before construction
        # (`bellman.syntax.lower.parse_with_spans`); a term decoded from
        # a saved AST, or built by hand, is read by this check, whose
        # answer depends on the term alone.
        if address in ids:
            raise self.error(
                "declared-once",
                address,
                (
                    f"two lines of block {block_id!r} carry the id "
                    f"{written_id!r}: line {ids[address]} and line "
                    f"{ordinal} of the block. A methods file names a line "
                    f"by `<block>.<id>` and a method must reach one line, "
                    f"so give each line its own id"
                ),
            )
        ids[address] = ordinal

    def check_defined_once(self, block_id, left_fields, address, definitions) -> None:
        """An operative equation defines each field of its left side once in
        its block; `definitions` holds the address of the equation that first
        defines each field."""
        for lhs in left_fields:
            first = definitions.get(lhs)
            if first is not None:
                raise self.error(
                    "defined-once",
                    address,
                    (
                        f"block {block_id!r} already defines "
                        f"{spelling_text(lhs)} at {self.where(first)}, and "
                        "this operative equation defines it again; an operative "
                        "left side is defined once within a block"
                    ),
                )
            definitions[lhs] = address

    def check_stated_once(self, block_id, lhs, spelling, address, stated) -> None:
        """A derivative line states each derivative term, `D_{m_d}V`, once in
        its block; `stated` holds the address of the line that first states
        each term, by its coordinate and the value's spelling (`defined-once`
        extended to derivative terms, F68 of the case studies of specification
        0.7)."""
        key = (lhs.subs[0].name, spelling)
        first = stated.get(key)
        if first is not None:
            raise self.error(
                "defined-once",
                address,
                (
                    f"block {block_id!r} already states D_{{{key[0]}}}{spelling_text(spelling)} "
                    f"at {self.where(first)}, and this derivative line states it again; a "
                    "derivative term is stated once within a block"
                ),
            )
        stated[key] = address

    def envelope_reads(self, block_id) -> set:
        """The spellings the upper envelopes of a block compare: the names read
        by the arguments of each `upper_env` call in the block's lines, among
        them the value candidate `v[>]` of `c = upper_env(w[>], c[>], v[>])`,
        for which the language has no other spelling."""
        found = set()
        for _, address, item in self.bodies[block_id]:
            core = item.core.core if isinstance(item.core, terms.Slack) else item.core
            for node in nodes(core.rhs):
                if isinstance(node, terms.Call) and node.fun == "upper_env":
                    for argument in node.args:
                        found.update(free_names(argument, address, self))
        return found

    def candidate_names(self) -> tuple:
        """The names a candidate line may write under the continuation mark:
        the controls of the stage, and the states of the decision perch,
        whose candidate line is the grid line."""
        controls = [
            listing.stem
            for listing in self.listings
            if self.field_roles.get(listing.stem) == CONTROL
        ]
        states = [
            listing.stem
            for listing in self.listings
            if listing.wire_type is not None
            and listing.wire_type.perch == DECISION
            and self.field_roles.get(listing.stem) == STATE
        ]
        return tuple(dict.fromkeys(controls)), tuple(dict.fromkeys(states))

    def check_candidate_coordinate(self, block_id, spelling, address, envelope_reads) -> None:
        """A candidate line of a policy block, `x[>] = …`, names a control at
        the candidate points, `c[>]`, a state of the decision perch, the grid
        line `m[>] = a + c[>]`, or the value candidate an upper envelope of
        the block compares; any other name is refused under
        `candidate-coordinate` with the coordinates in scope (F39 of the case
        studies of specification 0.7)."""
        controls, states = self.candidate_names()
        if spelling.stem in controls or spelling.stem in states or spelling in envelope_reads:
            return
        raise self.error(
            "candidate-coordinate",
            address,
            (
                f"the line writes {spelling_text(spelling)}, a candidate of {spelling.stem!r}, "
                f"which is no control and no state of the {DECISION} perch, and no upper "
                f"envelope of block {block_id!r} compares it; a candidate line of a solution "
                f"method names a control at the candidate points, a state of the decision "
                f"perch, which is the grid line, or the value candidate an upper envelope "
                f"reads (rule candidate-coordinate). The controls are "
                f"{', '.join(controls) or 'none'} and the states of the {DECISION} perch are "
                f"{', '.join(states) or 'none'}"
            ),
        )

    def check_candidates_read(self, block_id, candidates, reads_of) -> None:
        """A candidate a policy block writes is read by a later line of the
        block or is the grid line, a state of the decision perch at the
        candidates, whose points are the knots at which the policy is stored;
        a candidate nothing reads is refused under `candidate-read` naming
        the line (F61 of the case studies of specification 0.7)."""
        _, states = self.candidate_names()
        for spelling, address, ordinal in candidates:
            if spelling.stem in states:
                continue
            if any(spelling in read for place, read in reads_of if place > ordinal):
                continue
            raise self.error(
                "candidate-read",
                address,
                (
                    f"the line writes the candidate {spelling_text(spelling)}, which no later "
                    f"line of block {block_id!r} reads; a candidate is read by a later line of "
                    f"the block, as an identification `{spelling.stem} = "
                    f"{spelling_text(spelling)}` reads it, or is the grid line, a state of the "
                    f"decision perch at the candidates, whose points are the knots at which the "
                    f"policy is stored (rule candidate-read). Read the candidate on a later "
                    f"line, or remove the line"
                ),
            )

    def clause_reads(self, core, equation, address) -> list:
        """The expressions a line's clause reads, after `⟂`: none for a line
        without a clause. A clause with two bounds is the ascending weak chain
        after an equation, and a one-bound clause writes the bounded quantity
        first; any other clause is refused under `readable-form`."""
        if not isinstance(core, terms.Slack):
            return []
        chain = core.bound
        if isinstance(chain, terms.Between) and not (
            isinstance(chain.lo, terms.Le) and isinstance(chain.hi, terms.Le)
        ):
            raise self.error(
                "readable-form",
                address,
                (
                    f"the clause of this line writes the chain `{to_source(chain)}`; a clause "
                    f"with two bounds is read as the ascending weak chain, lower bound, "
                    f"quantity, upper bound, and no rule reads a descending, strict or mixed "
                    f"one (AMD-SG-035 §4). Write `lb <= x <= ub`"
                ),
            )
        if isinstance(chain, terms.Between) and isinstance(equation, terms.Inequality):
            raise self.error(
                "readable-form",
                address,
                (
                    f"the clause `⟂ {to_source(chain)}` follows an inequality; a clause with "
                    f"two bounds has a sign rule on an equation alone (AMD-SG-035 §2, D13). "
                    f"Write the line as an equation, or give its clause one bound"
                ),
            )
        if isinstance(chain, terms.Rel) and is_number_alone(chain.left):
            raise self.error(
                "readable-form",
                address,
                (
                    f"the clause `⟂ {to_source(chain)}` writes a number or `inf` alone before its "
                    f"relation sign; the sign of the line's residual is read from a one-bound "
                    f"clause written with the bounded quantity first, so this spelling would "
                    f"state the reversed sign (AMD-SG-035 §2, E33). Write "
                    f"`⟂ {to_source(converse_bound(chain))}`"
                ),
            )
        return list(bound_expressions(chain))

    def check_names_in_scope(self, block_id, rhs, defined, listings, address) -> None:
        """Every name a line reads is in scope where the line stands, having a
        declaration or a binder there: a parameter, a named space or a function
        the stage defines, whose own formal coordinates are no reads of the
        line; a field an earlier line of the same block defines; a field the
        block's header lists; or a name an operator's subscript binds — the
        shocks of `E_{Ψ,θ}(…)` inside its written integrand, the binder of
        `argmax_{c : Γ(m_d)}(…)` and of `solve_{ς}(…)` — which is no read.

        A block's header is complete: a field or a shock of the stage that
        the block's header does not list and no earlier line of the block
        defines is refused under `signature-complete`, with the header that
        lists it. The header is what this rule is about, not the record
        `signature()` answers, which is the block's wires and leaves a
        control the header names out. In a backward block, a state field of
        any perch that a line mentions is a coordinate and no input (AAS, 12
        October 2026): a state of the perch at which the output stands is an
        argument of the function the block defines, and a continuation state
        is the bound coordinate of the policy lines that compute the policy
        by inverting functions of it, so the block reads no state as a wire
        and such a field needs no listing. The name then resolves to the
        stage field a forward block's side places, with any set a preamble
        declaration gives it, and whether the line may read it at its perch
        is `check_known_at_perch`'s question. A value field a backward line
        reads is listed as before, so the correction a backward block
        receives names value fields alone. Listing a name does not make a
        shock known at an earlier perch; `check_known_at_perch` asks that
        separately. A call to a name the stage does not declare is admitted:
        the language declares no built-in functions, so `log(x)` names a
        function the realization supplies. A bare name that nothing in the
        file declares — a misspelled field, a parameter the file forgot to
        declare — is refused under `name-in-scope`."""
        for spelling in free_names(rhs, address, self):
            stem, _ = spelling
            if (
                spelling in defined
                or stem == "inf"
                or listed_identity(spelling, listings, self) is not None
            ):
                continue
            declared = self.declared_as(stem)
            if declared in ("parameter", "function", "space"):
                continue
            if (
                declared == "field"
                and self.field_roles.get(stem) == STATE
                and self.block_is_backward(block_id)
            ):
                if perch_of_spelling(spelling, block_id, self, elsewhere=True) is None:
                    self.refuse_two_perch_state(block_id, spelling, address)
                continue
            if declared in ("field", "shock"):
                kind = "backward" if self.block_is_backward(block_id) else "forward"
                lists = (
                    "the value fields its lines read, with the controls at which they are read"
                    if self.block_is_backward(block_id)
                    else "every field its lines read"
                )
                raise self.error(
                    "signature-complete",
                    address,
                    (
                        f"the line reads {spelling_text(spelling)}, which the header of block "
                        f"{block_id!r} does not list and no earlier line of the block defines; a "
                        f"{kind} block's header lists {lists} (AMD-SG-007 §5, rule "
                        f"signature-complete). List it in the header, "
                        f"`{self.corrected_header(block_id, spelling)}`, or define it on an "
                        f"earlier line of the block. The correction writes a perch word on each "
                        f"field of a side where the side's one word no longer holds for every "
                        f"field; the perch of a control is unchanged by either spelling, being "
                        f"the decision perch wherever a header lists it (AMD-SG-017 §2)"
                    ),
                )
            raise self.error(
                "name-in-scope",
                address,
                (
                    f"the line mentions {spelling_text(spelling)}, which the stage "
                    f"does not declare: it is no field of the stage, no line of "
                    f"block {block_id!r} above it defines it, and it is no "
                    f"parameter, shock, named space, or function. Declare it, or "
                    f"write one of the names in scope here: "
                    f"{self.block_names_in_scope_text(listings, defined)}"
                ),
            )

    def refuse_two_perch_state(self, block_id, spelling, address) -> None:
        """A bare name a backward line mentions that the stage places at two
        perches, `a` at arrival and `a[>]` at continuation in `disc.bl`, names
        the state of no one perch, so it is refused under `name-in-scope`
        with the two perches and the marks that choose between them. A state
        a backward header listed under the bare name was placed by that
        listing before AAS's ruling of 12 October 2026; a backward header lists
        no state, so the mark alone decides."""
        perches = []
        for listing in self.listings:
            if listing.stem == spelling.stem and listing.wire_type is not None:
                if listing.wire_type.perch not in perches:
                    perches.append(listing.wire_type.perch)
        if len(perches) < 2:
            raise self.error(
                "name-in-scope",
                address,
                (
                    f"the line mentions {spelling_text(spelling)}, a state that no side of a "
                    f"forward block places at a perch, so it is the field of no perch where "
                    f"the line stands; a backward block's header lists no state, so a forward "
                    f"block's side places every state. List it on the side of the forward "
                    f"block that reads or writes it"
                ),
            )
        marks = {ARRIVAL: "[<]", DECISION: "", CONTINUATION: "[>]"}
        choices = ", ".join(
            f"`{spelling.stem}{marks.get(perch, '')}` for the {perch} state" for perch in perches
        )
        raise self.error(
            "name-in-scope",
            address,
            (
                f"the line mentions {spelling_text(spelling)}, a state the stage places at "
                f"{len(perches)} perches, {' and '.join(perches)}, so the bare name names the "
                f"state of no one perch where the line stands; a backward block's header "
                f"lists no state, so the mark decides. Write {choices}"
            ),
        )

    def block_names_in_scope_text(self, listings, defined) -> str:
        """The names a line of one block may mention, for a refusal: the
        fields the block lists, the names its earlier lines define, then the
        stage's functions, named spaces, parameters, shocks, and its fields
        at every other perch."""
        names = []
        for listing in listings:
            if listing.text not in names:
                names.append(listing.text)
        for spelling in defined:
            text = spelling_text(spelling)
            if text not in names:
                names.append(text)
        for name in (
            list(self.functions)
            + list(self.spaces)
            + list(self.parameters())
            + list(self.shocks)
            + self.field_names()
        ):
            if name not in names:
                names.append(name)
        return ", ".join(names) or "none"

    def parameters(self) -> dict:
        """The top-level scalar declarations that are not fields and not
        shocks (no function or space name is among them: those names are
        refused before this point)."""
        field_names = set(self.field_names())
        return {
            name: declaration.domain
            for name, declaration in self.scalars.items()
            if name not in field_names and name not in self.shocks
        }

    def corrected_header(self, block_id, spelling) -> str:
        """The signature of a block with a field one of its lines reads
        added to its input side: every listing as written, the added field
        with a perch word where neither a mark nor its role places it, and,
        when the input side's one perch word no longer holds for every
        field, that word written on each listing it placed instead. A state a
        backward line reads never reaches this correction, since
        `check_names_in_scope` reads it as a coordinate; the correction of a
        backward header therefore adds a value field alone."""
        stem, mark = spelling
        wire = listed_identity(spelling, self.listings, self)
        perch = mark or (wire.perch if wire else None)
        inputs = self.side_entries(block_id, INPUT)
        outputs = self.side_entries(block_id, OUTPUT)
        written_in, written_out = self.written_perches[block_id]

        def placed(listing):
            return (
                listing.mark is None
                and listing.own_perch is None
                and self.field_roles.get(listing.stem) not in (CONTROL, SHOCK)
            )

        added = (
            mark is None
            and self.field_roles.get(stem) not in (CONTROL, SHOCK)
            and perch not in (None, SHCK)
        )
        keep = written_in is not None and (not added or perch == written_in)

        listed = [
            _header_entry(l, None if keep or not placed(l) else written_in) for l in inputs
        ]
        listed.append(spelling_text(spelling) + (f" : !{perch}" if added and not keep else ""))
        source = f"({', '.join(listed)})" + (f" : !{written_in}" if keep else "")
        target = f"({', '.join(_header_entry(l) for l in outputs)})" + (
            f" : !{written_out}" if written_out else ""
        )
        return f"{source} -> {target}"

    def header_without(self, block_id, spelling, side=INPUT) -> str:
        """The signature of a block as written with one listing of its input
        or output side removed, the one of the field `spelling` names: every
        other listing as written, and each side's perch word as written. It
        is the correction a refusal under `header-coordinate` names."""
        stem, mark = spelling
        inputs = [
            l
            for l in self.side_entries(block_id, INPUT)
            if side != INPUT or not (l.stem == stem and l.mark == mark)
        ]
        outputs = [
            l
            for l in self.side_entries(block_id, OUTPUT)
            if side != OUTPUT or not (l.stem == stem and l.mark == mark)
        ]
        written_in, written_out = self.written_perches[block_id]
        source = f"({', '.join(_header_entry(l) for l in inputs)})" + (
            f" : !{written_in}" if written_in else ""
        )
        target = f"({', '.join(_header_entry(l) for l in outputs)})" + (
            f" : !{written_out}" if written_out else ""
        )
        return f"{source} -> {target}"

    def check_known_at_perch(self, block_id, lhs, lhs_type, rhs, aliases, address) -> None:
        """The check of every dependency of a line under the operators that
        contain it.

        Expectations integrate only their bound shocks. Root and maximization
        binders introduce only their unknowns; neither admits an unrelated
        shock. The equations of a law of motion read both endpoint states. A
        backward block's line reads a state of the block's input perch
        through the law of motion alone (`check_input_perch_state`, called on
        every expression of the line in `check_block`).
        """
        dependencies = free_names_with_shocks(rhs, address, self, aliases=aliases)
        left = perch_of_spelling(lhs, block_id, self)
        if left is None or left == SHCK:
            return
        direct = self.transition_perches(block_id, lhs, lhs_type)
        for spelling, integrated in dependencies:
            perch = perch_of_spelling(spelling, block_id, self, elsewhere=True)
            if perch is None or perch == left or perch in direct:
                continue
            if perch == SHCK:
                if spelling.stem in integrated:
                    continue
                # a backward block's own edge shocks are checked by the fold,
                # which admits a local result a later expectation
                # integrates
                if self.backward_block_edge(block_id) is not None and self.shock_edge(
                    spelling.stem
                ) == self.backward_block_edge(block_id):
                    continue
                self.check_shock_observed(spelling.stem, left, address)
            else:
                self.check_forward_reading(spelling, perch, left, address, integrated)

    def check_input_perch_state(self, block_id, left, rhs, aliases, address) -> None:
        """A line of a backward block that is read at the perch its output
        stands at mentions a state of a later perch only where the law of
        motion reaches it: inside an expectation
        over a shock drawn on the edge between the two perches, whose fold
        composes the integrand with the law of motion before it integrates,
        or by the forward block's equation for the state written in its
        place. A direct read of such a state across a chain of forward blocks
        that draws no shock is refused under `input-perch-state`, naming the
        forward block that defines the state and the equation it writes;
        across an edge that draws a shock the direct read stays refused under
        `shock-observed` by `check_forward_reading`. Two reads of a policy block are no case of
        this rule (AMD-SG-017 §2): a candidate line, whose left side stands
        under the continuation mark, is read at the continuation perch; and a
        line at the decision perch that reads a candidate the block's earlier
        lines define, `c = upper_env(w[>], c[>], v[>])`, reads the candidate
        and not the state that indexes it, so the aliases of such candidates
        are not read in place here, while a bare alias is, so that no alias
        hides a direct read. A state that the forward law itself places at
        continuation is not a policy candidate even if a policy line repeats
        its name. AAS accepted the rule and its exceptions in
        decision BH-4 on 13 October 2026."""
        if not self.block_is_backward(block_id):
            return
        perch_in, perch_out = self.backward_perches(block_id)
        if left not in PERCHES:
            left = perch_out
        if left not in PERCHES:
            raise self.error(
                "field-perch", address,
                f"the backward line has no perch at which its state reads can be checked",
            )
        bare_aliases = {alias: body for alias, body in aliases.items() if alias.mark is None}
        for spelling, integrated in free_names_with_shocks(
            rhs, address, self, aliases=bare_aliases
        ):
            if self.continuation_policy_candidate(block_id, spelling, aliases):
                continue
            if self.field_roles.get(spelling.stem) != STATE:
                continue
            perch = perch_of_spelling(spelling, block_id, self, elsewhere=True)
            if perch is None or perch == SHCK or not _precedes(left, perch):
                continue
            chain = forward_blocks_between(left, perch, self)
            if chain is None:
                reached = "a later perch with no complete forward law of motion from " + left
                missing = [
                    f"{PERCHES[i]} to {PERCHES[i + 1]}"
                    for i in range(PERCHES.index(left), PERCHES.index(perch))
                    if self.block_between(PERCHES[i], PERCHES[i + 1]) is None
                ]
                supplied = (
                    f"The stage writes no forward block from {', '.join(missing)}, so it "
                    f"supplies no {left}-perch expression for {spelling_text(spelling)}. "
                    f"Define the missing forward relation and use its {left}-perch expression "
                    f"in this line"
                )
            else:
                if any(self.input_shocks(block) for block in chain):
                    self.check_forward_reading(spelling, perch, left, address, integrated)
                    continue
                if left != perch_out:
                    reached = (
                        f"a later perch than the {left} perch where this line stands, reached "
                        "through " + " then ".join(repr(block) for block in chain)
                    )
                elif perch_in is None:
                    reached = (
                        "a later perch than the one where this line stands, with no input "
                        "perch named in the block's header"
                    )
                elif perch == perch_in:
                    reached = f"the perch block {block_id!r} reads its inputs at"
                else:
                    reached = (
                        "a perch after the one the block reads its inputs at, reached through "
                        + " then ".join(repr(block) for block in chain)
                    )
                law = self.authored_law(chain[-1], spelling.stem)
                if law is None:
                    supplied = (
                        f"No line of the forward block {chain[-1]!r} defines {spelling.stem}, "
                        f"so the law of motion supplies no {left}-perch expression for it. "
                        f"Define that state in the forward law and use its {left}-perch "
                        f"expression in this line"
                    )
                elif len(chain) == 1:
                    where, equation, expression = law
                    replacement = (
                        f"Write `{to_source(expression)}` in its place"
                        if self.replacement_at_perch(expression, block_id, left, address)
                        else f"Express it using names in scope at the {left} perch"
                    )
                    supplied = (
                        f"The forward block {chain[0]!r} defines it at {where}, `{equation}`. "
                        f"{replacement}"
                    )
                else:
                    where, equation, _ = law
                    supplied = (
                        f"The forward block {chain[-1]!r} defines it at {where}, `{equation}`, whose "
                        f"right side is read in turn through the earlier blocks of the chain. Write "
                        f"the {left}-perch expression the laws give it in its place"
                    )
            raise self.error(
                "input-perch-state",
                address,
                (
                    f"the line is read at the {left} perch and mentions "
                    f"{spelling_text(spelling)}, a state of the {perch} perch, {reached}; a "
                    f"backward block reaches a state of its input perch, or of a later perch, "
                    f"through the law of motion alone, and read directly the state would stand "
                    f"free in a rule that holds on the {left} state (rule input-perch-state). "
                    f"{supplied}"
                ),
            )

    def policy_candidate_spelling(self, block_id, spelling) -> bool:
        """A continuation-marked name of a policy candidate, rather than a
        state the stage's forward law places at continuation."""
        outputs = self.side_entries(block_id, OUTPUT)
        return (
            spelling.mark == CONTINUATION
            and bool(outputs)
            and all(self.field_roles.get(entry.stem) == CONTROL for entry in outputs)
            and not any(
                entry.stem == spelling.stem
                and entry.wire_type is not None
                and entry.wire_type.perch == CONTINUATION
                for entry in self.listings
            )
        )

    def continuation_policy_candidate(self, block_id, spelling, aliases) -> bool:
        """A policy candidate that an earlier operative line defines."""
        return spelling in aliases and self.policy_candidate_spelling(block_id, spelling)

    def replacement_at_perch(self, expression, block_id, perch, address) -> bool:
        """Whether the right side of a forward law uses names a backward line
        can read at `perch`. An alias local to the forward block is not such a
        name, even when the forward block's next line uses it."""
        for spelling in free_names(expression, address, self):
            kind = self.declared_as(spelling.stem)
            if kind in ("parameter", "function", "space"):
                continue
            if kind != "field" or perch_of_spelling(
                spelling, block_id, self, elsewhere=True
            ) != perch:
                return False
        return True

    def authored_law(self, block_id: str, stem: str):
        """The authored equation of a forward block that defines the state
        `stem`, as the position of its line, its text `stem = rhs`, and the
        right-side expression, or None
        where no operative line of the block defines it. The text is the
        line as written, read from the parsed term, and no definition of its
        own: the law of motion stays the forward block's."""
        for _, address, item in self.bodies[block_id]:
            core = item.core
            equation = core.core if isinstance(core, terms.Slack) else core
            if not isinstance(equation, terms.Equation) or not isinstance(equation.lhs, terms.Sym):
                continue
            marks, _ = annotation_entries(item.annot, address, self)
            if DOC in marks:
                continue
            if field_spelling(equation.lhs, address, self).stem == stem:
                return self.where(address), f"{stem} = {to_source(equation.rhs)}", equation.rhs
        return None

    def transition_perches(self, block_id, lhs, lhs_type) -> frozenset:
        """The two perches a line of a law of motion reads directly: the input
        and output perches of a forward block whose output state the line
        defines. Empty for every other line, whose right side is read at its
        left side's perch."""
        perch_from, perch_to = self.side_perches[block_id]
        if lhs_type is None or perch_from is None or perch_to is None:
            return frozenset()
        if not _precedes(perch_from, perch_to):
            return frozenset()
        if self.field_roles.get(lhs.stem) != STATE:
            return frozenset()
        return frozenset((perch_from, perch_to))

    def check_shock_observed(self, shock: str, left: str, address) -> None:
        """A shock is drawn on the edge between two perches: it is known at
        the later of them and at every perch after it, and not before. A line
        read at a perch that has not observed it must take an expectation
        over it."""
        drawn = self.shock_edge(shock)
        if drawn is None:
            raise self.error(
                "shock-observed",
                address,
                (
                    f"the line mentions the shock {shock!r}, but no block lists "
                    f"{shock!r} on an input side, so the stage does not say when it "
                    f"is drawn. List it on the input side of the block that draws "
                    f"it, as `(k_d, ς, Ψ, θ) : !dcsn` does in port.bl, or take an "
                    f"expectation over it"
                ),
            )
        before, after = drawn
        if not _precedes(left, after):
            return
        raise self.error(
            "shock-observed",
            address,
            (
                f"the line is read at the {left} perch and its right side depends "
                f"on the shock {shock!r}, which is drawn between the {before} and "
                f"the {after} perch: at the {left} perch its value is not yet "
                f"known. Write the expectation over it, `E_{{{shock}}}(…)`"
            ),
        )

    def shock_edge(self, shock: str):
        """The edge a shock is drawn on, as the pair of perches it joins: the
        input perch of the first block, in textual order, that lists the shock
        on its input side, and that block's output perch; for a shock no
        header lists, the edge its declaration is assigned to
        (`check_distributions`). None when neither places it."""
        assigned = getattr(self, "shock_edges", {}).get(shock)
        if assigned is not None and all(p is not None for p in self.side_perches[assigned]):
            return self.side_perches[assigned]
        for block_id, _ in self.blocks:
            listed = any(l.stem == shock for l in self.side_entries(block_id, INPUT))
            perch_from, perch_to = self.side_perches[block_id]
            if listed and perch_from is not None and perch_to is not None:
                return (perch_from, perch_to)
        return None

    def check_forward_reading(
        self, spelling, perch, left, address, integrated=frozenset()
    ) -> None:
        """A field at another perch is read at the left side's perch through
        the stage's forward blocks from the one perch to the other, and only
        when no shock is drawn on the way.

        The perches of a stage run arrival, decision, continuation, and the
        forward blocks run that way only, so a field at a perch *before* the
        left side's has no reading there whatever blocks the stage writes:
        that is `w[>] = w`, which asks for the decision state as a function
        of the continuation state. A field at a perch *after* the left
        side's is read through the forward blocks between the two; a stage
        that does not write one of them is incomplete, and no reading is
        checked in it."""
        if not _precedes(left, perch):
            raise self.error(
                "forward-composite",
                address,
                (
                    f"the line is read at the {left} perch and mentions "
                    f"{spelling_text(spelling)}, a field at the {perch} perch, "
                    f"which comes before it: a stage runs arrival, decision, "
                    f"continuation, so a line at the {left} perch is a function "
                    f"of the {left} state, and the file defines the {left} state "
                    f"from the {perch} state, not the {perch} state from the "
                    f"{left} state. Write the {left}-perch field the law of motion "
                    f"defines, or state the equation at the {perch} perch"
                ),
            )
        chain = forward_blocks_between(left, perch, self)
        if chain is None:
            return
        shocks = [
            (shock, block)
            for block in chain
            for shock in self.input_shocks(block)
            if shock not in integrated
        ]
        if shocks:
            drawn = ", ".join(sorted({shock for shock, _ in shocks}))
            first, _ = shocks[0]
            raise self.error(
                "shock-observed",
                address,
                (
                    f"the line is read at the {left} perch and mentions "
                    f"{spelling_text(spelling)}, a field at the {perch} perch; the "
                    f"edge from the {left} perch to the {perch} perch draws "
                    f"the shock {drawn}, so the value of "
                    f"{spelling_text(spelling)} is not known at the {left} perch. "
                    f"Write the expectation over it, `E_{{{first}}}(…)`"
                ),
            )

    def input_shocks(self, block_id: str) -> list:
        """The shocks a block lists on its input side, in header order."""
        return [
            l.stem
            for l in self.side_entries(block_id, INPUT)
            if self.field_roles.get(l.stem) == SHOCK
        ]

    def backward_block_edge(self, block_id):
        """The (source perch, target perch) of the edge a backward block
        that writes values integrates over — its output perch, then its
        input perch — or None for any other block. The fold checks the
        shocks of that edge."""
        perch_from, perch_to = self.side_perches[block_id]
        outputs = self.side_entries(block_id, OUTPUT)
        if (
            perch_from in PERCHES
            and perch_to in PERCHES
            and _precedes(perch_to, perch_from)
            and outputs
            and all(self.field_roles.get(l.stem) in VALUE_ROLES for l in outputs)
        ):
            return (perch_to, perch_from)
        return None

    def check_bound_names(self, block_id, multiplier) -> None:
        """The names the bound of a declared multiplier reads: a state of
        the continuation perch, a multiplier of the block, a parameter, a
        number or `inf`. Any other field — a control, a state of the
        decision or the arrival perch, a value, a shock, a marked candidate
        — is refused under `multiplier-declaration`, and a name the stage
        does not declare under `name-in-scope`. This rule, and not
        `check_names_in_scope`, governs the bound of a declaration."""
        continuation_states = {
            listing.stem
            for listing in self.listings
            if listing.wire_type is not None
            and listing.wire_type.perch == CONTINUATION
            and self.field_roles.get(listing.stem) == STATE
        }
        own = {stem for stem, held in self.multipliers.items() if held.block == block_id}
        for expression in bound_expressions(multiplier.bound):
            for spelling in free_names(expression, multiplier.address, self):
                stem, mark = spelling
                if mark is None and stem == "inf":
                    continue
                if mark == CONTINUATION and stem in own:
                    continue
                if mark in (None, CONTINUATION) and stem in continuation_states:
                    continue
                declared = self.declared_as(stem)
                if mark is None and declared in ("parameter", "function", "space"):
                    continue
                if declared is None:
                    raise self.error(
                        "name-in-scope",
                        multiplier.address,
                        (
                            f"the bound of the multiplier {multiplier.stem!r} "
                            f"mentions {spelling_text(spelling)}, which the stage "
                            f"does not declare: it is no field, parameter, shock, "
                            f"named space or function of the stage. Declare it, or "
                            f"write a continuation state or a parameter in its place"
                        ),
                    )
                role = self.field_roles.get(stem, STATE) if declared == "field" else declared
                if role == MULTIPLIER:
                    what = (
                        f"the multiplier {stem!r}, which a bound writes `{stem}[>]`"
                        if stem in own
                        else f"a multiplier of block {self.multipliers[stem].block!r}"
                    )
                elif role == CONTROL:
                    what = "the candidate of a control" if mark else "a control"
                elif declared == "field":
                    perches = mark or " and ".join(
                        sorted(
                            {
                                listing.wire_type.perch
                                for listing in self.listings
                                if listing.stem == stem and listing.wire_type is not None
                            }
                        )
                    )
                    what = f"a {role} of the {perches} perch"
                else:
                    what = f"a {role}"
                raise self.error(
                    "multiplier-declaration",
                    multiplier.address,
                    (
                        f"the bound of the multiplier {multiplier.stem!r} names {stem!r}, "
                        f"written {spelling_text(spelling)}, {what}; the bound of a "
                        f"declared multiplier names continuation states, multipliers of "
                        f"block {block_id!r}, parameters, numbers or `inf` "
                        f"(AMD-SG-035 D11). Write the bound on a continuation state, or state "
                        f"the condition on a line of the block with its own clause"
                    ),
                )

    # -- the lookups the construction and the typing walk read --

    def listed_identities(self, side: str) -> list:
        """The wire types listed on every side of kind `side`, each once, in
        first-listing order."""
        out = []
        for listing in self.listings:
            if (
                listing.side == side
                and listing.wire_type is not None
                and listing.wire_type not in out
            ):
                out.append(listing.wire_type)
        return out

    def first_listing_address(self, wire_type: Identity) -> str:
        """The address of the block whose header first lists a wire type."""
        for listing in self.listings:
            if listing.wire_type == wire_type:
                return listing.address
        raise KeyError(wire_type)

    def block_between(self, perch_from: str, perch_to: str) -> str | None:
        """The one block from `perch_from` to `perch_to` that writes a state,
        going forward, or a value, going backward; None where there is none.

        A policy block whose outputs are controls alone writes no value, so it
        is not one. Several such blocks are refused under `forward-composite`:
        the construction never chooses one by its place in the file.
        """
        candidates = self.blocks_between(perch_from, perch_to)
        if len(candidates) > 1:
            raise self.error(
                "forward-composite",
                candidates[0],
                f"the {perch_from} to {perch_to} relation has several candidate "
                f"builders: {', '.join(candidates)}; specify one unambiguous relation",
            )
        return candidates[0] if candidates else None

    def blocks_between(self, perch_from, perch_to):
        """Builders with the requested direction and output role, in source
        order."""
        roles = (STATE,) if _precedes(perch_from, perch_to) else VALUE_ROLES
        return [
            block_id
            for block_id, _ in self.blocks
            if self.side_perches[block_id] == (perch_from, perch_to)
            and any(self.field_roles[l.stem] in roles for l in self.side_entries(block_id, OUTPUT))
        ]

    def callable_definition(self, name):
        """The definition a name calls, through its function aliases: `g := f`
        answers the definition of `f`, whose argument list `g` has; a callable
        an operator defines, `g := Inv(f)`, answers its own definition, whose
        argument list is not written. None for a name no definition defines,
        and for a cycle of aliases, which the check under `definition-order`
        refuses.
        """
        seen = set()
        while name in self.functions and name not in seen:
            seen.add(name)
            definition = self.functions[name]
            body = definition.body
            if (
                definition.slot != "body"
                and isinstance(body, terms.Sym)
                and isinstance(body.symbol, terms.Constant)
                and body.symbol.name in self.functions
            ):
                name = body.symbol.name
            else:
                return definition
        return None

    def exogenous(self) -> tuple:
        """The shocks in declaration order: by the position of the item that
        first introduces each — its top-level declaration when it has one,
        else its distribution declaration or the listing that carries
        `!shck` — and, within one item, by its place among the coordinates
        or subjects."""

        def introduced(name):
            keys = [self.shocks[name]]
            if name in self.scalar_keys:
                keys.append(self.scalar_keys[name])
            return min(keys)

        return tuple(sorted(self.shocks, key=introduced))

    # -- 10. the annotation of the working stage --
    # written after the typing call

    def declarations_record(self, fields) -> dict:
        roles = self.field_roles
        # a site of the fields table is (where, side, the set declared there),
        # and the set is the retained term the declaration writes, which is
        # what `check_declared_sets` compares one site with another by
        fields_table = {
            wire_type: (
                field.perch,
                roles[field.stem],
                sets.meet(field.domain_terms),
                tuple(
                    (where, side, term)
                    for (where, side), term in zip(field.sites, field.domain_terms)
                ),
            )
            for wire_type, field in fields.items()
        }
        names = self.field_names()
        with_role = lambda role: tuple(n for n in names if roles[n] == role)
        decision_fields = [f.stem for f in fields.values() if f.perch == DECISION]
        symbols = {
            "spaces": tuple(self.spaces),
            "arvl_states": self.side_members(ARRIVAL, INPUT),
            "dcsn_states": tuple(n for n in decision_fields if roles[n] == STATE),
            "cntn_states": self.side_members(CONTINUATION, OUTPUT),
            "controls": with_role(CONTROL),
            "exogenous": self.exogenous(),
            "values": with_role(VALUE),
            "parameters": tuple(self.parameters()),
            "settings": (),
            "functions": tuple(self.functions),
        }
        assert tuple(symbols) == SYMBOL_GROUPS
        return {
            "name": self.stage,
            "kind": STANDARD,
            "metadata": {key: value for key, (value, _) in self.metadata.items()},
            # each named space as the retained set term it is defined as, which
            # is the form `check_declared_sets` resolves a name through
            "spaces": {name: self.space_terms[name] for name in self.spaces},
            "parameters": self.parameters(),
            "definitions": {
                name: (d.params, d.printed, d.operators) for name, d in self.functions.items()
            },
            "definition_order": self.definition_order,
            "block_order": tuple(block_id for block_id, _ in self.blocks),
            "laws": {subjects: declaration.printed for subjects, declaration in self.laws.items()},
            "fields": fields_table,
            "symbols": symbols,
        }

    def side_members(self, perch_word: str, side: str) -> tuple:
        """The field names on every side of kind `side` whose perch —
        written or inferred — is `perch_word`, each once, in textual order:
        the symbol groups `arvl_states` (the arrival input sides) and
        `cntn_states` (the continuation output sides). A shock is a member of
        no side's information set."""
        out = []
        for listing in self.listings:
            perches = self.side_perches[listing.block_id]
            side_perch = perches.input if side == INPUT else perches.output
            if (
                listing.side == side
                and side_perch == perch_word
                and listing.stem not in out
                and self.field_roles.get(listing.stem) != SHOCK
            ):
                out.append(listing.stem)
        return tuple(out)


def _header_entry(listing, perch_word=None) -> str:
    """One listing of a header as a corrected header writes it: the field as
    written, then its set, its role word and its own perch word, or the
    `perch_word` given where it carries none."""
    parts = [listing.domain] if listing.domain is not None else []
    if listing.role is not None:
        parts.append("!" + ROLE_WORD[listing.role])
    if (listing.own_perch or perch_word) is not None:
        parts.append(f"!{listing.own_perch or perch_word}")
    return listing.text + (" : " + " @ ".join(parts) if parts else "")


def _precedes(first, second) -> bool:
    """Whether the perch `first` comes before the perch `second` in the order
    of a stage: arrival, decision, continuation."""
    return PERCHES.index(first) < PERCHES.index(second)
