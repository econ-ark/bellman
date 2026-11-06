"""The kernel a primitive operator applies, read and compiled
(AMD-SG-007 §§2, 3.1).

`kernel` answers a `Kernel`: the text after `applies` in a box's printed card —
the complete law of motion of a pullback or a push-forward, the segment of the
value aggregator an aggregation applies, the distribution an expectation
integrates against — with the records of the definitions table the operator
refers to under `origins` (AMD-SG-020 §3.2). Where the kernel is an explicit
function, the record also holds `python`, the source text of one plain Python
function written from the retained terms, never from a printed line, with the
parameters it reads and the values the calibration binds to them; of a row
whose output is its own unknown, that function is the explicit side its
relation holds, where the relation holds one (`grains.explicit_side`).
`compile_kernel` executes that text and answers the function it defines,
which reads its parameters as arguments and refers to no stage.
The records between the kernel and its text — `_KernelRecord` and
`_KernelParts` — carry the arguments, the outputs and the retained terms one
kernel is made of; they stand in `kernel_records`. `affine` says whether an
aggregation's map is affine in its value inputs, and the form across the
expectation is written from it.
"""

from __future__ import annotations

import dataclasses
import functools
import itertools
import keyword
import linecache
import math
import re
import unicodedata
import weakref
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import NamedTuple

from bellman.display.printed_records import tuple_text
from bellman.distributions.conditionals import conditional_texts
from bellman.fold.conditions import conditional_distribution_of, edge_drawing
from bellman.fold.stage_names import StageNames
from bellman.fold.wire_terms import (
    affine_in,
    coordinate_declared_set,
    is_wire_symbol,
    label_case,
    term_nodes,
)
from bellman.native.identity import Identity
from bellman.native.labels import function_field, wire_spelling
from bellman.native.provenance import package_version, source_file
from bellman.native.versions import kept_answer
from bellman.refusals import ConstructionError, construction_error
from bellman.stage.boxes import operator_target, origins, row_at, rows_of
from bellman.stage.defining_expressions import section_identity, wire_name
from bellman.stage.grains import (
    construction_table,
    answers_function_set,
    block_id_of,
    explicit_side,
    is_relation,
    wire_table,
)
from bellman.stage.kernel_records import (
    derivative_kernel,
    aggregator_kernel,
    distribution_arguments,
    is_kernel_output,
    kernel_output_name,
    kernel_record,
    law_of_motion_kernel,
    marked_field,
    spelling,
    stems_of,
)
from bellman.stage.stage_answers import field_role
from bellman.syntax import terms as T
from bellman.syntax.source import distribution_subject_text, to_source
from bellman.syntax.vocabulary import PERCH_MARK
from bellman.typing import sets

# --- the kernel of an operator, as text and compiled ---


class _NamedPiece(NamedTuple):
    """The name of a derivative piece, which the writer of a kernel's text
    reads as it reads a box's name."""

    name: str


def derivative_piece(stage, box):
    """The Evaluation row, the entry of its `derivatives` and the Aggregation
    row of the same builder that a derivative piece target names,
    `<line id>:Derivative:1` or `<line address>:Derivative:1`,
    `marginal:Derivative:1` for the line `D_{m_d}V = 𝑑𝑢(c) :: [id=marginal]`
    (AMD-MB-001 §4.3; decision MB-A14); None where `box` names no such
    piece."""
    if not isinstance(box, str):
        return None
    parts = box.rsplit(":", 2)
    if len(parts) != 3 or parts[1] != "Derivative" or parts[2] != "1":
        return None
    wanted = parts[0]
    for row in construction_table(stage).primitive_rows:
        if row.kind != "Evaluation":
            continue
        for entry in row.derivatives:
            address = entry[2]
            if wanted not in (address, address.split(".", 1)[-1]):
                continue
            aggregation = next(
                held
                for held in rows_of(stage, row.builder)
                if held.kind == "Aggregation" and set(held.outputs) & set(row.inputs)
            )
            return row, entry, aggregation
    return None


def derivative_piece_addresses(stage, builder):
    """The derivative pieces of the builder `builder`, each by its line's full
    address, `<line address>:Derivative:1`, one per entry of its Evaluation
    rows' `derivatives`, in row order. An address names one line of the
    stage, where a line's id alone names a line of every block that uses it,
    so `kernel` and `compile_kernel` resolve an address to this builder's
    piece."""
    return tuple(
        f"{entry[2]}:Derivative:1"
        for row in rows_of(stage, builder)
        if row.kind == "Evaluation"
        for entry in row.derivatives
    )


def _derivative_kernel(stage, box, piece):
    """The `Kernel` of a derivative piece: its printed lines, arguments and
    output, and its Python text where the right side holds forms the text
    writes."""
    spec = derivative_kernel(stage, *piece)
    named = _NamedPiece(box)
    try:
        written = _python_text(stage, named, spec)
    except ConstructionError as error:
        if error.rule != "kernel-form":
            raise
        written = None
    parameters = () if written is None else written.parameters
    values = stage.bindings.calibration
    return Kernel(
        "\n".join(spec.lines),
        (),
        arguments=_kernel_arguments(spec),
        outputs=spec.outputs,
        python=None if written is None else written.source,
        parameters=parameters,
        parameter_values=None if values is None else tuple(values[name] for name in parameters),
        integrated=spec.integrated,
    )


def kernel(stage, box, *, across_expectation=False):
    """The kernel a primitive operator box applies, as a `Kernel`: exactly the
    text after `applies` in the box's printed card, with the definition records
    the box refers to under `origins` (AMD-SG-007 §§2, 3.1; AMD-SG-020 §3.2).
    For a pullback or a push-forward it is the complete g of the associated
    forward builder, for an aggregation the G segment the box applies with its
    value arguments before its coordinates, for an expectation or an extension
    the distribution it integrates or extends by, for an evaluation or a
    policy insertion the policy and the coordinate it replaces, for a
    sub-builder's evaluation the identity, for an `Argmax` its objective,
    choice and feasible set. Of a row whose output is its own unknown
    (`grains.is_relation`) it is the G segment of the explicit side where the
    relation holds one (`grains.explicit_side`), the relation remaining the
    row's rule, and otherwise the relation and its unknowns: the
    identification, a pullback of the policy along the coordinate function
    of the grid, applies no law of motion. `box` is a primitive box of this
    version or its unambiguous name; any other target is refused under
    `kernel-target`. Where the kernel is an explicit function, the record
    holds its Python text under `python`, the parameters that function reads
    under `parameters` and their values under `parameter_values`, None on a
    symbolic version. Of a pullback along the section of a branching law at
    one label, the record holds that section's kernel under `section`
    (`_section_kernel`). With `across_expectation`, the symbolic rewrite of
    an affine aggregation across the expectation that feeds it (AMD-SG-005
    §3), not a kernel."""
    piece = derivative_piece(stage, box)
    if piece is not None:
        return _derivative_kernel(stage, box, piece)
    target, entry = operator_target(stage, box, "kernel")
    row = row_at(stage, target, entry)
    if across_expectation:
        return Kernel(_across_expectation(stage, target, row), origins(stage, target))
    # the kernel is what the box applies; the feasible set of a control, which
    # the `applies` block also carries, is a condition and not part of it
    spec = None if answers_function_set(stage, row) else kernel_record(stage, row)
    written = _text_or_none(stage, target, row)
    parameters = () if written is None else written.parameters
    values = stage.bindings.calibration
    return Kernel(
        "\n".join(_kernel_lines(stage, target, row)),
        origins(stage, target),
        arguments=_kernel_arguments(spec),
        outputs=() if spec is None else spec.outputs,
        python=None if written is None else written.source,
        parameters=parameters,
        parameter_values=None if values is None else tuple(values[name] for name in parameters),
        section=_section_kernel(stage, target, row, spec),
    )


def _section_kernel(stage, target, row, spec):
    """The kernel of the section a pullback of one branch composes with, the
    law of motion read at the row's label, named as the card's `Where`
    section names it, `𝑔_keep≻` (`section_identity`), as a `Kernel` with the
    box's origins and no Python text; None where the row reads no section or
    its kernel is no law of motion (unit K of model interface spec 0.4, Task
    14; decision K-I203)."""
    if spec is None or spec.letter != "g" or getattr(row, "section", None) is None:
        return None
    letter = section_identity(StageNames(stage), row.builder, row.section).field
    section = law_of_motion_kernel(stage, row.definition, row.section, letter)
    return Kernel(
        "\n".join(section.lines),
        origins(stage, target),
        arguments=_kernel_arguments(section),
        outputs=section.outputs,
    )


def compile_kernel(stage, box):
    """The kernel of a pullback, a push-forward or an aggregation box as one
    plain Python function (AMD-SG-007 §3.1; AMD-SG-005 §2a), the function the
    text `kernel(stage, box).python` defines: the complete g of a pullback or
    a push-forward, the G segment of an aggregation, and of a row whose output
    is its own unknown the explicit function its relation holds
    (`grains.explicit_side`), `𝑑𝑢𝑖𝑛𝑣 ∘ 𝑑𝑉≻` of `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>])
    ⟂ a >= 0` with or without the clause; the relation, its clause included,
    remains the row's rule and is no part of the function.
    Its arguments are those of the printed kernel, in its order, a formal
    unused argument included, then each parameter the kernel reads, directly
    or through a named function, in declaration order, so that a caller
    passes the values at each call, `G(v, m_d, c, *kernel.parameter_values)`,
    and a new calibration needs no new function; a symbolic version compiles
    too. The named functions the kernel calls are inner functions of it, and
    NumPy is reached by `np` alone. With array arguments it follows NumPy
    broadcasting, a value declared on a product of n sets carrying its n
    components on its last axis; it checks no declared set, shape or label.
    It returns one output as it is and several as a tuple. Retained
    arithmetic and calls to closed-form named functions, also through an
    alias of a function's name, are written through their definitions, and an
    expectation over a label shock as its weighted sum; a symbolic derivative
    or another form the text cannot write is refused under `kernel-form`, and
    under `kernel-target` a box with no explicit function: an `Argmax`, an
    expectation, an evaluation, a policy insertion, an extension, and a
    relation with no explicit side, the identification, whose law of motion
    is not compiled, and a joint solve's residual system among them.
    The text is executed in a fresh namespace that holds `np` alone and is
    entered in `linecache`, so that `inspect.getsource` prints the function,
    cloudpickle saves it and `numba.njit` compiles it; nothing is stored on
    the stage or the box, and the printed kernel is never parsed."""
    piece = derivative_piece(stage, box)
    if piece is not None:
        return _function_of(_python_text(stage, _NamedPiece(box), derivative_kernel(stage, *piece)))
    target, entry = operator_target(stage, box, "compile")
    row = row_at(stage, target, entry)
    spec = _function_record(stage, row)
    if spec is None:
        # a relation refused here can be a pullback or an aggregation, so its
        # remedy names a row that maps its inputs to its output: the first
        # row of the same block whose relation has an explicit side, where
        # the block holds one, and no row otherwise
        if is_relation(row):
            what = (
                f"{target.name!r} states a relation its output satisfies, and no side of the "
                "relation is an explicit function of the row's inputs; its kernel"
            )
            example = next(
                (
                    held
                    for held in rows_of(stage, block_id_of(target))
                    if explicit_side(stage, held) is not None
                ),
                None,
            )
            remedy = "or compile a row that maps its inputs to its output"
            if example is not None:
                remedy = (
                    f"{remedy}, such as {example.identity}, whose relation has an explicit side"
                )
        else:
            what = f"{target.name!r} is a {row.kind} box whose kernel"
            remedy = "or compile a pullback, push-forward or aggregation box"
        raise construction_error(
            f"stage {stage.name!r}: compile evaluates the explicit numerical kernels g and G, and "
            f"{what}, {'; '.join(_applied_lines(stage, target, row))}, has no callable "
            "representation (AMD-SG-007 §3.1, rule kernel-target); inspect it with "
            f"kernel(stage, box), {remedy}",
            stage=stage.name,
            address=row.statements[0] if row.statements else row.builder,
            span=None,
            rule="kernel-target",
            file=source_file(stage),
        )
    return _function_of(_python_text(stage, target, spec))


class Kernel(str):
    """The kernel a primitive operator applies, displayed as text.

    `origins` holds its defining records: the law of motion, value aggregator,
    distribution declaration or the policy's defining lines, as appropriate.
    `arguments` holds ordered argument-name and set-term pairs, and `outputs`
    the output names, for a law of motion or value aggregator; otherwise both
    are empty. Where the kernel is an explicit function, `python` is the
    source text of one plain Python function of it, `parameters` the names of
    the parameters that function reads after the kernel's arguments, in
    declaration order, and `parameter_values` the values the calibration of
    the version binds to them, in that order, None on a symbolic version;
    `python` is None and `parameters` empty where the kernel is no explicit
    function or holds a form the text cannot write. For a pullback along the
    section of a branching law at one label, `section` holds that section's
    kernel, `𝑔_keep≻`, as a `Kernel` of text, origins, arguments and outputs
    with no Python text, since `compile_kernel` compiles the complete law;
    `section` is None for every other operator (`law_of_motion_kernel`). The
    record remains a string, holds text, names and numbers and no reference
    to the stage, and no printed line need be parsed.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §2."""

    def __new__(
        cls,
        text,
        origins=(),
        arguments=(),
        outputs=(),
        python=None,
        parameters=(),
        parameter_values=None,
        section=None,
        integrated=(),
    ):
        made = super().__new__(cls, text)
        made.origins = tuple(origins)
        made.arguments = tuple(arguments)
        made.outputs = tuple(outputs)
        made.python = python
        made.parameters = tuple(parameters)
        made.parameter_values = None if parameter_values is None else tuple(parameter_values)
        made.section = section
        # the shocks a derivative piece's integrand is integrated over, `()`
        # for every other kernel (AMD-MB-001; MB-A18)
        made.integrated = tuple(integrated)
        return made

    def __str__(self):
        return str.__str__(self)

    __repr__ = __str__


def _kernel_arguments(spec):
    """The ordered pairs of argument name and set term of a kernel, as the
    printed rule writes them (AMD-SG-021 §2.2); the set is None where the file
    declares none."""
    if spec is None:
        return ()
    return tuple(zip(spec.names, spec.argument_sets))


# --- the lines after `applies`: a box's kernel, its controls' sets ---


def _applied_lines(stage, box, row):
    """The text after `applies` in the printed card of an operator box, line by
    line: the kernel of AMD-SG-007 §2's table for the box's kind, then the
    feasible set of a control the box's wires carry, with the place it was read
    from (AMD-SG-012 §3). The `where` block holds conditions; where a condition
    came from is the box explaining itself, which is what `applies` is for."""
    return _kernel_lines(stage, box, row) + tuple(
        f"{condition}, read from {origin}" for condition, origin in _feasibility_lines(stage, box)
    )


def _kernel_lines(stage, box, row):
    """The kernel of AMD-SG-007 §2's table for the box's kind, line by line.
    A row whose output is its own unknown is read before its kind: with no
    explicit side (`grains.explicit_side`) its kernel is its relation and
    its unknowns, and with one it is the aggregation of that side."""
    table = stage.definitions
    kind = row.kind
    if is_relation(row) and explicit_side(stage, row) is None:
        return _relation_lines(row)
    if kind in ("Pullback", "Pushforward"):
        return law_of_motion_kernel(stage, row.definition).lines
    if kind == "Aggregation":
        return aggregator_kernel(stage, row).lines
    if kind == "Expectation" and row.given is not None:
        return _conditional_expectation_lines(stage, box, row)
    if kind in ("Expectation", "DistributionExtension"):
        owners = tuple(table[reference] for reference in row.references if reference in table)
        shocks, given = integrated_shocks(stage, row), conditioning(stage, row)
        subjects = ", ".join(
            name for definition in owners for name in definition.equations[0].subjects
        )
        verb = "integrates" if kind == "Expectation" else "extends the measure by"
        arguments = tuple(
            dict.fromkeys(
                name for definition in owners for name in distribution_arguments(definition)
            )
        )
        if kind == "DistributionExtension":
            return (
                f"distribution of {subjects}: "
                f"{'; '.join(_declaration_text(definition, given) for definition in owners)}",
                f"{verb} {subjects}; conditioning arguments {', '.join(arguments) or 'none'}",
            )
        # on an expectation the verb answers the card's own statements, in the
        # card's words and order (§3 rule 5)
        return (
            f"distribution of {tuple_text(shocks)}: "
            f"{'; '.join(_declaration_text(definition, given) for definition in owners)}",
            f"conditioned on {', '.join(given) or 'none declared'}; "
            f"{_drawn_and_integrated(stage, box, row, edge_drawing(stage, shocks), shocks)}; "
            f"declared at {', '.join(str(definition.identity) for definition in owners)}",
        )
    if kind == "Evaluation":
        stems = tuple(i.field for sort in box.cod.inside for i in coordinates_of(sort))
        return (f"identity at {tuple_text(stems)}; no policy is inserted",)
    if kind == "Argmax":
        ctx = StageNames(stage)
        core = table[row.statements[0]].equations[0]
        found = next(
            (
                node
                for node in term_nodes(core)
                if isinstance(node, T.Operator) and node.head == "argmax"
            ),
            None,
        )
        if found is not None and found.subs:
            choices, feasible = [], []
            for position, binder in enumerate(found.subs):
                choice = binder.var if isinstance(binder, T.In) else binder.name
                choices.append(choice)
                target = (
                    row.unknowns[position]
                    if position < len(row.unknowns)
                    else ctx.resolve(choice, row.builder)
                )
                declared = binder.set if isinstance(binder, T.In) else ctx.declared_set(target)
                feasible.append(to_source(declared) if declared is not None else "not declared")
            choice = choices[0] if len(choices) == 1 else tuple_text(choices)
            objective = f"objective {to_source(found.args[0])}"
            functions = (
                tuple(sort for sort in box.dom.inside if sort.kind == "function")
                if row.maps
                else ()
            )
            if functions:
                objective += "; objective function " + ", ".join(
                    f"{wire_name(stage, sort)}({', '.join(i.field for i in sort.coordinates)})"
                    for sort in functions
                )
            return (f"{objective}; choice {choice}; feasible set {' × '.join(feasible)}",)
    return _relation_lines(row)


def _relation_lines(row):
    """The kernel of a row that states its equations and names its unknowns:
    each equation or relation the row holds as the file writes it, then the
    unknowns, `equation c = c[>]` and `unknowns c`."""
    unknowns = row.unknowns or tuple(function_field(output) for output in row.outputs)
    return tuple(
        f"{'equation' if isinstance(core, T.Equation) else 'relation'} {to_source(core)}"
        for core in row.equations
    ) + (f"unknowns {', '.join(wire_spelling(unknown) for unknown in unknowns)}",)


def _conditional_expectation_lines(stage, box, row):
    """The kernel of an expectation whose occurrence selects a conditional
    distribution from the joint distribution of the edge (AMD-SG-009 §5), in
    the card's words and order (AMD-SG-019 §3 rule 5): the distribution of the
    shocks it integrates, with its conditioning and the declarations that
    define it, and on a calibrated version that distribution at the calibration
    where its terms are numbers."""
    selection = kept_answer(
        stage,
        ("selection", row.identity, row.integrated, row.given),
        lambda: conditional_distribution_of(stage, row),
    )
    lines = [
        f"distribution of {tuple_text(selection.integrated)}: "
        f"{' · '.join(conditional_texts(selection))}",
        f"conditioned on {', '.join(selection.given) or 'none declared'}; "
        f"{_drawn_and_integrated(stage, box, row, selection.edge.block, selection.integrated)}; "
        f"declared at {', '.join(str(owner.identity) for owner in selection.declarations)}"
        + (
            f"; marginalizes {', '.join(s for owner in selection.leaves for s in owner.subjects)}"
            if selection.leaves
            else ""
        ),
    ]
    values = stage.bindings.calibration
    if values is not None and any(
        factor.form in ("marginal", "conditional") for factor in selection.factors
    ):
        numeric = conditional_texts(selection, dict(values))
        if numeric is not None:
            lines.append("at the calibration: " + " · ".join(numeric))
    return tuple(lines)


def _drawn_and_integrated(stage, box, row, edge, shocks):
    """The clause of an expectation's kernel line that names the edge that
    draws its shocks and the builder that integrates them, `drawn on the edge
    dcsn_to_cntn; in cntn_to_dcsn at each point of k_d, integrates Ψ, θ`: a
    shock is drawn on the edge of the forward builder that lists it,
    `fold.conditions.edge_drawing`, and the expectation over it is taken in
    the builder that holds the row, at each point of the coordinates its
    result is written in."""
    drawn = f"drawn on the edge {edge}" if edge is not None else "drawn on no forward edge"
    return (
        f"{drawn}; in {row.builder} at each point of "
        f"{tuple_text(_side_points(stage, box.cod.inside))}, integrates {', '.join(shocks)}"
    )


def _side_points(stage, sorts):
    """The coordinate names one side of a box is written in, once and in order:
    the point an operator acting pointwise ranges over."""
    return stems_of(
        tuple(dict.fromkeys(identity for sort in sorts for identity in coordinates_of(sort)))
    )


def coordinates_of(sort):
    """The coordinate identities of a wire as its sort retains them: a
    function's coordinates, the coordinates a measure is on, a field wire's
    own identity."""
    if sort.kind in ("function", "measure"):
        return tuple(sort.coordinates)
    return (sort.identity,)


def integrated_shocks(stage, row):
    """The shocks an expectation integrates or an extension draws, from the row
    where it holds them and from the declarations it names otherwise."""
    return tuple(row.integrated) or tuple(
        name
        for reference in row.references
        if reference in stage.definitions
        for name in stage.definitions[reference].equations[0].subjects
    )


def conditioning(stage, row):
    """The names a row's distribution is conditioned on, from the row where it
    holds them and from the declarations it names otherwise. A name the row
    itself integrates is no conditioning of the selection it takes: a joint
    draw of (s, η, θ) in which θ is declared given (η, s) is conditioned on
    nothing outside the draw."""
    if row.given:
        return tuple(row.given)
    integrated = set(integrated_shocks(stage, row))
    return tuple(
        dict.fromkeys(
            name
            for reference in row.references
            if reference in stage.definitions
            for name in distribution_arguments(stage.definitions[reference])
            if name not in integrated
        )
    )


def _declaration_text(definition, given=()):
    """A distribution declaration as written: its subjects, the names it is
    conditioned on where it names any, `~` and its family call, a scalar
    component of a mixture written as the measure it is, `point mass at 0`
    (AMD-SG-015 §5 item 6g). The declaration prints one way on every card,
    the extension's card included: `Ψ | ν ~ LogNormal(ν, σ_Ψ)` (AMD-SG-019
    §5a item 7)."""
    law = definition.equations[0]
    written = distribution_subject_text(list(law.subjects)) + (
        f" | {', '.join(given)}" if given else ""
    )
    return f"{written} ~ {_point_masses(to_source(law.law))}"


def _point_masses(text):
    """A scalar component of a mixture written as the measure it is: `(p, 0)`
    reads `(p, point mass at 0)` (AMD-SG-015 §5 item 6g). Only a pair whose
    second item is a number is rewritten, a pair being a bracket that no name
    precedes, so that the last argument of a family's call,
    `TruncatedNormal(0, 1, -1, 1)`, stays an argument."""
    if "Mixture(" not in text:
        return text
    return re.sub(
        r"((?<![\w)])\((?:[^(),]|\([^()]*\))+,\s*)(-?\d+(?:\.\d+)?)(\s*\))",
        r"\1point mass at \2\3",
        text,
    )


def _feasibility_lines(stage, box):
    """The feasibility conditions the wires of a box carry (AMD-SG-012 §3;
    AMD-SG-019 §2.3), each as the pair `(condition, origin)`: a wire written in
    the coordinates of a control is a function, or a measure, on a set smaller
    than the product its type line writes, so `c ∈ Γ(m_d)` stays a condition,
    with the place the correspondence was read from. It stands on every card
    whose wires carry the control as a coordinate, the pullback and the
    push-forward included. The pair is answered, not a sentence to be cut
    again."""
    return [
        (f"{identity.field} ∈ {text}", where)
        for identity, (text, where) in _feasible_controls(stage, box)
    ]


def _feasible_controls(stage, box):
    """The controls the wires of a box carry that declare a correspondence,
    each with its feasible set and the place the set was read from: what the
    `feasible` lines above are written from, and what the WHERE block reads to
    learn which controls the card already names."""
    found = []
    for identity in dict.fromkeys(
        identity for sort in box.dom.inside + box.cod.inside for identity in coordinates_of(sort)
    ):
        if field_role(stage, identity) != "control":
            continue
        feasible = _feasible_set_and_origin(stage, identity)
        if feasible is not None:
            found.append((identity, feasible))
    return tuple(found)


def _feasible_set_and_origin(stage, control):
    """The declared feasibility correspondence of a control, as its source text
    and where it was read from, or None (AMD-SG-012 §§3, 5): the `argmax`
    binder of a line of the stage, documentary or not. A documentary line is
    where the economist states the control's feasible set — on `cons.bl` the
    `!doc` line `optimality` carries `Γ(m_d)` and the operative lines are the
    endogenous grid — so excluding it would leave the feasibility on no line of
    the builder that applies the policy. A line that is not documentary is read
    first, since it is the one a method binds."""
    ctx = StageNames(stage)
    name = control.field
    declared = ctx.declared_set(control)
    if isinstance(declared, T.Call):
        return to_source(declared), None
    documentary = None
    for definition in stage.definitions.values():
        if definition.kind != "line":
            continue
        # one rule on both kinds of line: the binder of the control's own
        # name, or the single binder of a line whose left side is the control,
        # which is how an author binds a letter of his own,
        # `c = argmax_{cp : Γ(k_d)}(…)` (AMD-SG-013 §2)
        if "!doc" in getattr(definition, "tags", ()):
            documentary = documentary or _binder_of(definition, name)
            continue
        operative = _binder_of(definition, name)
        if operative is not None:
            return operative
    return documentary


def _binder_of(definition, name):
    """The subscript of the `argmax` that binds the control `name` on one line,
    as its source text and the line it was read from, or None. The author may
    bind a letter of his own, `c = argmax_{cp : Γ(m_d)}(…)` on `cons.bl`, so a
    single binder on a line whose left side is the control is that control's;
    and on a joint choice over several controls,
    `(c, l) = argmax_{cp : Γ(x), lp : Λ(x)}(…)`, where the left side is the
    ordered tuple of the controls and every one of them carries a set, the
    binder in the control's own position is that control's (AMD-SG-008 §7
    writes the joint choice this way)."""
    defines, positions = False, []
    for equation in definition.equations:
        if not isinstance(equation, T.Equation):
            continue
        left = equation.lhs
        if getattr(getattr(left, "symbol", None), "name", None) == name:
            defines = True
        items = getattr(left, "items", None)
        if items is None:
            continue
        written = [getattr(getattr(item, "symbol", None), "name", None) for item in items]
        if name in written:
            positions.append((written.index(name), len(written)))
    for node in term_nodes(definition.equations):
        if not (isinstance(node, T.Operator) and node.head == "argmax"):
            continue
        binders = [binder for binder in node.subs if isinstance(binder, T.In)]
        for binder in binders:
            if binder.var == name:
                return to_source(binder.set), definition.address
        if defines and len(binders) == 1:
            return to_source(binders[0].set), definition.address
        for index, width in positions:
            if len(binders) == width:
                return to_source(binders[index].set), definition.address
    return None


# --- an aggregation across the expectation ---


def affine(stage, box):
    """Whether the map of an aggregation box is affine in its value inputs:
    on the retained term, every value input enters only through terms of
    degree at most one, with coefficients free of every value input
    (AMD-SG-005 §3). A query; never a condition of construction. `box`
    is a primitive box of this version or its unambiguous name, resolved as
    `kernel` resolves it; a formal value input its map does not read is affine
    trivially (AMD-SG-008 §3).

    A box that writes one component answers `True` or `False`. A box on a value
    bundle answers per component, as a read-only mapping from the name of each
    output to its own answer, since one component of an arrival operator can be
    affine in the value while another is not (AMD-SG-011 §2). A relation
    with no explicit side (`grains.explicit_side`) maps nothing and is
    refused as a box of another kind is."""
    target, entry = operator_target(stage, box, "affine")
    row = row_at(stage, target, entry)
    if row.kind != "Aggregation" or answers_function_set(stage, row):
        what = "states a relation its output satisfies" if is_relation(row) else f"is a {row.kind}"
        raise TypeError(f"affine answers for an aggregation box; {target.name!r} {what}")
    answers = tuple(affine_in(term, row.inputs) for term in row.maps)
    if len(row.outputs) < 2 or len(answers) != len(row.outputs):
        return all(answers)
    # one key per output: the field it defines where it defines one, else the
    # wire identity, so that no two components share a key
    printed = [kernel_output_name(stage, output) for output in row.outputs]
    keys = [
        name if printed.count(name) == 1 else output for name, output in zip(printed, row.outputs)
    ]
    return MappingProxyType(dict(zip(keys, answers)))


def _across_expectation(stage, box, row):
    """The map of an aggregation with each expectation's result replaced by
    its integrand and the expectation written around it, `V[<](b) =
    E_{y}(β*V(g(·)))`: equal to the kernel by linearity of the integral, so
    printed only when `affine` answers yes (AMD-SG-005 §3); otherwise
    `ValueError`. A derivation of the kernel query, held here and not in the
    display. A relation is expanded through no producer: its map is no
    equation of its output."""
    if row.kind != "Aggregation" or answers_function_set(stage, row):
        what = "states a relation its output satisfies" if is_relation(row) else f"is a {row.kind}"
        raise TypeError(
            f"the form across the expectation rewrites an aggregation box; {box.name!r} {what}"
        )
    rows = {r.identity: r for r in rows_of(stage, block_id_of(box))}
    producer = {output: r for r in rows.values() for output in r.outputs}
    coordinate_names = [c.field for c in row.arguments]
    if not all(affine_in(term, row.inputs) for term in row.maps):
        raise ValueError(
            f"the map of {box.name!r} is not affine in its value inputs, so the aggregation "
            "cannot be moved across the expectation: the two forms are "
            "equal only by linearity of the integral (AMD-SG-005 §3)"
        )
    found = []  # (shock names, distribution identity) in order of first appearance

    def named(term):
        # a wire the map reads by the name an aggregation's kernel gives it
        # where it is of the kinds that kernel names as outputs, and otherwise
        # by the name the stage gives the wire
        if is_wire_symbol(term):
            identity = term.symbol.name
            name = (
                kernel_output_name(stage, identity)
                if is_kernel_output(stage, identity)
                else wire_name(stage, wire_table(stage).sort_of(identity))
            )
            return T.Sym(T.Constant(name))
        if isinstance(term, tuple):
            return tuple(named(t) for t in term)
        if dataclasses.is_dataclass(term) and not isinstance(term, type):
            return dataclasses.replace(
                term, **{f.name: named(getattr(term, f.name)) for f in dataclasses.fields(term)}
            )
        return term

    def expanded(term):
        if is_wire_symbol(term):
            source = producer.get(term.symbol.name)
            if source is not None and source.kind == "Aggregation" and not is_relation(source):
                return expanded(source.maps[0])
            if source is not None and source.kind == "Expectation":
                shocks = tuple(source.integrated)
                if (shocks, source.distribution) not in found:
                    found.append((shocks, source.distribution))
                return expanded(source.maps[0])
            return term
        if isinstance(term, tuple):
            return tuple(expanded(t) for t in term)
        if dataclasses.is_dataclass(term) and not isinstance(term, type):
            return dataclasses.replace(
                term, **{f.name: expanded(getattr(term, f.name)) for f in dataclasses.fields(term)}
            )
        return term

    lines = [f"kernel of {box.name} across the expectation"]
    for identity, term in zip(row.outputs, row.maps):
        found.clear()
        text = to_source(named(expanded(term)))
        if not found:
            raise ValueError(f"no expectation feeds the output {identity!r} of {box.name!r}")
        for shocks, _ in reversed(found):
            text = f"E_{{{', '.join(shocks)}}}({text})"
        output = (
            marked_field(identity)
            if identity.kind in ("function", "choice") and identity.perch is not None
            else identity
        )
        lines.append(f"  {output}({', '.join(coordinate_names)}) = {text}")
    return "\n".join(lines)


# --- the kernel as the source text of one Python function ---

# the precedence of a written Python expression, lowest first: a comparison,
# a sum or a difference, a product or a quotient, a negation, a power, and a
# name, a number, a call or a subscript
_COMPARISON, _SUM, _PRODUCT, _NEGATION, _POWER, _ATOM = range(6)

# the Python sign and the precedence of each arithmetic operation of a
# retained term
_OPERATIONS = {
    T.Add: (" + ", _SUM),
    T.Sub: (" - ", _SUM),
    T.Mul: ("*", _PRODUCT),
    T.Div: ("/", _PRODUCT),
    T.Pow: ("**", _POWER),
}

# the perch a mark at the end of a printed name stands for, `cntn` for `≻`
_MARKED_PERCH = {mark: perch for perch, mark in PERCH_MARK.items() if mark}

# the texts made into functions in this process, counted, so that each text
# is entered in `linecache` under a name of its own
_MADE = itertools.count(1)


class _Written(NamedTuple):
    """One written Python expression: its text, the precedence of its
    outermost operation, the number of axes its value has at a point, and
    whether its value can carry the axes of the evaluation points, as a value
    read from the kernel's arguments can and a number or a parameter cannot."""

    text: str
    precedence: int
    axes: int
    batched: bool


class _Text(NamedTuple):
    """The Python text of one kernel: the source, the name of the one
    function it defines, and the parameters that function takes after the
    kernel's arguments, by the names the file declares, in declaration
    order."""

    source: str
    name: str
    parameters: tuple


class _Function(NamedTuple):
    """An inner function of a kernel's text: its Python name, its definition
    as lines without their indentation, the number of axes its value has at a
    point, and the names the file writes for it, its own and an alias's."""

    name: str
    lines: tuple
    axes: int
    written: tuple


class _Names:
    """The Python names of one text or of one inner function, each taken
    once: a printed name as Python reads it (`_python_name`), or the fallback
    where it reads none, and where that name is a keyword or already taken,
    the first free one of `name_1`, `name_2`, … . `np` is taken from the
    start, since the text reaches NumPy by it."""

    def __init__(self, taken=()):
        self.taken = {"np", *taken}

    def take(self, written, fallback):
        base = _python_name(written) or fallback
        chosen, suffix = base, 0
        while chosen in self.taken or keyword.iskeyword(chosen):
            suffix += 1
            chosen = f"{base}_{suffix}"
        self.taken.add(chosen)
        return chosen


def _python_name(written):
    """The name a printed name takes in Python: a perch mark at its end
    written as the perch, `V≻` as `V_cntn`, and the result as Python reads an
    identifier (NFKC, PEP 3131), so that `𝑢` is `u` and `𝑑𝑢𝑖𝑛𝑣` is `duinv`;
    None where the result is no identifier, as for an output that the kernel
    names by the map its row writes, `V≻^(1 - γ)`."""
    text = str(written)
    for mark, perch in _MARKED_PERCH.items():
        if text.endswith(mark):
            text = f"{text[: -len(mark)]}_{perch}"
    text = unicodedata.normalize("NFKC", text)
    return text if text.isidentifier() else None


def _function_record(stage, row):
    """The kernel record of the one explicit function a row applies, from
    which its text is written: the complete g of a pullback or a push-forward,
    the G segment of an aggregation, and of a row whose output is its own
    unknown the explicit side of its relation (`grains.explicit_side`);
    None where the row applies no explicit function."""
    if is_relation(row):
        return aggregator_kernel(stage, row) if explicit_side(stage, row) is not None else None
    if row.kind in ("Pullback", "Pushforward"):
        return law_of_motion_kernel(stage, row.definition)
    if row.kind == "Aggregation":
        return aggregator_kernel(stage, row)
    return None


def _text_or_none(stage, box, row):
    """The Python text of the function a row applies, or None where the row
    applies none or its kernel holds a form the text cannot write, which
    `compile_kernel` refuses under `kernel-form`."""
    record = _function_record(stage, row)
    if record is None:
        return None
    try:
        return _python_text(stage, box, record)
    except ConstructionError as error:
        if error.rule == "kernel-form":
            return None
        raise


def _python_text(stage, box, spec):
    """The source text of one plain Python function of a kernel: a header of
    comments naming the stage, the box, the stage file with its SHA-256, the
    package's version, the printed kernel, the declared sets of the
    parameters the kernel reads and the Python name of each name of the file
    that Python writes otherwise; then `import numpy as np` and the function.
    Its arguments are the kernel's own, in printed order, then each parameter
    it reads, directly or through a named function, in declaration order; the
    named functions it calls are its inner functions, reading those
    parameters; each output is assigned to its printed name as Python writes
    it, or to `result` where that name is no identifier, and the outputs are
    returned in printed order, one as it is and several as a tuple.
    NumPy is reached by `np` alone. The text holds no date and no value, so
    that two elaborations of one file and two calibrations of one version
    give the same text. A form it cannot write is refused under
    `kernel-form`, naming the output whose term holds it."""
    writer = _Writer(stage, box, spec)
    values = []
    for position, term in enumerate(spec.terms):
        writer.position = position
        values.append(writer.expression(term, {}, {}))
    writer.position = None
    read = tuple(name for name in writer.ctx.parameter_sets if name in writer.read)
    outputs = tuple(writer.names.take(name, "result") for name in spec.outputs)
    arguments = tuple(written.text for written in writer.arguments)
    parameters = tuple(writer.parameters[name].text for name in read)
    functions = tuple(writer.functions[key] for key in writer.order)
    renamed = dict.fromkeys(
        (python, written)
        for python, written in (
            *zip(arguments, spec.shown or spec.names),
            *zip(parameters, read),
            *((function.name, name) for function in functions for name in function.written),
        )
        if python != written
    )
    renamed.update(
        dict.fromkeys(
            (python, f"the output {written}")
            for python, written in zip(outputs, spec.outputs)
            if python != written
        )
    )
    declared = writer.ctx.parameter_sets
    source = source_file(stage)
    lines = [
        f"# bellman kernel of {stage.name}, {box.name}; "
        f"{PurePosixPath(str(source)).name if source else 'no file'} sha256 "
        f"{stage.provenance.get('sha256') or 'not recorded'}; bellman {_package_version()}",
        *(f"# {line}" for line in spec.lines),
        "# parameters: "
        + (
            "; ".join(
                name if declared.get(name) is None else f"{name} ∈ {to_source(declared[name])}"
                for name in read
            )
            or "none"
        ),
        "# names: "
        + (
            "; ".join(f"{python} is {written}" for python, written in renamed)
            or "as in the stage file"
        ),
        "import numpy as np",
        "",
        f"def {writer.function}({', '.join(arguments + parameters)}):",
        *(f"    {line}" for function in functions for line in function.lines),
        *(f"    {name} = {value.text}" for name, value in zip(outputs, values)),
        f"    return {', '.join(outputs)}",
    ]
    return _Text("\n".join(lines) + "\n", writer.function, read)


def _function_of(text):
    """The function a kernel's text defines, made by executing the text in a
    fresh namespace, which then holds `np` alone. The text is entered in
    `linecache` under a name of its own with no modification time, so that
    `inspect.getsource` prints the function's definition, and the entry is
    removed when the function is collected. Nothing is stored on the stage or
    the box."""
    filename = f"<bellman kernel {text.name} {next(_MADE)}>"
    namespace = {}
    exec(compile(text.source, filename, "exec"), namespace)
    function = namespace.pop(text.name)
    linecache.cache[filename] = (
        len(text.source),
        None,
        text.source.splitlines(keepends=True),
        filename,
    )
    weakref.finalize(function, linecache.cache.pop, filename, None)
    return function


@functools.cache
def _package_version():
    """The version of the package that writes the texts, read once."""
    return package_version()


def _function_name(spec):
    """The name of a kernel's function: its letter and its builder, and for a
    segment of a builder's value aggregator the segment as well,
    `G_policy_InvEuler` beside `G_policy_endoggrid`, so that no two kernels of
    one stage share a name."""
    parts = [spec.letter, spec.builder]
    segment = spec.segment
    if spec.letter == "G" and segment != Identity("Aggregation", address=spec.builder):
        address = segment.address or ""
        if "." in address:
            parts.append(address.split(".", 1)[1])
        parts.extend(
            str(part)
            for part in (
                segment.field,
                segment.occurrence,
                "_".join(segment.subjects) or None,
                segment.mark,
            )
            if part is not None
        )
    joined = unicodedata.normalize("NFKC", "_".join(parts))
    return joined if joined.isidentifier() else re.sub(r"\W", "_", joined)


class _Writer:
    """The writing of one kernel's text: the stage, the box and its kernel
    record; the names of the stage; the Python names of the text, with the
    function's own name, the kernel's arguments, the parameters and the named
    functions taken in that order; the written argument of each position and
    of each parameter; the inner functions written, in the order a caller
    reads them, and those being written; the parameters read; and the
    position of the output whose term is being written, None between
    terms."""

    def __init__(self, stage, box, spec):
        self.stage, self.box, self.spec = stage, box, spec
        self.ctx = StageNames(stage)
        self.function = _function_name(spec)
        self.names = _Names((self.function,))
        self.arguments = tuple(
            _Written(
                self.names.take(name, "argument"),
                _ATOM,
                len(_declared_shape(declared, self.ctx.set_terms) or ()),
                True,
            )
            for name, declared in zip(spec.names, spec.argument_sets)
        )
        self.parameters = {
            name: _Written(
                self.names.take(name, "parameter"),
                _ATOM,
                len(_declared_shape(declared, self.ctx.set_terms) or ()),
                False,
            )
            for name, declared in self.ctx.parameter_sets.items()
        }
        # one selection helper for each declared number of collection axes
        self.entry_helpers = {}
        self.function_names = {
            name: self.names.take(name, "function") for name in self.ctx.functions
        }
        self.functions, self.order, self.writing = {}, [], set()
        self.read = set()
        self.position = None

    def expression(self, term, env, domains):
        """The Python expression of `term`; `env` holds the written
        parameters of the inner function being written, by the name its
        definition gives them, and `domains` their declared sets."""
        if isinstance(term, T.Number):
            return _number(term.value)
        if isinstance(term, T.Sym):
            return self._symbol(term, env)
        if isinstance(term, tuple(_OPERATIONS)):
            return self._arithmetic(term, env, domains)
        if isinstance(term, T.Neg):
            # `-a*b` and `-a/b`, which Python reads as `(-a)*b` and `(-a)/b`,
            # equal the negated product and quotient exactly, so a product
            # or a quotient takes no brackets after the sign
            operand = self.expression(term.operand, env, domains)
            kept = _unsigned(operand) and operand.precedence >= _PRODUCT
            return _Written(
                f"-{operand.text if kept else f'({operand.text})'}",
                _NEGATION,
                operand.axes,
                operand.batched,
            )
        if isinstance(term, T.Tuple):
            return self._stacked(term, env, domains)
        if isinstance(term, T.Select) and isinstance(term.sel, T.Pos):
            return self._position(term, env, domains)
        if isinstance(term, T.Select) and isinstance(term.sel, T.Key):
            return self._key(term, env, domains)
        if isinstance(term, T.Call):
            return self._call(term, env, domains)
        case = label_case(self.ctx, term, self.spec.builder)
        if case is not None:
            return self.expression(case, env, domains)
        self._refuse(f"the form {self._printed(term)}")

    def _symbol(self, term, env):
        """A name written as an argument of the kernel, a parameter, a
        parameter of the inner function being written or infinity; any other
        name is refused."""
        spec, ctx = self.spec, self.ctx
        if is_wire_symbol(term):
            return self.arguments[spec.index[term.symbol.name]]
        name, side = spelling(term)
        if side is None and name in env:
            return env[name]
        if side is None and name in ("inf", "∞"):
            return _Written("np.inf", _ATOM, 0, False)
        if side is None and name in ctx.parameter_names:
            self.read.add(name)
            return self.parameters[name]
        position = spec.index.get(ctx.resolve(name, spec.builder, side))
        if position is None:
            self._refuse(
                f"the name {self._printed(term)}, which is neither "
                "an argument of the kernel nor a parameter"
            )
        return self.arguments[position]

    def _arithmetic(self, term, env, domains):
        """A sum, a difference, a product, a quotient or a power of two
        written operands, their axes at a point aligned. An operand of the
        same precedence on the right keeps its brackets, so that the function
        evaluates in the order the retained term does."""
        sign, precedence = _OPERATIONS[type(term)]
        first, second = (
            (term.base, term.exponent) if isinstance(term, T.Pow) else (term.left, term.right)
        )
        left = self.expression(first, env, domains)
        right = self.expression(second, env, domains)
        axes = max(left.axes, right.axes)
        left, right = _aligned(left, axes), _aligned(right, axes)
        if precedence == _POWER:
            text = f"{_bracketed(left, _ATOM)}**{_bracketed(right, _ATOM)}"
        else:
            kept = _unsigned(right) and right.precedence > precedence
            text = (
                f"{_bracketed(left, precedence)}{sign}{right.text if kept else f'({right.text})'}"
            )
        return _Written(text, precedence, axes, left.batched or right.batched)

    def _stacked(self, term, env, domains):
        """The entries of a tuple as one array, their evaluation points
        broadcast together and the entries stacked along a new axis before
        the axes each has at a point; entries with different numbers of axes
        at a point are refused."""
        entries = [self.expression(item, env, domains) for item in term.items]
        counts = {entry.axes for entry in entries}
        if len(counts) != 1:
            self._refuse(
                f"the tuple {self._printed(term)}, whose entries have different shapes at a point"
            )
        count = counts.pop()
        return _Written(
            f"np.stack(np.broadcast_arrays({', '.join(entry.text for entry in entries)}), "
            f"axis={-(count + 1)})",
            _ATOM,
            count + 1,
            any(entry.batched for entry in entries),
        )

    def _position(self, term, env, domains):
        """The component of a product value its 1-based position selects: an
        entry of a written tuple itself, and otherwise the component along
        the first axis at a point."""
        at = term.sel.at
        if isinstance(term.family, T.Tuple):
            if not 1 <= at <= len(term.family.items):
                self._refuse(
                    f"the selection {self._printed(term)}, outside the "
                    f"{len(term.family.items)} entries of its tuple"
                )
            return self.expression(term.family.items[at - 1], env, domains)
        family = self.expression(term.family, env, domains)
        if family.axes < 1:
            self._refuse(
                f"the selection {self._printed(term)}, whose family has no components at a point"
            )
        return _component(family, at - 1)

    def _key(self, term, env, domains):
        """The entry of a collection, or the component of a product value,
        that a key selects. For a collection on an index set the entry is
        found by the collection's own index set, the first factor of its
        domain: by a label's position for a set of labels, by one `np.where`
        for each integer member of a listed set, the members written from
        the parameters, and by the offset from the lower bound for an
        integer range, the bounds written from the parameters, so that the
        text holds no calibration and the parameters the index set reads
        become arguments; a key equal to no member, or outside the range,
        gives no value. For a product value the key's own declared finite set
        of labels gives the component's position, written as one `np.where`
        for each label; a key with no such set is refused."""
        ctx, name = self.ctx, term.sel.at
        key = self.expression(T.Sym(T.Constant(name)), env, domains)
        if key.axes:
            self._refuse(f"the selection {self._printed(term)}, whose key is no label at a point")
        indexed = sets.index_sets(self._family_set(term.family, domains), ctx.set_terms)
        if indexed is not None:
            first = _set_named(indexed[0], ctx.set_terms)
            family = self.expression(term.family, env, domains)
            if family.axes < 1:
                self._refuse(
                    f"the selection {self._printed(term)}, whose family has no components "
                    "at a point"
                )
            if isinstance(first, T.IntegerRange):
                lower = self._index_expression(first.lower, env, domains)
                upper = self._index_expression(first.upper, env, domains)
                return _Written(
                    f"{self._entry_helper(family.axes)}({family.text}, {key.text}, {lower.text}, "
                    f"{upper.text})",
                    _ATOM,
                    family.axes - 1,
                    True,
                )
            if isinstance(first, T.Points):
                match = self._integer_match_helper()
                conditions = tuple(
                    f"{match}({key.text}, {self._index_expression(member, env, domains).text})"
                    for member in first.members
                )
            elif isinstance(first, T.FiniteSet):
                conditions = tuple(
                    f"np.asarray({key.text}) == {str(label)!r}" for label in first.members
                )
            else:
                self._refuse(
                    f"the selection {self._printed(term)}, whose collection is declared on "
                    f"{to_source(indexed[0])}, which is no finite index set"
                )
            components = [_component(family, index) for index in range(len(conditions))]
            return self._cases(conditions, components)
        declared = (
            domains[name]
            if name in domains
            else ctx.declared_set(ctx.resolve(name, self.spec.builder))
        )
        domain = _set_named(declared, ctx.set_terms)
        if not isinstance(domain, T.FiniteSet):
            self._refuse(
                f"the selection {self._printed(term)}, whose key has no declared finite set "
                "of labels"
            )
        labels = tuple(str(label) for label in domain.members)
        if isinstance(term.family, T.Tuple):
            if len(term.family.items) != len(labels):
                self._refuse(
                    f"the selection {self._printed(term)}, whose {len(term.family.items)} entries "
                    f"are not one for each of its {len(labels)} labels"
                )
            components = [self.expression(item, env, domains) for item in term.family.items]
        else:
            family = self.expression(term.family, env, domains)
            if family.axes < 1:
                self._refuse(
                    f"the selection {self._printed(term)}, whose family has no components "
                    "at a point"
                )
            components = [_component(family, index) for index in range(len(labels))]
        return self._cases(
            tuple(f"np.asarray({key.text}) == {label!r}" for label in labels), components
        )

    def _index_expression(self, term, env, domains):
        """An integer bound or member, with closed arithmetic evaluated
        exactly and parameter arithmetic checked for machine-integer overflow.
        Division by one is removed; other division has no compiled form."""
        value = sets.number_at(term, {}).value
        if value is not None and sets.integer_valued(value):
            return _number(int(value))
        if isinstance(term, T.Div):
            if sets.number_at(term.right, {}).value == 1:
                return self._index_expression(term.left, env, domains)
            self._refuse(
                f"the integer index expression {self._printed(term)}, whose division "
                "has no exact compiled form; declare its integer result as a separate parameter"
            )
        if isinstance(term, (T.Add, T.Sub, T.Mul, T.Pow, T.Neg)):
            if isinstance(term, T.Neg):
                kind, parts = T.Sub, (T.Number(0), term.operand)
            elif isinstance(term, T.Pow):
                kind, parts = T.Pow, (term.base, term.exponent)
            else:
                kind, parts = type(term), (term.left, term.right)
            operands = tuple(self._index_expression(part, env, domains) for part in parts)
            helper = self._integer_arithmetic_helper(kind)
            return _Written(f"{helper}({operands[0].text}, {operands[1].text})", _ATOM, 0, False)
        return self.expression(term, env, domains)

    def _integer_arithmetic_helper(self, kind):
        """The checked machine-integer operation used in an index expression.
        Invalid operands or overflow refuse evaluation before a wrapped result
        can identify an entry."""
        key = ("integer_arithmetic", kind)
        if key not in self.functions:
            integer = self._integer_key_helper()
            name = self.names.take(f"index_{kind.__name__.lower()}", "function")
            lines = [
                f"def {name}(left, right):",
                f"    a, a_valid = {integer}(left)",
                f"    b, b_valid = {integer}(right)",
                "    if not (a_valid.item() and b_valid.item()):",
                (
                    "        raise ValueError('compiled index arithmetic requires signed 64"
                    "-bit integer operands')"
                ),
            ]
            if kind is T.Pow:
                multiply = self._integer_arithmetic_helper(T.Mul)
                lines.extend(
                    (
                        "    exponent = b.item()",
                        "    if exponent < 0:",
                        (
                            "        raise ValueError('compiled index arithmetic requi"
                            "res a nonnega"
                            "tive integer exponent')"
                        ),
                        "    result = np.ones(np.shape(a), dtype=np.int64)",
                        "    while exponent > 0:",
                        "        if exponent % 2:",
                        f"            result = {multiply}(result, a)",
                        "        exponent = exponent // 2",
                        "        if exponent > 0:",
                        f"            a = {multiply}(a, a)",
                        "    return result",
                    )
                )
            else:
                sign = _OPERATIONS[kind][0]
                lines.append(f"    result = np.asarray(a {sign.strip()} b)")
                if kind is T.Add:
                    lines.append(
                        "    valid = ((b >= 0) & (result >= a)) | ((b < 0) & (result < a))"
                    )
                elif kind is T.Sub:
                    lines.append(
                        "    valid = ((b >= 0) & (result <= a)) | ((b < 0) & (result > a))"
                    )
                else:
                    lines.extend(
                        (
                            "    minimum = -9223372036854775808",
                            "    special = (a == -1) & (b == minimum)",
                            (
                                "    divisor = np.where((a == 0) | ((result == minimum"
                                ") & (a == -1)), 1"
                                ", a)"
                            ),
                            "    valid = ((a == 0) | (result // divisor == b)) & ~special",
                        )
                    )
                lines.extend(
                    (
                        "    if not np.asarray(valid).item():",
                        (
                            "        raise ValueError('compiled index arithmetic excee"
                            "ds signed 64-"
                            "bit integers')"
                        ),
                        "    return result",
                    )
                )
            self.functions[key] = _Function(name, tuple(lines), 0, ())
            self.order.append(key)
        return self.functions[key].name

    def _integer_key_helper(self):
        """The inner function converting a numerical key to a machine integer
        with a mask that excludes noninteger and Boolean values."""
        key = ("integer_key",)
        if key not in self.functions:
            name = self.names.take("integer_key", "function")
            self.functions[key] = _Function(
                name,
                (
                    f"def {name}(value):",
                    "    value = np.asarray(value)",
                    (
                        "    if (value.dtype == np.dtype('complex64')) or (value.dtype == np.dt"
                        "ype('complex128')):"
                    ),
                    (
                        "        return np.zeros(value.shape, dtype=np.int64), np.zeros(value.s"
                        "hape, dtype=np.bool_)"
                    ),
                    "    if value.dtype == np.dtype('uint64'):",
                    "        integer = value.astype(np.int64)",
                    "        valid = value <= np.uint64(9223372036854775807)",
                    "        return integer, np.asarray(valid)",
                    "    number = value",
                    "    finite = np.isfinite(number)",
                    (
                        "    if number.dtype == np.dtype('float64') or number.dtype == np.dtype"
                        "('float32'):"
                    ),
                    (
                        "        finite = finite & (number >= -9223372036854775808.0) & (number"
                        " < 9223372036854775808.0)"
                    ),
                    "    integer = np.where(finite, number, 0).astype(np.int64)",
                    (
                        "    excluded = (value.dtype == np.dtype('bool')) or (value.dtype == np"
                        ".dtype('complex64')) or (value.dtype == np.dtype('complex128'))"
                    ),
                    "    valid = finite & (number == integer) & (not excluded)",
                    "    return integer, np.asarray(valid)",
                ),
                0,
                (),
            )
            self.order.insert(0, key)
        return self.functions[key].name

    def _integer_match_helper(self):
        """The inner function comparing integer keys after conversion, with no
        floating comparison between the two keys."""
        key = ("integer_match",)
        if key not in self.functions:
            integer = self._integer_key_helper()
            name = self.names.take("same_integer", "function")
            self.functions[key] = _Function(
                name,
                (
                    f"def {name}(left, right):",
                    f"    left_integer, left_valid = {integer}(left)",
                    f"    right_integer, right_valid = {integer}(right)",
                    "    return left_valid & right_valid & (left_integer == right_integer)",
                ),
                0,
                (),
            )
            self.order.append(key)
        return self.functions[key].name

    def _cases(self, conditions, components):
        """One `np.where` for each member of a finite index set, the component
        of the family at the member's position where the key equals the
        member, and no value where it equals none."""
        axes = max(component.axes for component in components)
        text = "np.nan"
        for condition, component in reversed(tuple(zip(conditions, components))):
            written = _Written(condition, _COMPARISON, 0, True)
            text = (
                f"np.where({_aligned(written, axes).text}, "
                f"{_aligned(component, axes).text}, {text})"
            )
        return _Written(text, _ATOM, axes, True)

    def _family_set(self, family, domains):
        """The declared set of the family a selection reads: of a parameter,
        a parameter of the inner function being written, or an argument of
        the kernel its set, and of a nested selection the set its entries
        lie in once the outer key is fixed; None for a written tuple or a
        name with no declared set."""
        ctx, spec = self.ctx, self.spec
        if isinstance(family, T.Select):
            indexed = sets.index_sets(self._family_set(family.family, domains), ctx.set_terms)
            return None if indexed is None else indexed[1]
        if not isinstance(family, T.Sym):
            return None
        if is_wire_symbol(family):
            return spec.argument_sets[spec.index[family.symbol.name]]
        name, side = spelling(family)
        if side is None and name in domains:
            return domains[name]
        if side is None and name in ctx.parameter_names:
            return ctx.declared_set(Identity("parameter", stage=ctx.stage_name, field=name))
        return ctx.declared_set(ctx.resolve(name, spec.builder, side))

    def _entry_helper(self, axes):
        """The name of the inner function that reads the entry of a collection
        at an integer key, written once before the first output that selects
        by a range: the key counted from the lower bound, no value outside
        the bounds or at a key that is no integer, the family broadcast
        against the key's batch and read along the first of its `axes` axes
        at a point. The declared number of axes fixes the selection axis
        and the reshape tuples in the function text."""
        if axes not in self.entry_helpers:
            name = self.names.take(f"entry_at_{axes}", "function")
            self.entry_helpers[axes] = name
            integer = self._integer_key_helper()
            self.functions[("entry", name)] = _Function(
                name,
                (
                    f"def {name}(F, k, lo, hi):",
                    "    F = np.asarray(F)",
                    f"    key, key_valid = {integer}(k)",
                    f"    lower, lower_valid = {integer}(lo)",
                    f"    upper, upper_valid = {integer}(hi)",
                    (
                        "    valid = np.asarray(key_valid & lower_valid & upper_valid & (key >="
                        " lower) & (key <= upper))"
                    ),
                    "    j = np.asarray(np.where(valid, key, lower) - lower).astype(np.intp)",
                    f"    shape = np.shape(j) + {(1,) * axes!r}",
                    "    shape = np.broadcast_shapes(np.shape(F), shape)",
                    "    F_b = np.broadcast_to(F, shape)",
                    "    j_b = np.broadcast_to(np.reshape(j, np.shape(j) + "
                    f"{(1,) * axes!r}), shape)",
                    f"    out = np.take(np.take_along_axis(F_b, j_b, axis={-axes}), "
                    f"0, axis={-axes})",
                    f"    mask = np.reshape(valid, np.shape(valid) + {(1,) * (axes - 1)!r})",
                    "    return np.where(mask, out, np.nan)",
                ),
                0,
                (),
            )
            self.order.append(("entry", name))
        return self.entry_helpers[axes]

    def _call(self, term, env, domains):
        """A call of a closed-form function, written as a call of the inner
        function that the text defines for it."""
        definition, core = self._closed_form(term)
        if len(term.args) != len(core.params):
            self._refuse(
                f"the call {self._printed(term)} of {definition.identity} with {len(term.args)} "
                f"arguments, whose definition takes {len(core.params)}"
            )
        arguments = [self.expression(argument, env, domains) for argument in term.args]
        function = self._function(definition, core, term.fun)
        return _Written(
            f"{function.name}({', '.join(argument.text for argument in arguments)})",
            _ATOM,
            function.axes,
            any(argument.batched for argument in arguments),
        )

    def _function(self, definition, core, called):
        """The inner function of a closed-form definition, written once and
        before the output that first calls it: its parameters named as the
        definition names them, each with the number of axes its declared set
        gives it at a point, and its body returned. Its parameters may take
        the names of the kernel's arguments, which the body does not read,
        and never those of a parameter or a named function, which it may."""
        key = definition.identity
        if key in self.functions:
            known = self.functions[key]
            if called not in known.written:
                known = known._replace(written=known.written + (called,))
                self.functions[key] = known
            return known
        if key in self.writing:
            self._refuse(f"the call of {definition.identity}, whose definition reaches itself")
        self.writing.add(key)
        local = _Names(
            (
                *(written.text for written in self.parameters.values()),
                *self.function_names.values(),
            )
        )
        env, domains, names = {}, {}, []
        for param in core.params:
            declared = coordinate_declared_set(param)
            name = local.take(param.stem, "x")
            names.append(name)
            env[param.stem] = _Written(
                name,
                _ATOM,
                len(_declared_shape(declared, self.ctx.set_terms) or ()),
                True,
            )
            domains[param.stem] = declared
        body = self.expression(core.body, env, domains)
        name = self.function_names[definition.identity.field]
        function = _Function(
            name,
            (f"def {name}({', '.join(names)}):", f"    return {body.text}"),
            body.axes,
            tuple(dict.fromkeys((definition.identity.field, called))),
        )
        self.writing.discard(key)
        self.functions[key] = function
        self.order.append(key)
        return function

    def _closed_form(self, term):
        """The definition a call reaches and its function term, an alias of a
        function's name followed to the function it names."""
        functions = self.ctx.functions
        name, seen = term.fun, []
        while True:
            definition = functions.get(name)
            if definition is None:
                self._refuse(
                    f"the call {self._printed(term)} of a function no definition of the stage "
                    "declares"
                )
            core = definition.equations[0]
            if isinstance(core, T.FuncDef):
                return definition, core
            seen.append(name)
            if (
                definition.kind == "function_alias"
                and isinstance(core, T.Sym)
                and isinstance(core.symbol, T.Constant)
                and core.symbol.name in functions
                and core.symbol.name not in seen
            ):
                name = core.symbol.name
                continue
            text = (
                f"{name} := {to_source(core)}"
                if definition.kind == "function_alias"
                else to_source(core)
            )
            self._refuse(
                f"the call {self._printed(term)} of {text} "
                f"({definition.identity}), which is not a closed-form function"
            )

    def _printed(self, term):
        """The source text of a term a refusal names, each wire symbol written
        by the name of the kernel's argument it is, `𝑑𝑢𝑖𝑛𝑣(dV≻)`."""

        def named(node):
            if is_wire_symbol(node):
                position = self.spec.index.get(node.symbol.name)
                written = (
                    self.spec.names[position] if position is not None else str(node.symbol.name)
                )
                return T.Sym(T.Constant(written))
            if isinstance(node, tuple):
                return tuple(named(item) for item in node)
            if dataclasses.is_dataclass(node) and not isinstance(node, type):
                return dataclasses.replace(
                    node,
                    **{
                        field.name: named(getattr(node, field.name))
                        for field in dataclasses.fields(node)
                    },
                )
            return node

        return to_source(named(term))

    def _refuse(self, what):
        """The `kernel-form` refusal of a form the text cannot write, naming
        the output whose term holds it and the statement that defines that
        output."""
        stage, box, spec, position = self.stage, self.box, self.spec, self.position
        address = spec.address if position is None else spec.sources[position]
        where = (
            f"the component {spec.outputs[position]} ({address}) of the kernel of {box.name!r}"
            if position is not None and len(spec.outputs) > 1
            else f"the kernel of {box.name!r}"
        )
        raise construction_error(
            f"stage {stage.name!r}: {where} ({spec.identity}) contains {what}; no compile rule "
            "evaluates it: compile evaluates retained arithmetic and calls to closed-form named "
            "functions and selects no numerical method (AMD-SG-007 §3.1, rule kernel-form); "
            "define that function in closed form, or read the kernel with kernel(stage, box)",
            stage=stage.name,
            address=address,
            span=None,
            rule="kernel-form",
            file=source_file(stage),
        )


def _number(value):
    """A number of a retained term as a Python literal; an unbounded value as
    `np.inf`."""
    if isinstance(value, float) and not math.isfinite(value):
        text = "np.nan" if math.isnan(value) else ("-np.inf" if value < 0 else "np.inf")
    else:
        text = repr(value)
    return _Written(text, _NEGATION if text.startswith("-") else _ATOM, 0, False)


def _bracketed(written, least):
    """The text of an operand, in brackets where its precedence is below
    `least`."""
    return written.text if written.precedence >= least else f"({written.text})"


def _unsigned(written):
    """Whether a written operand begins with no minus sign, so that it may
    stand after a sign or a negation without brackets."""
    return written.precedence != _NEGATION and not written.text.startswith("-")


def _aligned(written, axes):
    """An operand with axes of length one inserted before its own axes at a
    point, up to `axes`, where its value can carry the axes of the evaluation
    points, so that NumPy's broadcasting pairs the evaluation points of every
    operand of one operation."""
    if written.axes >= axes or not written.batched:
        return written
    positions = tuple(range(-axes, -written.axes))
    where = str(positions[0]) if len(positions) == 1 else str(positions)
    return _Written(f"np.expand_dims({written.text}, {where})", _ATOM, axes, True)


def _component(family, index):
    """The component at the 0-based `index` along the first axis at a point
    of a product value."""
    rest = ", :" * (family.axes - 1)
    return _Written(
        f"np.asarray({family.text})[..., {index}{rest}]", _ATOM, family.axes - 1, family.batched
    )


def _set_named(term, declared_sets):
    """A named domain resolved through the retained set definitions."""
    seen = set()
    while isinstance(term, T.Named) and term.name in declared_sets and term.name not in seen:
        seen.add(term.name)
        term = declared_sets[term.name]
    return term


def _declared_shape(declared, declared_sets=None):
    """The shape one value of a declared set has at a point: `()` for a set of
    numbers, `(n,)` for a product of n sets such as `ℝ₊₊ × ℝ₊₊`, one axis per
    index set of a collection's domain followed by the shape of its entries,
    `(None,)` for `I → ℝ₊` and `(None, None)` for `I × K → ℝ₊`, the length of
    an axis being decided by the calibration alone, None where no set is
    declared. A name is read through the stage's named sets
    `declared_sets`."""
    declared = _set_named(declared, declared_sets or {})
    if declared is None:
        return None
    if isinstance(declared, T.Product):
        return (len(declared.factors),)
    if isinstance(declared, T.Comprehension):
        return _declared_shape(declared.base, declared_sets)
    if isinstance(declared, T.Functions):
        domain = _set_named(declared.domain, declared_sets or {})
        axes = len(domain.factors) if isinstance(domain, T.Product) else 1
        return (None,) * axes + tuple(_declared_shape(declared.codomain, declared_sets) or ())
    return ()
