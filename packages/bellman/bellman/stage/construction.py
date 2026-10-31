"""The construction of a stage from a generated Bellman-SYM file term.

`make_stage(term, spans)` takes the `FILE` term of one stage — the result of
parsing its `.bl` source (`bellman.syntax.lower.parse_with_spans`) or of
decoding a saved AST (`bellman.syntax.decode.from_json`) — and returns the
`ElaboratedStage` of one occurrence of that stage: its definitions, its four
graphs and its bindings, and nothing of the term. `spans` is the source-span
table of a fresh parse, so that a refusal can cite `file:line:column`, or
None for a decoded term, in which case a refusal cites the item's term
address (`bellman.syntax.lower.item_addresses`). Neither the term nor the
table is kept on the stage.

The pipeline, in the order `make_stage` calls it:

1. the arguments are checked, and the stage's name is read from its one
   `@stage` line;
2. the declaration pass, `Declarations` of `typing/declarations.py`, reads
   and checks every top-level item and every block header in nine calls;
3. `_field_sorts` gives the sort of every field wire: its perch, its role and
   the meet of the sets declared for it;
4. `_builder_boxes` makes one box per block, in the order the file writes the
   blocks, each holding its statement records and its authored nodes;
5. `_stage_hypergraph` wires the boxes into one hypergraph, one spider per
   field, its inputs the continuation values and the arrival state and its
   outputs the arrival values and the post-decision state, and checks that
   every field is produced and consumed and that every output is defined;
6. `_latent_shock_sorts` adds the sorts of the shocks a law draws and no
   block lists; the typing, `type_stage` of `typing/context.py`, types every
   line and answers the sort of every wire; `_typed_boxes` puts the typed
   records on the boxes of the working value, `WorkingStage` of
   `native/versions.py`;
7. the fold, `fold_stage_file` of `fold/stage_fold.py`, reads each block's
   lines into its builder's operator rows, the construction table;
8. `construct_graphs` of `graphs/builders_graphs.py` builds the two initial
   diagrams and the two builders graphs from the table;
9. the stage is constructed from its name, its metadata, the definitions
   table, the four graphs, empty bindings and an empty provenance, and its
   `__post_init__` freezes each stored graph.

Refusals and their order. A file that breaks a construction rule is refused
with a `ConstructionError` (`bellman.refusals`) naming the position of the
authored item responsible, that item's term address, and the rule it does not
satisfy; a form outside the standard-stage construction is refused with a
`NotConstructed`, which is both a `ConstructionError` and a
`NotImplementedError`. The checks run in this order, and each one runs over the
whole file before the next begins, so that a later check may assume what the
earlier ones establish. (1) The arguments: `term` is a `FILE` and `spans` is a
span table or None — a `TypeError`, since these are the caller's arguments and
not the modeler's file. (2) The stage's name, from the one `@stage` line, so
that every wire type and every later refusal can name the stage. (3) The
top-level items and the block headers, in textual order: each item's form, the
sets and role and perch words of every declaration, and the two sides of every
block header; the body lines of each block are collected and not yet read. (4)
One name, one meaning: no name is two of a field, a function, a named space, a
shock, and a parameter, none is the name of a numerical operator, and only a
shock is both declared at the top level and listed on the side of a block. (5)
The perch and wire type of every listed field, and the perch of every side;
from here a field's identity, its role, and its domain are known. (6) The
definitions: their dependency order, the functions they apply, and the names
their bodies mention. (7) The forms this module does not construct, the
textually first refused. (8) The lines of every block, in textual order: the
statement ids of a block are distinct, the selections take coordinates of
declared families, every name a line mentions is in scope where it stands, and
a line that names no operator mentions fields its left side's perch can read.
(9) The boxes, the statement records, and the wiring: every dotted id names
an operative line of its policy block, at most one implicit statement per
output field, every field produced and consumed, every output defined by
a line of its block, and every grid line in agreement with the law of motion
solved for its decision state. (10) The typing, the fold, the graphs and the
returned stage.
The stage object is constructed last and from finished parts, so a refusal at
any step returns nothing and changes nothing.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import NamedTuple

from discopy.frobenius import Box, Ty

from bellman.fold.block_lines import property_owners
from bellman.fold.stage_fold import fold_stage_file
from bellman.graphs.builders_graphs import construct_graphs
from bellman.native.frozen import freeze
from bellman.native.hypergraphs import BellmanHypergraph
from bellman.native.identity import Identity
from bellman.native.records import (
    Bindings,
    BlockData,
    Line,
    NodeData,
    OperatorOccurrence,
    Sort,
    with_identity,
)
from bellman.native.versions import WorkingStage
from bellman.refusals import ConstructionError, construction_error
from bellman.stage.term_operations import relation_of
from bellman.syntax import terms
from bellman.syntax.lower import item_addresses, span_at
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    ALIAS,
    ARRIVAL,
    CONTINUATION,
    CONTROL,
    DECISION,
    DOC,
    NODE,
    OUTPUT_LINE,
    PERCHES,
    SHCK,
    STAGE_BUILDERS,
    STATE,
    VALUE_ROLES,
)
from bellman.typing import ranges, sets
from bellman.typing.context import type_stage
from bellman.typing.declarations import STANDARD, Declarations
from bellman.typing.line_unknowns import (
    CONSTRAINED_OPTIMUM,
    INPUT,
    INTERIOR_ROOT,
    OUTPUT,
    annotation_entries,
    candidates_of_statement,
    forward_blocks_between,
    free_names_with_shocks,
    item_kind,
    listed_identity,
    mentions_after_aliases,
    names_fields,
    occurrence_paths,
    outputs_and_unknowns,
    perch_of_spelling,
    position_text,
    span_of,
    spelling_text,
    statement_id,
    system_occurrence,
    systems_by_shared_candidate,
)

# --- the construction, and the stage's name ---


def stage_fields(term, spans):
    """The fields of the `ElaboratedStage` of the stage that `term`
    describes, by their names, which `elaborated.make_stage` constructs the
    stage from; this module does not import the stage's class, so that the
    reading of a method block (`method_blocks.read_block`) constructs its
    stage by this function without a cycle of imports.

    `term` is a `bellman.syntax.terms.FILE`; `spans` is its source-span table
    (a Mapping from term address to `SourceSpan`) for a fresh parse, or None
    for a decoded saved term. An argument of another kind — `.bl` text, a JSON
    mapping not yet decoded, a Lark tree, a YAML node — raises `TypeError`
    before anything is built. A declaration or statement that breaks a
    construction rule — a file with no `@stage` line or with two, a field
    listed with two roles, a mark disagreeing with its side, a shock placed at
    a perch, a name that is both a field and a function or space, a function
    named like an operator, a name that is both a parameter and a field, a
    cycle among definitions, an unknown selection, a name nothing declares, a
    side that lists a coordinate nothing places, two lines of one block under
    one id, a right side that depends on a shock its perch has not observed or
    on a field its perch cannot reach, a second implicit statement for one
    output, a field no block produces or none consumes, a grid line that
    disagrees with the law of motion, a form no rule reads —
    raises a `ConstructionError` (`bellman.refusals`) carrying the position of
    the item responsible, its term address, and the rule. A form this module
    does not construct (a branching block selected by a shock, a definition or
    law inside a block) raises a `NotConstructed`, which is also a
    `NotImplementedError`, after every declaration has been read. On any
    refusal no stage is returned and nothing built earlier is kept.

    The stage is made by four calls in order. The declarations and the boxes
    come first: the declaration pass reads and checks every top-level item and
    every block header, `_field_sorts` and `_latent_shock_sorts` give the sort
    of every wire, `_builder_boxes` and `_stage_hypergraph` make the
    working hypergraph, and `_check_grid_lines` compares each grid line with
    the law of motion. Then, in order, the typing call, which types every line
    of the retained term and returns the typed hypergraph with the sort of
    every wire; the fold call, which returns the construction table; the call
    of `construct_graphs`, which returns the four stored graphs; and the stage
    itself, whose `__post_init__` freezes each stored graph. The working
    value, a `WorkingStage`, is built once, after the typing call, and is
    passed to the fold and to `construct_graphs`; no call assigns an
    attribute of a value another call returned."""
    if not isinstance(term, terms.FILE):
        raise TypeError(
            f"make_stage expects a generated Bellman-SYM file term, "
            f"bellman.syntax.terms.FILE, as returned by "
            f"bellman.syntax.lower.parse_with_spans or bellman.syntax.decode.from_json; got "
            f"{type(term).__name__}{_hint(term)}"
        )
    if spans is not None and not isinstance(spans, Mapping):
        raise TypeError(
            f"spans must be the source-span table of a fresh parse, a Mapping "
            f"from term address to SourceSpan, or None for a decoded saved "
            f"term; got {type(spans).__name__}"
        )
    items = item_addresses(term)
    name = stage_name(term, items, spans)
    declarations = Declarations(name, items, spans)
    declarations.read(term)
    declarations.check_identity_collisions()
    declarations.check_names()
    fields, signatures = declarations.fields_and_header_sides()
    declarations.check_distributions()
    declarations.resolve_definitions()
    declarations.check_branches()
    declarations.refuse_unconstructed()
    declarations.check_statements()
    unread = declarations.unread_value_inputs()
    sorts = _field_sorts(declarations, fields)
    boxes = _builder_boxes(declarations, _read_signatures(signatures, unread), sorts, unread)
    hypergraph = _stage_hypergraph(declarations, fields, boxes, sorts, unread)
    _check_grid_lines(declarations)
    wire_sorts = dict(sorts)
    wire_sorts.update(_latent_shock_sorts(declarations, sorts))

    # the typing call: the typed rows of every line and the sort of every wire
    typed = type_stage(
        declarations=declarations, fields=fields, wire_sorts=wire_sorts, hypergraph=hypergraph
    )
    annotation = declarations.declarations_record(fields)
    working = WorkingStage(
        name=name,
        kind=STANDARD,
        hypergraph=_typed_boxes(hypergraph, typed.builders),
        symbols=annotation["symbols"],
        data=annotation,
        field_sorts=sorts,
        sorts=typed.sorts,
        parameter_sets={
            param: declaration.domain_term
            for param, declaration in declarations.scalars.items()
            if param in declarations.parameters()
        },
        law_terms={
            subjects: next(body for body, at in declarations.law_terms if at == law.address)
            for subjects, law in declarations.laws.items()
        },
    )
    # the fold call: the construction table
    table = _fold_stage(working=working, term=term, spans=spans)
    # the call of `construct_graphs`: the four stored graphs
    initial, builders = construct_graphs(stage=working, table=table, spans=spans)
    # the fields of the stage itself, whose `__post_init__` freezes each
    # stored graph
    return dict(
        name=working.name,
        metadata=freeze(dict(working.data["metadata"])),
        definitions=_definitions_table(table),
        initial=initial,
        _builders=builders,
        bindings=Bindings(None, None, None),
        provenance=freeze({}),
    )


def _hint(term) -> str:
    if isinstance(term, str):
        return "; parse .bl text with bellman.syntax.lower.parse_with_spans first"
    if isinstance(term, Mapping):
        return "; decode a saved AST mapping with bellman.syntax.decode.from_json first"
    return ""


def stage_name(term, items, spans) -> str:
    """The value of the term's one `@stage` metadata line."""
    stage_lines = [
        (address, item)
        for address, item in items
        if isinstance(item, terms.Metadata) and item.key == "stage"
    ]
    if not stage_lines:
        raise construction_error(
            f"the file has no '@stage' line, so the stage has no name; write "
            f"'@stage: <name>' as its first line. The term is "
            f"a FILE of {len(term.items)} items: {_kinds(term)}",
            stage=None,
            address=None,
            span=None,
            rule="stage-name",
        )
    if len(stage_lines) > 1:
        positions = ", ".join(
            f"'{item.value}' at {position_text(address, spans)}" for address, item in stage_lines
        )
        last = stage_lines[-1][0]
        raise construction_error(
            f"{len(stage_lines)} '@stage' lines name the stage: {positions}; a "
            f"stage file has exactly one, so delete all but the line that "
            f"names it",
            stage=None,
            address=last,
            span=span_of(last, spans),
            rule="stage-name",
        )
    ((address, line),) = stage_lines
    if not isinstance(line.value, str) or not line.value:
        raise TypeError(
            f"the '@stage' value at {position_text(address, spans)} must be a "
            f"non-empty string; got {type(line.value).__name__} "
            f"({line.value!r})"
        )
    return line.value


def _kinds(term) -> str:
    return ", ".join(item_kind(item) for item in term.items) or "none"


def _field_sorts(declarations, fields) -> dict:
    """The sort of every field wire: its perch, its role word, and the meet of
    the sets declared for it at its sites as a retained term."""
    roles = declarations.field_roles
    return {
        wire_type: Sort(
            wire_type,
            "field",
            perch=field.perch,
            role=roles[field.stem],
            domain=sets.meet(field.domain_terms),
        )
        for wire_type, field in fields.items()
    }


# --- the builder boxes and their records ---


def _read_signatures(signatures, unread) -> dict:
    """The block signatures with the listings of `unread` left out of their
    input sides: a value input a backward block's header lists and no line of
    the block reads is no input of the block's box, so that the block, its
    builder and the kernels' formal arguments are the same whether or not the
    header lists it (`Declarations.unread_value_inputs`; AAS, 17 October
    2026). The header stays as the file writes it, and the stage records the
    listing as a diagnostic."""
    left_out = {block_id: {l.wire_type for l in listings} for block_id, listings in unread.items()}
    return {
        block_id: (tuple(i for i in inputs if i not in left_out.get(block_id, ())), outputs)
        for block_id, (inputs, outputs) in signatures.items()
    }


def _builder_boxes(declarations, signatures, sorts, unread) -> tuple:
    """One `Box` per block, in the order the file writes the blocks. The
    four builders are told apart by the perches of their signatures
    (`STAGE_BUILDERS`), not by this order. `unread` is the answer of
    `Declarations.unread_value_inputs`, whose listings `signatures` leaves
    out and each box records."""
    return tuple(
        _builder_box(block_id, declarations, signatures, sorts, unread.get(block_id, ()))
        for block_id, _ in declarations.blocks
    )


def _builder_box(block_id, declarations, signatures, sorts, unread) -> Box:
    """The box of one block: dom and cod the tensors of the sorts of its two
    sides, data the block's record with its statements, its authored nodes,
    each holding the records folded into it, and the sorts of the value inputs
    its header lists and no line reads (`unread`), which its dom leaves out.
    The typing call gives every record its types and every node the identities
    it reads and writes."""
    inputs, outputs = signatures[block_id]
    dom, cod = Ty(*(sorts[i] for i in inputs)), Ty(*(sorts[o] for o in outputs))
    records, nodes = _statement_records(block_id, declarations)
    perch_from, perch_to = declarations.side_perches[block_id]
    data = BlockData(
        perch_from=perch_from,
        perch_to=perch_to,
        statements_outside_nodes=tuple(records),
        nodes=tuple(nodes),
        branch_labels=tuple(declarations.branch_labels.get(block_id, ())),
        unread_inputs=tuple(sorts[listing.wire_type] for listing in unread),
    )
    return with_identity(Box(block_id, dom, cod, data=data), Identity("block", address=block_id))


def _statement_records(block_id, declarations):
    """The records a block keeps at its own level, in textual order, and its
    nodes, each a `NodeData` holding the aliases folded into it and its own
    record, from the block's body
    lines: a line is a node when it carries `!node`; else documentation when
    it carries `!doc`; else an output statement when its left side names an
    output field of the block by wire type (`listed_identity`); else an alias,
    folded into the next node, or kept at the block level when no node
    follows. A line a dotted id attaches to another line as its property
    (`_property_lines`) stays at the block level, records no operator
    occurrence and names no alias, since it forms no operation. Every other
    line but a `!doc` line records its operator occurrences; an output or node
    line that is implicit records the one `solve` occurrence of the implicit
    statement, and a system of candidate statements records one `solve`
    occurrence, at its first statement (`_system_solves`)."""
    out_listings = declarations.side_entries(block_id, OUTPUT)
    properties = _property_lines(block_id, declarations)
    solves = _system_solves(block_id, declarations, properties)
    block_level, nodes, pending = [], [], []  # pending: the alias records a node folds
    aliases = {}  # lhs spelling -> right side of every earlier alias line
    implicit_seen = {}  # output wire type -> address of its implicit statement
    for ordinal, address, item in declarations.bodies[block_id]:
        core = item.core
        slack = isinstance(core, terms.Slack)
        equation = core.core if slack else core
        candidate = isinstance(equation, terms.Equation) and not names_fields(equation.lhs)
        left_fields = outputs_and_unknowns(
            equation.lhs,
            address,
            declarations,
            equation.rhs,
            relation=not isinstance(equation, terms.Equation),
        )
        left_types = tuple(listed_identity(lhs, out_listings, declarations) for lhs in left_fields)
        # an inequality whose left side is not a name states a relation and
        # names no field, so the block keeps the line and no operator
        # represents it (AMD-SG-017 §§1, 5.6)
        lhs, lhs_type = (left_fields[0], left_types[0]) if left_fields else (None, None)
        marks, tags = annotation_entries(item.annot, address, declarations)
        role = _line_role(marks, tags, left_types, declarations, address)
        held = role == DOC or address in properties
        operators = (
            ()
            if held
            else tuple(
                occurrence_paths(
                    equation.rhs, ("rhs",), slack=slack, declarations=declarations, address=address
                )
            )
        )
        if (
            not held
            and len(left_fields) == 1
            and role in (OUTPUT_LINE, NODE)
            and not operators
            and _is_implicit(equation.rhs, lhs_type, aliases, block_id, declarations, address)
        ):
            if lhs_type in implicit_seen:
                _refuse_second_implicit(
                    declarations, block_id, address, lhs, implicit_seen[lhs_type]
                )
            implicit_seen[lhs_type] = address
            if not candidate:
                operators = (_implicit_occurrence(equation, slack),)
        if candidate and role in (OUTPUT_LINE, NODE) and not operators and address in solves:
            # the first statement of a system records the system's one solve
            operators = (solves[address],)
        if held:
            # a documentary line and a property record no operator, and a
            # form in them that no construction rule reads is refused all the
            # same
            occurrence_paths(
                equation.rhs, ("rhs",), slack=slack, declarations=declarations, address=address
            )
        record = Line(
            address=address,
            ordinal=ordinal,
            role=role,
            tags=tuple(tags),
            operators=tuple(operators),
        )
        if address in properties:
            block_level.append(record)
        elif role == NODE:
            nodes.append(
                NodeData(
                    node_id=address,
                    block_id=block_id,
                    statements=tuple(pending) + (record,),
                    marks=("node",),
                    branch=None,
                )
            )
            pending = []
        elif role == ALIAS:
            pending.append(record)
        else:
            block_level.append(record)
        if not held:
            for lhs, lhs_type in zip(left_fields, left_types):
                if lhs_type is None:
                    aliases[lhs] = equation.rhs
    block_level.extend(pending)
    block_level.sort(key=lambda r: r.ordinal)
    return block_level, nodes


def _line_role(marks, tags, left_types, declarations, address):
    """The role of one line of a block: a node when it carries `!node`, which
    requires a nonempty explicit id; documentation when it carries `!doc`; a
    output statement when its left side names an output field; an alias
    otherwise."""
    if NODE in marks:
        if not any(tag.startswith("id=") and tag[3:].strip() for tag in tags):
            raise declarations.error(
                "declared-once",
                address,
                "an authored node requires a nonempty explicit id; write an id before the mark, "
                "`:: [id=<name>, !node]`",
            )
        return NODE
    if DOC in marks:
        return DOC
    if any(value is not None for value in left_types):
        return OUTPUT_LINE
    return ALIAS


def _property_lines(block_id, declarations) -> dict:
    """The lines of a block a dotted id attaches to another line as its
    property, by address, each with the address of the line it is attached to
    (`property_owners`), after the check of every dotted id the block writes.
    A line whose id is `x.y` states a property of the line `x`: it forms no
    operation of its own, and the row of `x` holds it. So `x` is a line of the
    same block, neither marked `!doc` nor itself a property, and the block is
    a policy block, whose rows alone hold properties; a dotted id that
    attaches its line to nothing is refused under `readable-form`, as is one
    in a block that writes no control."""
    body = declarations.bodies[block_id]
    properties = property_owners(address for _, address, _ in body)
    marked = {
        address
        for _, address, item in body
        if DOC in annotation_entries(item.annot, address, declarations)[0]
    }
    policy = any(
        declarations.field_roles[listing.stem] == CONTROL
        for listing in declarations.side_entries(block_id, OUTPUT)
    )
    for _, address, item in body:
        written = statement_id(item.annot)
        if written is None or "." not in str(written):
            continue
        owner = str(written).rpartition(".")[0]
        attached = properties.get(address)
        if attached is None:
            reason = f"which block {block_id!r} does not write"
        elif attached in marked:
            reason = "which is marked !doc and forms no operation"
        elif attached in properties:
            reason = "which is itself a property and forms no operation"
        elif not policy:
            reason = (
                f"in block {block_id!r}, which writes no control; a property stands on a row "
                f"of a policy block"
            )
        else:
            continue
        raise declarations.error(
            "readable-form",
            address,
            (
                f"the id {str(written)!r} attaches this line to the line {owner!r} as its "
                f"property, {reason}. A dotted id `x.y` names a property of the operative line "
                f"`x` of its policy block, which the row of `x` holds and no operation "
                f"realizes; write the id of such a line before the dot, or give this line a "
                f"plain id without a dot"
            ),
        )
    return properties


def _refuse_second_implicit(declarations, block_id, address, lhs, first):
    """The refusal of a second implicit statement for one output of a block,
    naming the first."""
    raise declarations.error(
        "one-implicit-statement",
        address,
        (
            f"block {block_id!r} has a second implicit statement for "
            f"its output {lhs.stem!r}; the first is at "
            f"{declarations.where(first)}. A block "
            f"has at most one implicit statement per output field, "
            f"since two equations in one unknown state two problems"
        ),
    )


def _implicit_occurrence(equation, slack):
    """The one `solve` occurrence an implicit statement records, in its left
    side's spelling: a constrained optimum where the line carries a clause,
    an interior root otherwise."""
    unknown = to_source(equation.lhs)
    return OperatorOccurrence(
        head="solve",
        subscripts=(unknown,),
        position=(),
        unknown=unknown,
        target=CONSTRAINED_OPTIMUM if slack else INTERIOR_ROOT,
    )


def _system_solves(block_id, declarations, properties) -> dict:
    """The one `solve` occurrence of each system of candidate statements of a
    block, by the address of the system's first statement (AMD-SG-035 §5):
    the systems are `systems_by_shared_candidate` of the candidate statements
    that are neither marked `!doc` nor among `properties`, the lines a dotted
    id attaches to another line, each with its candidates; the occurrence
    names the system's candidates in the order of the header
    (`candidates_of_statement`) and is `system_occurrence` of them. A system
    with no candidate records none."""
    members, clauses = [], set()
    for _, address, item in declarations.bodies[block_id]:
        marks, _ = annotation_entries(item.annot, address, declarations)
        equation = relation_of(item.core)
        if (
            DOC in marks
            or address in properties
            or not isinstance(equation, terms.Equation)
            or names_fields(equation.lhs)
        ):
            continue
        members.append(
            (address, outputs_and_unknowns(equation.lhs, address, declarations, equation.rhs))
        )
        if isinstance(item.core, terms.Slack):
            clauses.add(address)
    outputs = tuple(listing.wire_type for listing in declarations.side_entries(block_id, OUTPUT))
    solves = {}
    for first, (addresses, candidates) in systems_by_shared_candidate(members).items():
        # each candidate spelling by the identity of its field, so that the
        # rule of the header's order is the one
        # `candidates_of_statement` states
        identities = tuple(
            Identity(
                "field",
                stage=declarations.stage,
                field=stem,
                perch=perch_of_spelling((stem, mark), block_id, declarations),
            )
            for stem, mark in candidates
        )
        ordered = candidates_of_statement(identities, outputs, ())
        if ordered:
            solves[first] = system_occurrence(
                (identity.field for identity in ordered), bool(clauses & set(addresses))
            )
    return solves


def _is_implicit(rhs, lhs_type, aliases, block_id, declarations, address) -> bool:
    """Whether an operator-free line that defines an output of its block is
    an implicit statement (spec 0.3c §3.2): its right side — with the
    block's earlier aliases substituted — names no operator and mentions a
    field at a perch later than the left side's, and the forward blocks from
    the left side's perch to that perch read an output of this block."""
    if lhs_type is None:
        return False
    mentions, has_operator = mentions_after_aliases(rhs, aliases, address, declarations)
    if has_operator:
        return False
    outputs = {l.wire_type for l in declarations.side_entries(block_id, OUTPUT)}
    left = lhs_type.perch
    perches = {
        p
        for p in (perch_of_spelling(s, block_id, declarations) for s in mentions)
        if p is not None
    }
    return any(_forward_chain_reads(left, perch, outputs, declarations) for perch in perches)


def _forward_chain_reads(perch_from, perch_to, outputs, declarations) -> bool:
    """Whether the forward blocks from one perch to a later one
    list on an input side a wire type among `outputs`. False when there is no
    forward chain between the two perches."""
    chain = forward_blocks_between(perch_from, perch_to, declarations)
    if chain is None:
        return False
    return any(
        l.wire_type in outputs for block in chain for l in declarations.side_entries(block, INPUT)
    )


# --- the stage hypergraph and the checks of its fields ---


def _stage_hypergraph(declarations, fields, boxes, sorts, unread) -> BellmanHypergraph:
    """The stage as one hypergraph: the builder boxes in the order the file
    writes the blocks, each box's ports wired from its own dom and cod, one
    spider per wire type joining every port of that type, with dom the
    continuation values then the arrival state and cod the arrival values
    then the post-decision state, each group in first-listing order. Every
    spider carries the sort of its wire. A shock's spider joins the ports of
    the boxes that list it and no input or output of the stage: a shock is at
    no perch, so it is among neither, and the draw it stands for is an input
    of the forward builder that no box produces. A stage without a block is
    the identity on the empty type. `unread` is the answer of
    `Declarations.unread_value_inputs`, the value inputs a backward header
    lists and no line of the block reads: no box's dom holds one, and for the
    check that every field is consumed the author's listing counts as its
    consumption, since the listing is admitted and not refused (AAS, 17
    October 2026); the stage records it as a diagnostic, and a field it
    produces that the listing alone consumed stands among `unused_outputs`."""
    if not boxes:
        return BellmanHypergraph.id(Ty())
    roles = declarations.field_roles
    # a wire is a field some box's side holds: a multiplier a block body
    # declares stands in the fields table and on no side (AMD-SG-035 §5), and
    # a value input a backward header lists and no line of the block reads is
    # left out of its box's dom (`_read_signatures`; AAS, 17 October 2026),
    # so neither is a wire
    inputs = {ob.name for box in boxes for ob in box.dom.inside}
    outputs = {ob.name for box in boxes for ob in box.cod.inside}
    wired = {t: field for t, field in fields.items() if t in inputs or t in outputs}
    types = tuple(wired)
    index = {t: i for i, t in enumerate(types)}
    perch = lambda t: fields[t].perch
    role = lambda t: roles[fields[t].stem]
    dom_types = [
        t for t in types if t in inputs and perch(t) == CONTINUATION and role(t) in VALUE_ROLES
    ] + [t for t in types if t in inputs and perch(t) == ARRIVAL]
    cod_types = [
        t for t in types if t in outputs and perch(t) == ARRIVAL and role(t) in VALUE_ROLES
    ] + [t for t in types if t in outputs and perch(t) == CONTINUATION and role(t) == STATE]
    # Each box's wires are read from its own dom and cod, the products of the
    # two sides of its block; the annotation does not repeat those products.
    box_wires = tuple(
        (
            tuple(index[ob.name] for ob in box.dom.inside),
            tuple(index[ob.name] for ob in box.cod.inside),
        )
        for box in boxes
    )
    wires = (tuple(index[t] for t in dom_types), box_wires, tuple(index[t] for t in cod_types))
    # An input of the stage must be read (dom) and an output written (cod)
    # by a box; a wire type joined to no box port must not occur. Both hold
    # by construction for inputs and outputs drawn from the side listings
    # and are checked on the wiring itself.
    consumed = {s for dom_wires, _ in box_wires for s in dom_wires}
    consumed |= {
        index[listing.wire_type]
        for listings in unread.values()
        for listing in listings
        if listing.wire_type in index
    }
    produced = {s for _, cod_wires in box_wires for s in cod_wires}
    for t in dom_types:
        if index[t] not in consumed:
            raise declarations.error(
                "stage-boundary",
                declarations.first_listing_address(t),
                (f"the field {t!r} is an input of the stage but no block reads it"),
            )
    for t in cod_types:
        if index[t] not in produced:
            raise declarations.error(
                "stage-boundary",
                declarations.first_listing_address(t),
                (f"the field {t!r} is an output of the stage but no block writes it"),
            )
    _check_fields_produced_and_consumed(
        declarations, wired, dom_types, cod_types, index, consumed, produced
    )
    _check_block_outputs(declarations)
    assert set(index.values()) <= consumed | produced
    hypergraph = BellmanHypergraph(
        dom=Ty(*(sorts[t] for t in dom_types)),
        cod=Ty(*(sorts[t] for t in cod_types)),
        boxes=boxes,
        wires=wires,
        spider_types={i: Ty(sorts[t]) for t, i in index.items()},
    )
    # the identities of the inputs and outputs, not a type built from identity
    # strings: a sort does not equal the plain library object of its name
    assert tuple(ob.identity for ob in hypergraph.dom.inside) == tuple(dom_types) and tuple(
        ob.identity for ob in hypergraph.cod.inside
    ) == tuple(cod_types)
    assert hypergraph.n_spiders == len(types)
    return hypergraph


def _check_fields_produced_and_consumed(
    declarations, fields, dom_types, cod_types, index, consumed, produced
) -> None:
    """Every field of the stage is produced and consumed (spec 0.3c §2.2).

    A field is produced by the block that writes it or, among the stage's
    inputs, by what the stage receives: the continuation values a later
    stage supplies and the arrival state the connector supplies. It is
    consumed by the block that reads it or, among the stage's outputs, by
    what the stage delivers: the arrival values and the post-decision state.
    A state of a perch at which a backward block's output stands is consumed
    by that block: it is a coordinate of the value function the block
    defines, which a backward header lists no state for (AAS, 12 October
    2026), so a decision state that no forward block reads, the wealth of a
    terminal bequest stage, is consumed by the value block that stands at
    the decision perch. A shock is neither: it is drawn on the edge between two perches, so no
    block writes it and the stage does not receive it. A field that is
    neither produced nor received is a field the stage asks for and nothing
    supplies; a field that is neither consumed nor delivered is one the stage
    computes and nothing uses. Both are refused under `stage-boundary`, and
    the message names the field's perch, since the perch decides whether a
    field can be an input or an output of the stage.

    The two questions are asked of a file that writes the four builders of a
    stage — arrival to decision, decision to continuation, continuation to
    decision, and decision to arrival (spec 0.3c §4.3, "two chains of
    builders"), which cons.bl, disc.bl, port.bl, noport.bl and
    cons_savings_iid.bl all do. A file that writes fewer is a fragment: the
    field that the missing builder would write or read is missing with it, so
    a field left dangling says nothing about the file, and construction
    admits it."""
    if not all(declarations.blocks_between(*pair) for pair in STAGE_BUILDERS):
        return
    for pair in STAGE_BUILDERS:
        declarations.block_between(*pair)
    coordinate_perches = {
        declarations.backward_perches(block_id)[1]
        for block_id, _ in declarations.blocks
        if declarations.block_is_backward(block_id)
    }
    for wire_type, field in fields.items():
        if field.perch == SHCK:
            continue
        if (
            field.perch in coordinate_perches
            and declarations.field_roles.get(field.stem) == STATE
            and _placed_by_a_forward_block(declarations, wire_type)
        ):
            # a coordinate of the value function a backward block defines at
            # this perch, consumed by that block; a state only a block of the
            # backward direction writes is no coordinate and is read as before
            if index[wire_type] in produced or wire_type in dom_types:
                continue
        address = declarations.first_listing_address(wire_type)
        if index[wire_type] not in produced and wire_type not in dom_types:
            raise declarations.error(
                "stage-boundary",
                address,
                (
                    f"no block writes the field {field.stem!r} at the "
                    f"{field.perch} perch, and the stage does not receive it: the "
                    f"stage receives the continuation values and the arrival "
                    f"state, and a field at the {field.perch} perch in this "
                    f"position is neither. Write it as the output of a block, or "
                    f"list it where the stage receives it"
                ),
            )
        if index[wire_type] not in consumed and wire_type not in cod_types:
            raise declarations.error(
                "stage-boundary",
                address,
                (
                    f"no block reads the field {field.stem!r} at the "
                    f"{field.perch} perch, and the stage does not deliver it: the "
                    f"stage delivers the arrival values and the post-decision "
                    f"state, and a field at the {field.perch} perch in this "
                    f"position is neither. Read it in a block, or drop it from "
                    f"the header that lists it"
                ),
            )


def _placed_by_a_forward_block(declarations, wire_type) -> bool:
    """Whether a side of a forward block, one whose output perch is later
    than its input perch, lists the field: the arrival state the connector
    supplies and the decision and continuation states the laws of motion
    write are placed this way, and a state a backward block alone writes is
    not."""
    for listing in declarations.listings:
        if listing.wire_type != wire_type:
            continue
        perch_from, perch_to = declarations.side_perches[listing.block_id]
        if perch_from is None or perch_to is None:
            continue
        if PERCHES.index(perch_from) < PERCHES.index(perch_to):
            return True
    return False


def _check_block_outputs(declarations):
    """The check that every block defines each output its header declares,
    its equations read apart from the connectivity of its header.

    A field that has no listing must be defined by an earlier local equation.
    An implicit relation can use its declared unknown and supplied fields;
    a declared output alone never supplies its own value. A multiplier the
    block declares is a coordinate of the block's continuation grid: no input
    and no equation supplies it, and it is no output (AMD-SG-035 §5). A cycle
    among the ordinary output assignments of a block is refused, and so is an
    output no line of its block defines, under `output-defined`: every row of
    a builder is formed from a line the file writes, so a policy block that
    writes its candidate and the cash on hand at the continuation perch and
    omits the line identifying the policy with the candidate, `c = c[>]`, is
    refused, and no relation is inferred for the line it does not write."""
    for block_id, block_address in declarations.blocks:
        read = _output_equations(declarations, block_id)
        _refuse_circular_outputs(declarations, read.dependencies)
        for output in declarations.side_entries(block_id, OUTPUT):
            if output.wire_type in read.supplied:
                continue
            stem = output.stem
            instead = (
                f"; a policy block defines its policy by a line with {stem} on its left side, "
                f"the maximization `{stem} = argmax_{{…}}(…)`, a solve, or, where its lines "
                f"write the candidate at the continuation perch, the identification "
                f"`{stem} = {stem}[>]`"
                if declarations.field_roles[stem] == CONTROL
                else ""
            )
            raise declarations.error(
                "output-defined",
                block_address,
                f"block {block_id!r} declares output {output.wire_type!r}, "
                f"but its body supplies no defining equation{instead}",
            )


class _OutputEquations(NamedTuple):
    """The equations of one block as `_check_block_outputs` reads them: the
    output fields the equations supply, and the `_OutputDependency` of each
    ordinary output assignment."""

    supplied: set
    dependencies: dict


class _OutputDependency(NamedTuple):
    """The address of an ordinary output assignment and the outputs of its
    block its right side reads."""

    address: str
    outputs: set


def _output_equations(declarations, block_id):
    """The `_OutputEquations` of one block, its lines read in order, the
    lines marked `!doc` and the lines a dotted id attaches to another line
    passed over; an equation that depends on a field no input and no earlier
    equation supplies is refused."""
    inputs = declarations.side_entries(block_id, INPUT)
    outputs = declarations.side_entries(block_id, OUTPUT)
    coordinates = {
        (stem, CONTINUATION)
        for stem, multiplier in declarations.multipliers.items()
        if multiplier.block == block_id
    }
    aliases, supplied = {}, set()
    output_dependencies = {}
    body = declarations.bodies[block_id]
    properties = property_owners(address for _, address, _ in body)
    for _, address, item in body:
        marks, _ = annotation_entries(item.annot, address, declarations)
        if DOC in marks or address in properties:
            continue
        core = relation_of(item.core)
        # a candidate statement states a relation in its unknowns and defines
        # none of them, so it supplies its outputs as an implicit statement
        # does and is no step of the dependency order (AMD-SG-017 §1)
        candidate = isinstance(core, terms.Equation) and not names_fields(core.lhs)
        for lhs in outputs_and_unknowns(
            core.lhs,
            address,
            declarations,
            core.rhs,
            relation=not isinstance(core, terms.Equation),
        ):
            output = listed_identity(lhs, outputs, declarations)
            implicit = candidate or _is_implicit(
                core.rhs, output, aliases, block_id, declarations, address
            )
            dependencies = set()
            for ref, _ in free_names_with_shocks(core.rhs, address, declarations, aliases=aliases):
                stem, mark = ref
                known = declarations.declared_as(stem)
                if mark is None and known in ("parameter", "function", "space", "shock"):
                    continue
                if ref in coordinates:
                    continue
                if stem == "inf":
                    continue
                resolved = listed_identity(ref, inputs, declarations)
                if resolved is None:
                    resolved = listed_identity(ref, outputs, declarations)
                if resolved is None:
                    resolved = listed_identity(ref, declarations.listings, declarations)
                if (
                    output is not None
                    and not implicit
                    and listed_identity(ref, outputs, declarations) is not None
                    and listed_identity(ref, inputs, declarations) is None
                ):
                    dependencies.add(resolved)
                if resolved is None or (
                    resolved == output
                    and not implicit
                    and resolved not in supplied
                    and listed_identity(ref, inputs, declarations) is None
                ):
                    raise declarations.error(
                        "output-defined",
                        address,
                        f"the equation depends on {spelling_text(ref)}, but no input "
                        f"or earlier equation supplies that field; a header declaration "
                        f"does not define its value",
                    )
            if output is not None:
                supplied.add(output)
                output_dependencies[output] = _OutputDependency(address, dependencies)
            else:
                aliases[lhs] = core.rhs
    return _OutputEquations(supplied, output_dependencies)


def _refuse_circular_outputs(declarations, dependencies):
    """The refusal of ordinary output assignments of one block that depend
    circularly on one another, naming the addresses around the cycle: a
    search in depth from each assignment, in the order the block writes
    them, each output's dependencies in sorted order."""
    complete, active = set(), []

    def check_dependency(identity):
        if identity in active:
            cycle = active[active.index(identity) :] + [identity]
            addresses = [dependencies[t].address for t in cycle]
            raise declarations.error(
                "output-defined",
                addresses[0],
                f"the ordinary output assignments depend circularly on one "
                f"another: {' -> '.join(addresses)}; supply a defining "
                f"input relation or an explicit equation in declared unknowns",
            )
        if identity in complete or identity not in dependencies:
            return
        active.append(identity)
        for dependency in sorted(dependencies[identity].outputs):
            check_dependency(dependency)
        active.pop()
        complete.add(identity)

    for identity in dependencies:
        check_dependency(identity)


# --- the grid lines and the law of motion ---


def _check_grid_lines(declarations):
    """The check that every grid line agrees with the law of motion, under
    the rule `grid-line-consistency`.

    A grid line is an operative line of a block from the continuation perch
    to the decision perch whose left side is a decision state under the
    continuation mark, `m_d[>] = a + c[>]` in `cons.bl`: it gives the
    decision state at each continuation state, which the law of motion, the
    one block from the decision perch to the continuation perch, gives in the
    other direction. The law of motion is solved for the decision state at
    the candidate of each control the block writes a candidate line for,
    `c[>]`, a control without one being solved for from the other lines of
    the law of motion (`ranges.law_solved_for`); the grid line's right side
    and the law of motion so solved are compared by algebraic simplification
    with every function read as an opaque symbol (`ranges.compare_terms`),
    and a grid line that does not reduce to the law of motion so solved is
    refused, its message naming both. Where the law of motion is not solved
    so, one written in branches, one with a line that is not an equation
    defining one field, or one in which a name occurs other than once and
    affinely, no check is made and nothing is recorded."""
    laws = declarations.blocks_between(DECISION, CONTINUATION)
    if len(laws) != 1 or declarations.branch_labels.get(laws[0]):
        return
    (law_block,) = laws
    law = _law_lines(declarations, law_block)
    if law is None:
        return
    roles = declarations.field_roles
    states = {
        listing.stem
        for listing in declarations.listings
        if listing.wire_type is not None
        and listing.wire_type.perch == DECISION
        and roles.get(listing.stem) == STATE
    }
    unknowns = tuple(sorted(states | {stem for stem, role in roles.items() if role == CONTROL}))
    # an output of the law of motion is one field, spelled `a` or `a[>]`
    outputs = {_marked(stem): terms.Sym(terms.Constant(stem)) for stem, _ in law}
    declared = None
    for block_id, _ in declarations.blocks:
        if declarations.side_perches[block_id] != (CONTINUATION, DECISION):
            continue
        lines = _operative_lines(declarations, block_id)
        # a candidate line is read without its clause: `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>])`
        relations = [relation_of(core) for _, core in lines]
        candidates = {
            _continuation_stem(relation.lhs): relation.lhs
            for relation in relations
            if roles.get(_continuation_stem(getattr(relation, "lhs", None))) == CONTROL
        }
        for address, relation in lines:
            if not isinstance(relation, terms.Equation):
                continue
            coordinate = _continuation_stem(relation.lhs)
            if coordinate not in states:
                continue
            if declared is None:
                declared = _declared_sets(declarations)
            solved = ranges.law_solved_for(law, coordinate, unknowns, candidates, declared)
            if solved is None:
                continue
            written = ranges.substituted(relation.rhs, outputs)
            comparison = ranges.compare_terms(written, solved.term)
            if comparison is None or comparison.equal:
                continue
            raise declarations.error(
                "grid-line-consistency",
                address,
                _grid_line_refusal(relation, coordinate, law_block, law, solved, comparison),
            )


def _grid_line_refusal(relation, coordinate, law_block, law, solved, comparison):
    """The message refusing a grid line: the line as written, the lines of
    the law of motion that were solved and for which names, the law of motion
    solved for the decision state at the candidates, and why the two
    disagree."""
    rights = dict(law)
    lines = _listed([f"{output} = {to_source(rights[output])}" for output, _ in solved.lines])
    names = _listed([name for _, name in solved.lines])
    steps = f"its line{'s' if len(solved.lines) > 1 else ''} {lines} solved for {names}"
    at = ""
    if solved.candidates:
        noun = "candidates" if len(solved.candidates) > 1 else "candidate"
        at = f" at the {noun} " + _listed([f"{name}[>]" for name in solved.candidates])
    written, law_side = to_source(relation.rhs), to_source(solved.term)
    if comparison.functions:
        reason = (
            f"the difference {written} − ({law_side}) does not reduce to zero by algebraic "
            f"simplification; it applies the functions {', '.join(comparison.functions)}, "
            "which the check reads as opaque symbols and among which it assumes no identity"
        )
    else:
        reason = f"{written} does not reduce to {law_side} by algebraic simplification"
    solution = f"{coordinate}[>] = {law_side}"
    return (
        f"the grid line {to_source(relation)} disagrees with the law of motion of block "
        f"{law_block!r}: with {steps}{at}, the law of motion gives {solution}, and "
        f"{reason}; write the grid line as the law of motion solved for {coordinate}, "
        f"{solution}"
    )


def _listed(items):
    """Items joined as a sentence lists them: `a`, `a and b`, `a, b and c`."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _law_lines(declarations, block_id):
    """The lines of the law of motion, the block `block_id`, as pairs of an
    output's name and the right side of its line, each local name of the
    block written out; None where an output has no line of its own or
    several, or where a line is not an equation whose left side is one
    field."""
    outputs = [listing.stem for listing in declarations.side_entries(block_id, OUTPUT)]
    local, found = {}, {}
    for _, core in _operative_lines(declarations, block_id):
        name = _field_name(getattr(core, "lhs", None))
        if not isinstance(core, terms.Equation) or name is None:
            return None
        right = ranges.substituted(core.rhs, local)
        if name not in outputs:
            local[terms.Sym(terms.Constant(name))] = right
        elif name in found:
            return None
        else:
            found[name] = right
    if set(found) != set(outputs):
        return None
    return tuple((name, found[name]) for name in outputs)


def _operative_lines(declarations, block_id):
    """The operative lines of a block, each as its address and its statement
    as written, a clause included; a line marked `!doc` and a property are
    not operative."""
    body = declarations.bodies[block_id]
    properties = property_owners(address for _, address, _ in body)
    found = []
    for _, address, item in body:
        marks, _ = annotation_entries(item.annot, address, declarations)
        if DOC not in marks and address not in properties:
            found.append((address, item.core))
    return found


def _field_name(term):
    """The name of the one field a left side names, bare or marked, or
    None."""
    if isinstance(term, terms.Sym) and isinstance(term.symbol, (terms.Constant, terms.Variable)):
        return term.symbol.name
    return None


def _continuation_stem(term):
    """The name of a field written under the continuation mark, `c` of
    `c[>]`, or None."""
    if (
        isinstance(term, terms.Sym)
        and isinstance(term.symbol, terms.Variable)
        and isinstance(term.symbol.when, terms.At)
        and isinstance(term.symbol.when.side, terms.Continuation)
        and term.symbol.shift == 0
    ):
        return term.symbol.name
    return None


def _marked(stem):
    """The name `stem` under the continuation mark, `a[>]`."""
    return terms.Sym(terms.Variable(stem, terms.At(terms.Continuation()), 0))


def _declared_sets(declarations):
    """The set each parameter and field name is declared with, a named space
    written out as the set it names, from which the solution of a law of
    motion reads whether a coefficient is nonzero."""
    names = set(declarations.scalars) | {listing.stem for listing in declarations.listings}
    found = {}
    for name in names:
        declared = declarations.declared_set_of(name)
        if isinstance(declared, terms.Named) and declared.name in declarations.space_terms:
            declared = declarations.space_terms[declared.name]
        found[name] = declared
    return found


# --- the sorts of the shocks, the typed boxes, the fold, the definitions ---


def _latent_shock_sorts(declarations, sorts) -> dict:
    """The sort of every shock with a declared distribution that no block
    header lists, such as the parent ν of `Ψ ~ LogNormal(ν, σ_Ψ)`
    (AMD-SG-009 §2): a shock at no perch, with the set its top-level
    declaration writes. It types the wire of a node that reads the shock and
    is no wire of a builder signature."""
    found = {}
    for name in declarations.law_of:
        identity = Identity("field", stage=declarations.stage, perch=SHCK, field=name)
        if identity not in sorts:
            found[identity] = Sort(
                identity,
                "field",
                perch=SHCK,
                role="shock",
                domain=declarations.declared_set_of(name),
            )
    return found


def _typed_boxes(hypergraph, builders):
    """The working hypergraph with the typed rows on every builder box: each
    box is made again with the record the typing call returned for it, and the
    wiring of the stage hypergraph is unchanged."""
    boxes = []
    for box in hypergraph.boxes:
        typed = builders[box.name]
        data = dataclasses.replace(
            box.data,
            statements_outside_nodes=typed.statements_outside_nodes,
            nodes=typed.nodes,
        )
        boxes.append(with_identity(Box(box.name, box.dom, box.cod, data=data), box.identity))
    return BellmanHypergraph(
        dom=hypergraph.dom,
        cod=hypergraph.cod,
        boxes=tuple(boxes),
        wires=hypergraph.wires,
        spider_types=hypergraph.spider_types,
        offsets=hypergraph.offsets,
    )


def _fold_stage(*, working, term, spans):
    """The construction table of a `WorkingStage`: the fold of the statements
    of `term` with the typing context the `WorkingStage` carries.

    A refusal of the fold is positioned at the line it names, or at the
    top-level item whose file position a definition record gave it as its
    address (AMD-SG-017 §4)."""
    try:
        return fold_stage_file(term, working, spans)
    except ConstructionError as error:
        span = span_at(error.address, spans) if error.line is None else None
        if span is None:
            raise
        raise construction_error(
            error.message,
            stage=error.stage,
            address=error.address,
            span=span,
            rule=error.rule,
            error_class=type(error),
        ) from None


def _definitions_table(table) -> dict:
    """The definitions of the stage, an ordered mapping from each identity to
    its record, read from the construction table."""
    definitions = {}
    for record in table.definitions:
        if record.identity in definitions:
            raise ValueError(
                f"the definitions table holds two records of the identity {record.identity!r}"
            )
        definitions[record.identity] = record
    return definitions
