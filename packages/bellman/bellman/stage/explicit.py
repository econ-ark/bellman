"""The explicit solution of a builder, `!explicit` (AMD-MT-003 build contract
§5).

An author who knows the solution of a policy or backward value builder in
closed form types `!explicit` on the builder in the header of a block of an
addition, `[id=policy, policy.method : !explicit]`, and writes in that block
one line `output = expression` for each output of the builder: the
consumption function `c = κ*(m - L)` of the perfect-foresight model, or its
decision value. The lines stand in place of the declared lines at the
operative level, as the lines of every solution method do, and the declared
optimization problem stays the builder's statement at the declared level,
`stage.declared`. The compiled kernel of each output's row evaluates the
expression; compiling it establishes an evaluator and no optimality.

An expression may read the states of the builder's output perch, the
parameters, the derived parameters and the local names the block's earlier
lines define. Two checks refuse, under `explicit-solution`, what is no
explicit solution. `check_addition`, on the declared level before the
operative level is constructed, refuses an `!explicit` builder that is a
forward builder, one to which no addition appends a line in a block of the
builder's id, and a block whose lines write no output of the builder, each
at the typing entry. `check_explicit`, on the operative level, refuses at
the position of the line at fault a line that reads an input of the
builder's header, a value input or a derivative of one, `V[>]` or
`D_{a}V[>]`, or a control at which a value builder's declared lines are
read; a line that states a relation rather than defining a name; a line
whose right side applies an operator, `argmax`, `solve`, `E` or `D` among
them, since a line that chooses, solves, integrates or differentiates writes
no explicit function; and a line that defines or reads a field at another
perch, the candidate `c[>]` of a grid method or its identification
`c = c[>]`. The left side `D_{m}V` of an authored marginal line applies no
operator. Each refusal names the method under which such a line is written:
`!egm` for a field at another perch, and `!egm` or `!time_iteration` for a
relation, an input read and an operator. The conditions under which an
expression is defined, a positive base of a power or a nonzero divisor, are
the obligations the construction records and calibration decides.

That the compiler writes each output's kernel is checked where the version
is bound, after the construction, by `components.check_components`: the
kernel compiler, `stage/kernels.py`, stands above the construction that
calls these checks (`levels.construct`), and this module, which the
construction reads, imports nothing above it.

A block that satisfies the rules of the lines is a complete formula-only
block. `formula_only` answers whether a block is one, and the construction
refuses such a block under `!egm` and `!time_iteration`, naming `!explicit`
(`levels.construct`); a block of those methods that reads a value input or
states the relation the method solves is no such block and is checked by the
method's own rules.
"""

from __future__ import annotations

from bellman.fold.block_lines import blocks_of, header_of
from bellman.fold.stage_names import StageNames, lines_of
from bellman.fold.wire_terms import (
    spelled_with_mark,
    stated_derivative,
    symbol_occurrences,
    term_nodes,
)
from bellman.native.records import refuse_at_entry
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import CONTROL, DOC, SHOCK, VALUE_ROLES, WRITTEN_MARK

__all__ = (
    "CHOICES",
    "check_addition",
    "check_explicit",
    "explicit_faults",
    "formula_only",
    "method_entry",
)

# the operators that choose or solve, which a representation's expression
# does not apply either (`representations`); an explicit line applies no
# operator at all
CHOICES = ("argmax", "solve", "upper_env")

# the methods that compute a policy from what it satisfies, which a refusal
# names as the methods under which a relation, an input read or an operator
# is written
SOLVING_METHODS = (
    "!egm or !time_iteration, whose block reads the continuation value and states what the "
    "policy satisfies"
)


def method_entry(stage, block):
    """The typing record of the method component of the builder `block`, the
    entry `policy.method : !explicit`, or None."""
    return next(
        (
            record
            for record in stage.definitions.values()
            if record.kind == "typing"
            and record.identity.address == block
            and record.identity.field == "method"
        ),
        None,
    )


def _spelled(identity):
    """An output of a header as the file writes it, the field with the mark
    of its perch, `V[<]`."""
    return identity.field + WRITTEN_MARK.get(identity.perch, "")


def _forward_fault(ctx, block, outputs):
    """The fault of a builder whose outputs are neither a policy nor a
    value, a forward builder; None for a policy or backward value builder."""
    if any(
        ctx.role(identity) in VALUE_ROLES or ctx.role(identity) == CONTROL for identity in outputs
    ):
        return None
    return (
        f"{block!r} is a forward builder, the push-forward of a measure through its law "
        "of motion, which writes neither a policy nor a value; !explicit is typed on the "
        "policy builder or on a backward value builder",
        "Type !explicit on the policy builder or on a backward value builder",
    )


def check_addition(stage, block, lines):
    """The check of the builder `block` whose method is `!explicit` on the
    reading `stage` of the stage at its declared level, before the operative
    level is constructed: `lines` are the statements an addition appends to
    the block of the builder's id whose header types the method, empty where
    no addition appends one. A forward builder, a builder with no appended
    line and a block whose lines write no output of the builder are refused
    under `explicit-solution` at the entry that types the method, with the
    line to write; a block that also holds a relation is left to
    `check_explicit`, which refuses the relation at its line."""
    box = next(held for held in blocks_of(stage) if held.name == block)
    ctx = StageNames(stage)
    outputs = tuple(sort.identity for sort in header_of(box).outputs)
    fault = _forward_fault(ctx, block, outputs)
    first = _spelled(outputs[0])
    if fault is None and not lines:
        fault = (
            f"!explicit takes a block whose lines write the outputs of the builder {block!r} as "
            "explicit functions of the states of its perch and the parameters, and no addition "
            "appends a line to the block; the explicit lines are written in an addition, in a "
            f"block `[id={block}, {block}.method : !explicit]`, and stand in place of the "
            "declared lines at the operative level",
            f"Write in the methods file the block `[id={block}, {block}.method : !explicit] "
            f"{{ {first} = <expression> }}`",
        )
    # a block of defining lines none of which writes an output; a relation
    # among the lines is refused at its own line by `check_explicit`
    written = {_written(line.core) for line in lines}
    if fault is None and None not in written:
        missing = [_spelled(identity) for identity in outputs if _spelled(identity) not in written]
        if len(missing) == len(outputs):
            fault = (
                f"!explicit takes a block whose lines write the outputs of the builder {block!r} "
                "as explicit functions, and no line the addition appends writes "
                f"{', '.join(missing)}; write a line `{missing[0]} = <expression>` in the block",
                f"Write a line `{missing[0]} = <expression>` in the block `[id={block}]`",
            )
    if fault is not None:
        reason, write = fault
        refuse_at_entry(
            stage,
            block,
            method_entry(stage, block),
            "explicit-solution",
            reason,
            write=write,
            kind="builder",
        )


def _written(core):
    """The name a defining line writes, with its perch mark, `c` or `V[<]`;
    None for a line whose left side is no single name."""
    inner = core.core if isinstance(core, T.Slack) else core
    if not isinstance(inner, T.Equation) or not isinstance(inner.lhs, T.Sym):
        return None
    occurrence = next(iter(symbol_occurrences(inner.lhs)), None)
    return spelled_with_mark(occurrence) if occurrence is not None else None


def explicit_faults(stage, block):
    """The faults that keep the operative lines of the builder `block` of
    `stage` from being an explicit solution, in the order of the lines, each
    a triple of the sentence that states it, the edit that removes it and
    the address of the line at fault, None for a fault of no line; the empty
    tuple for a complete formula-only block. `stage` is the reading of the
    stage at its operative level, whose lines of the builder are the lines a
    solution method's addition appends, where one appends lines, and the
    stage file's lines otherwise; the stage file's lines are the operative
    lines of an `!egm` or `!time_iteration` builder alone, since
    `check_addition` refuses an `!explicit` builder with no appended line."""
    box = next((held for held in blocks_of(stage) if held.name == block), None)
    if box is None:
        return ((f"the stage has no builder {block!r}", None, None),)
    ctx = StageNames(stage)
    outputs = tuple(sort.identity for sort in header_of(box).outputs)
    roles = {identity: ctx.role(identity) for identity in outputs}
    fault = _forward_fault(ctx, block, outputs)
    if fault is not None:
        return (fault + (None,),)
    perch = outputs[0].perch
    inputs = {sort.identity for sort in header_of(box).inputs}
    faults, defined, local = [], {}, set()
    for _, line in lines_of(stage, box):
        if line.role == DOC or line.core is None:
            continue
        core = line.core
        where = f"the line `{line.address}`, `{to_source(core)}`,"
        derivative = stated_derivative(core)
        if derivative is None:
            fault = _defining_fault(ctx, block, perch, core, where)
            if fault is not None:
                faults.append(fault + (line.address,))
                continue
            (identity,) = ctx.defined(core, block)
            if identity in roles:
                defined.setdefault(identity, line.address)
            else:
                local.add(identity.field)
        inner = core.core if isinstance(core, T.Slack) else core
        rhs = derivative[2] if derivative is not None else inner.rhs
        fault = _reading_fault(ctx, block, perch, inputs, rhs, where, local)
        if fault is not None:
            faults.append(fault + (line.address,))
    for identity in outputs:
        if identity not in defined:
            spelled = _spelled(identity)
            faults.append(
                (
                    f"no line of the block {block!r} defines its output {spelled}; an explicit "
                    f"solution defines every output by a line `{spelled} = <expression>`; write "
                    f"a line `{spelled} = <expression>` in the block",
                    f"Write a line `{spelled} = <expression>` in the block `[id={block}]`",
                    None,
                )
            )
    return tuple(faults)


def _defining_fault(ctx, block, perch, core, where):
    """The fault of a line that defines no name by an expression at the
    builder's output perch: a relation, a complementarity, a left side that
    is no single name, and a name defined at another perch, the candidate of
    a grid method; None for a defining line."""
    if not isinstance(core, T.Equation) or not isinstance(core.lhs, T.Sym):
        return (
            f"{where} states a relation rather than defining one name by an expression; a "
            "relation the output satisfies is solved by a method that computes the solution; "
            f"write the line under {SOLVING_METHODS}",
            "Write the line as `<name> = <expression>`, or type !egm or !time_iteration on "
            "the builder for a block that states the relation",
        )
    symbol = core.lhs.symbol
    if not isinstance(symbol, T.Variable) or not isinstance(symbol.when, T.At):
        return None
    (identity,) = ctx.defined(core, block)
    if identity.kind == "field" and identity.perch not in (None, perch):
        return (
            f"{where} defines {to_source(core.lhs)}, a field at another perch, the candidate a "
            "grid method computes at each point of its grid; an explicit solution defines its "
            "outputs at the builder's own perch; write the line under !egm, whose block writes "
            "the candidate and the grid line",
            "Write the output as an expression of the states of the builder's output perch, or "
            "type !egm on the builder for a block that writes the candidate",
        )
    return None


def _reading_fault(ctx, block, perch, inputs, rhs, where, local):
    """The fault of a right side that reads an input of the builder's header,
    a value input or a derivative of one or a control at which a value
    builder's declared lines are read, a value, a field at another perch or
    a name the stage does not define, or that applies an operator; None for
    a right side that reads states of the output perch, parameters, derived
    parameters, functions and earlier local names. A derived parameter is
    admitted with the functions, among which `StageNames.function_names`
    holds it, since a kernel writes it through its definition (build
    contract §5). The reads are checked before the operators, so that a line
    `c = (β*D_{a}V[>])^(-1/ρ)` is refused for the value input it reads."""
    functions = ctx.function_names
    for name, side in symbol_occurrences(rhs):
        if name in functions or (side is None and name in local):
            continue
        identity = ctx.resolve(name, block, side)
        if identity.kind == "parameter":
            continue
        spelled = name + WRITTEN_MARK.get(identity.perch, "") if identity.perch else name
        role = ctx.role(identity) or ctx.role_by_name(identity)
        if identity in inputs and role == CONTROL:
            return (
                f"{where} reads {spelled}, a control input of the builder's header, at which its "
                "declared lines are read; an explicit function reads no value input and no "
                "control at which the declared lines are read, and is written on the states of "
                f"the builder's output perch; write the line under {SOLVING_METHODS}",
                f"Write the output as an expression that does not read {spelled}",
            )
        if role in VALUE_ROLES:
            return (
                f"{where} reads {spelled}, a value"
                + (" input of the builder" if identity in inputs else "")
                + ", or a derivative of it; an explicit solution reads no value input, since a "
                "line that reads one is an update of the solution; write the line under "
                f"{SOLVING_METHODS}",
                f"Write the output as an expression that does not read {spelled}",
            )
        if identity.kind == "field" and identity.perch not in (None, perch) and role != SHOCK:
            if side is not None:
                return (
                    f"{where} reads {spelled_with_mark((name, side))}, a field at another "
                    "perch, which the identification of a grid method reads; write the line "
                    "under !egm, whose block writes the candidate and the grid line",
                    "Write the output as an expression of the states of the builder's output "
                    "perch, or type !egm on the builder for a block that writes the candidate",
                )
            return (
                f"{where} reads {spelled}, a field at another perch; an explicit solution reads "
                "the states of the builder's output perch, the parameters, the derived "
                "parameters and the block's earlier local names",
                "Write the output as an expression of the states of the builder's output perch",
            )
        if identity.kind not in ("field", "parameter") and identity.kind != "shock":
            return (
                f"{where} reads {name}, which no earlier line of the block defines and which is "
                "no state, control or parameter of the stage",
                f"Define {name} by an earlier line of the block",
            )
    for node in term_nodes(rhs):
        if isinstance(node, T.Operator):
            return (
                f"{where} applies {node.head}, an operator; a line that chooses, solves, "
                "integrates or differentiates writes no explicit function; write the line under "
                f"{SOLVING_METHODS}, or type a method of the operator on the declared line",
                f"Write the output as an expression that applies no operator, or type a method "
                f"of `{node.head}`",
            )
    return None


def formula_only(stage, block):
    """Whether the operative lines of the builder `block` of `stage` are a
    complete formula-only block: every output defined by a line `output =
    expression` that reads no input of the header, states no relation,
    applies no operator and defines and reads no field at another perch.
    Such a block under `!egm` or `!time_iteration` is the block of
    `!explicit`."""
    return not explicit_faults(stage, block)


def check_explicit(stage, block, spans=None):
    """The check of the lines of the builder `block` whose method is
    `!explicit`, on the reading `stage` of the stage at its operative level:
    the first fault of `explicit_faults` is refused under
    `explicit-solution`, at the position of the line at fault, which `spans`,
    the span table of the operative level, holds at the line's address, and
    at the entry that types the method where no line is at fault or the
    table holds no position. That each output's row has an executable
    compiled kernel is checked where the version is bound
    (`components.check_components`)."""
    faults = explicit_faults(stage, block)
    if not faults:
        return
    reason, write, address = faults[0]
    span = spans.get(address) if spans is not None and address is not None else None
    if span is None:
        refuse_at_entry(
            stage,
            block,
            method_entry(stage, block),
            "explicit-solution",
            reason,
            write=write,
            kind="builder",
        )
    raise ConstructionError(
        f"stage {stage.name!r}, builder {block!r}: {reason}",
        stage=stage.name,
        file=span.file,
        line=span.line,
        column=span.column,
        end_line=getattr(span, "end_line", None),
        end_column=getattr(span, "end_column", None),
        address=block,
        rule="explicit-solution",
        write=write,
    )
