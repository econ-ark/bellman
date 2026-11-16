"""The terms and statements of the fold: the symbol of a wire in a reduced
term and the wires a term reads, the substitution of wires and affinity in
them, the left side of a statement and the field it defines, and the walks
over a term that read its symbols, its expectations, its external calls and
the scopes of its arithmetic. Every other module of the fold reads terms
through these functions. `BlockLine` is one line of a block as the fold reads
it. `label_case` reads the weighted case operation that a term
`E_{s}((Q₁, …, Qₙ)[s])` over a label shock denotes.
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from bellman.distributions.families import FAMILY_ARGUMENTS, weighted_case
from bellman.fold.block_lines import DeclaredSides, header_of
from bellman.native.identity import Identity
from bellman.native.predicates import And, Compare, Not
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import PERCH_OF_SIDE, WRITTEN_MARK
from bellman.typing.line_unknowns import names_fields


def wire_symbol(wire):
    """A retained symbol standing for a wire in a reduced term: a constant
    named by the wire's identity, which no authored name can spell."""
    return T.Sym(T.Constant(wire))


def is_wire_symbol(node):
    """True for the symbol that stands for a wire: its name is an identity and
    not an authored name (AMD-SG-016 §3)."""
    return (
        isinstance(node, T.Sym)
        and isinstance(node.symbol, T.Constant)
        and isinstance(node.symbol.name, Identity)
    )


def wires_read(term):
    """The wires a reduced term reads, in order of first appearance."""
    wires = []
    for node in term_nodes(term):
        if is_wire_symbol(node):
            wires.append(node.symbol.name)
        elif isinstance(node, T.Call) and isinstance(node.fun, Identity):
            wires.append(node.fun)
    return tuple(dict.fromkeys(wires))


def substitute_wires(term, replacements):
    """A reduced term with the wire symbols of `replacements` (wire → term)
    replaced: the composition of two pointwise maps."""
    if is_wire_symbol(term):
        return replacements.get(term.symbol.name, term)
    if isinstance(term, T.Call) and isinstance(term.fun, Identity):
        function = replacements.get(term.fun)
        if is_wire_symbol(function):
            term = dataclasses.replace(term, fun=function.symbol.name)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return type(term)(
            *(
                substitute_wires(getattr(term, f.name), replacements)
                for f in dataclasses.fields(term)
            )
        )
    if isinstance(term, tuple):
        return tuple(substitute_wires(item, replacements) for item in term)
    return term


def affine_in(term, wires):
    """Whether ``term`` is affine in the wire symbols ``wires``: every wire
    enters only through terms of degree at most one, with coefficients free of
    every wire (AMD-SG-005 §3)."""
    wires = set(wires)

    def free(node):
        return not any(is_wire_symbol(n) and n.symbol.name in wires for n in term_nodes(node))

    def affine(node):
        if free(node):
            return True
        if is_wire_symbol(node):
            return True
        if isinstance(node, (T.Add, T.Sub)):
            return affine(node.left) and affine(node.right)
        if isinstance(node, T.Neg):
            return affine(node.operand)
        if isinstance(node, T.Mul):
            return (free(node.left) and affine(node.right)) or (
                free(node.right) and affine(node.left)
            )
        if isinstance(node, T.Div):
            return free(node.right) and affine(node.left)
        return False

    return affine(term)


def names_no_field(core) -> bool:
    """Whether a statement names no field on its left side: an inequality whose
    left side is neither a name nor a tuple of names (AMD-SG-017 §§1, 5.6). It
    states a relation and no equation, defines nothing, and is retained on the
    initial diagram with the obligation `retained-relation`."""
    inner = core.core if isinstance(core, T.Slack) else core
    return isinstance(inner, T.Inequality) and not names_fields(inner.lhs)


def stated_derivative(core):
    """The parts of a derivative line, `D_{m_d}V = 𝑑𝑢(c)` (AMD-MB-001 §4.3):
    the written spelling of the value, `V` or `V[<]`, the name of the
    coordinate in the subscript and the right-side term; None for a line
    whose left side is not one derivative term of one field."""
    inner = core.core if isinstance(core, T.Slack) else core
    if not isinstance(inner, T.Equation):
        return None
    lhs = inner.lhs
    if not (
        isinstance(lhs, T.Operator)
        and lhs.head == "D"
        and len(lhs.subs) == 1
        and len(lhs.args) == 1
        and isinstance(lhs.subs[0], T.Var)
        and isinstance(lhs.args[0], T.Sym)
        and isinstance(lhs.args[0].symbol, (T.Variable, T.Constant))
    ):
        return None
    return to_source(lhs.args[0]), lhs.subs[0].name, inner.rhs


def derivative_text(term):
    """A term as the stage file writes a derivative of a value, `D_{m_d}V`,
    `D_{k}V[<]`: the derivative operator with one subscript and one field as
    its argument is written without parentheses, as a derivative line writes
    its left side; every other term as `to_source` writes it. The objects an
    Evaluation stores and the selectors of a typing entry's path are spelled
    by this one function, so that the two agree (specification 0.7 D4)."""
    if (
        isinstance(term, T.Operator)
        and term.head == "D"
        and len(term.subs) == 1
        and len(term.args) == 1
        and isinstance(term.subs[0], T.Var)
        and isinstance(term.args[0], T.Sym)
    ):
        return f"D_{{{term.subs[0].name}}}{to_source(term.args[0])}"
    return to_source(term)


def path_text(path):
    """A path of a typing entry as written, `dcsn_to_arvl.evaluate[D_{k}V[<]]`:
    its segments joined by dots, each selector in brackets, a name or a
    position as it is and a term as `derivative_text` spells it."""
    segments = []
    for segment in path.segments:
        selectors = "".join(
            f"[{derivative_text(s.at) if isinstance(s, T.Term) else s.at}]"
            for s in segment.selectors
        )
        segments.append(segment.name + selectors)
    return ".".join(segments)


def defined_name(core):
    """(name, side) of the field a statement defines, None where its left side
    names none; a derivative line states a derivative of a field and defines
    none."""
    if names_no_field(core) or stated_derivative(core) is not None:
        return None
    lhs = core.lhs if isinstance(core, (T.Equation, T.Inequality)) else core.core.lhs
    return next(iter(symbol_occurrences(lhs)), None)


class BlockLine(NamedTuple):
    """One line of a block as the fold reads it: its address, its role and its
    retained term, the core of its statement."""

    address: str
    role: str
    core: object


def defined_field(ctx, name, core):
    """The identity of the field a statement of block `name` defines, the
    first where its left side names several, None where it names none."""
    found = ctx.defined(core, name)
    return found[0] if found else None


def defining_line(ctx, name, lines, identity):
    """The line of block `name` that defines the field `identity`, or None."""
    return next((line for line in lines if defined_field(ctx, name, line.core) == identity), None)


def statement_core(stmt):
    """The core of a retained statement; a core is its own."""
    return stmt.core if isinstance(stmt, T.Statement) else stmt


def retained_term_at(lines, address):
    """The retained term of the line at `address`."""
    return next(core for a, _, core in lines if a == address)


def right_side(core):
    """The right side of an equation, with or without a complementarity
    clause."""
    return core.core.rhs if isinstance(core, T.Slack) else core.rhs


def header_identities(box):
    """The identities a block's header declares, its inputs then its outputs.
    A block of an initial diagram has no input wire for a control its header
    names, so the fold reads the header and not the box's own domain
    (AMD-SG-013 §3)."""
    sides = header_of(box)
    return DeclaredSides(
        inputs=tuple(sort.identity for sort in sides.inputs),
        outputs=tuple(sort.identity for sort in sides.outputs),
    )


def wire_identities(ty):
    """The identities of the wires on one side of a box, `box.dom` or
    `box.cod`."""
    return tuple(ob.identity for ob in ty.inside)


def expectation_nodes(core):
    """The E operator nodes of a term in pre-order, the order in which their
    occurrences are numbered."""
    return [n for n in term_nodes(core) if isinstance(n, T.Operator) and n.head == "E"]


def expectation_occurrences(core):
    """(shock names, integrand) for each E_{...}(...) occurrence in a term."""
    out = []
    for n in term_nodes(core):
        if isinstance(n, T.Operator) and n.head == "E":
            shocks = tuple(s.var if isinstance(s, T.In) else s.name for s in n.subs)
            out.append((shocks, n.args[0]))
    return out


# The families the calculus extends into measures itself are read from the one
# table of the arguments each family takes (`FAMILY_ARGUMENTS`): their calls,
# nested ones included, are the declared distribution algebra and no external
# providers, so a LogNormal component of a Mixture is not an external call.
# Every other callable in a distribution declaration that is no declared
# definition, and every callable of a statement that no definition declares,
# is an external provider whose signature the stage does not fix.


def external_calls(core, declared, distributions=False):
    """The names of the calls in a term that no authored
    definition declares."""
    out = []
    for n in term_nodes(core):
        if (
            isinstance(n, T.Call)
            and n.fun not in declared
            and n.fun != "Inv"
            and not (distributions and n.fun in FAMILY_ARGUMENTS)
        ):
            if n.fun not in out:
                out.append(n.fun)
    return out


def symbol_occurrences(core, skip_expectations=False):
    """(name, side or None) of every symbol occurrence in a term, in order;
    binder names of operators are excluded; with `skip_expectations`, the
    occurrences inside an expectation are excluded too."""
    bound = {
        s.var if isinstance(s, T.In) else s.name
        for n in term_nodes(core)
        if isinstance(n, T.Operator)
        for s in n.subs
    }
    out = []
    for n in nodes_outside_expectations(core) if skip_expectations else term_nodes(core):
        if isinstance(n, T.Sym):
            if isinstance(n.symbol, T.Variable):
                out.append(
                    (
                        n.symbol.name,
                        n.symbol.when.side if isinstance(n.symbol.when, T.At) else None,
                    )
                )
            elif isinstance(n.symbol, T.Constant) and n.symbol.name not in bound:
                out.append((n.symbol.name, None))
        elif isinstance(n, T.Key) and isinstance(n.at, str) and n.at not in bound:
            out.append((n.at, None))
    return out


def term_of_name(name, side):
    """The term of a name as written: a variable under its perch mark, or a
    bare constant."""
    return T.Sym(T.Variable(name, T.At(side), 0)) if side is not None else T.Sym(T.Constant(name))


def spelled_with_mark(spelling):
    """A (name, side) spelling as the file writes it, the name with its perch
    mark, `c[>]`."""
    name, side = spelling
    return name + WRITTEN_MARK.get(PERCH_OF_SIDE.get(type(side)), "")


def authored_spelling(wire):
    """The authored spelling of the field a function wire carries, or the
    wire itself for an occurrence's result."""
    if wire.carries_field and wire.kind in ("function", "choice"):
        return wire.field + WRITTEN_MARK.get(wire.perch, "")
    return wire


def coordinate_declared_set(coordinate):
    """The set a coordinate is declared in, or None."""
    for c in coordinate.classifiers:
        if isinstance(c, T.Domain):
            return c.space
    return None


def term_nodes(node):
    """Every node of a term in pre-order, the term itself first."""
    yield node
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        for f in dataclasses.fields(node):
            yield from term_nodes(getattr(node, f.name))
    elif isinstance(node, tuple):
        for item in node:
            yield from term_nodes(item)


def nodes_outside_expectations(node):
    """The nodes of a term outside its expectations: an E operator is yielded
    and not entered."""
    yield node
    if isinstance(node, T.Operator) and node.head == "E":
        return
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        for f in dataclasses.fields(node):
            yield from nodes_outside_expectations(getattr(node, f.name))
    elif isinstance(node, tuple):
        for item in node:
            yield from nodes_outside_expectations(item)


def arithmetic_nodes(core):
    """The arithmetic nodes of a term in pre-order."""
    return [
        n for n in term_nodes(core) if isinstance(n, (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg))
    ]


def case_guards(test, guard):
    """The predicates selecting the two branches within the enclosing guard."""
    relation = {T.Lt: "<", T.Le: "<=", T.Eq: "=", T.Ge: ">=", T.Gt: ">"}
    condition = Compare(test.left, relation[type(test.op)], test.right)
    if guard is None:
        return condition, Not(condition)
    return And(guard, condition), And(guard, Not(condition))


def guarded_term_nodes(node, guard=None):
    """Each term and the predicate that selects its branch."""
    yield node, guard
    if isinstance(node, T.Conditional):
        then, otherwise = case_guards(node.test, guard)
        yield from guarded_term_nodes(node.test, guard)
        yield from guarded_term_nodes(node.then, then)
        yield from guarded_term_nodes(node.otherwise, otherwise)
    elif dataclasses.is_dataclass(node) and not isinstance(node, type):
        for field in dataclasses.fields(node):
            yield from guarded_term_nodes(getattr(node, field.name), guard)
    elif isinstance(node, tuple):
        for item in node:
            yield from guarded_term_nodes(item, guard)


def arithmetic_nodes_with_scopes(node, ctx, block, local, guard=None, *, guards=False):
    """Each arithmetic node with the sets of its bound names and its guard."""
    if isinstance(node, (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)):
        yield (node, local, guard) if guards else (node, local)
    if isinstance(node, T.Operator):
        scope = dict(local)
        for sub in node.subs:
            if isinstance(sub, T.In):
                yield from arithmetic_nodes_with_scopes(
                    sub.set, ctx, block, local, guard, guards=guards
                )
                scope[sub.var] = sub.set
            elif isinstance(sub, T.Var):
                scope[sub.name] = ctx.sets.get(ctx.resolve(sub.name, block))
        for argument in node.args:
            yield from arithmetic_nodes_with_scopes(
                argument, ctx, block, scope, guard, guards=guards
            )
    elif isinstance(node, T.Conditional):
        then, otherwise = case_guards(node.test, guard)
        yield from arithmetic_nodes_with_scopes(node.test, ctx, block, local, guard, guards=guards)
        yield from arithmetic_nodes_with_scopes(node.then, ctx, block, local, then, guards=guards)
        yield from arithmetic_nodes_with_scopes(
            node.otherwise, ctx, block, local, otherwise, guards=guards
        )
    elif dataclasses.is_dataclass(node) and not isinstance(node, type):
        for field in dataclasses.fields(node):
            yield from arithmetic_nodes_with_scopes(
                getattr(node, field.name), ctx, block, local, guard, guards=guards
            )
    elif isinstance(node, tuple):
        for item in node:
            yield from arithmetic_nodes_with_scopes(item, ctx, block, local, guard, guards=guards)


def label_case(ctx, term, block, *, owner=None):
    """The weighted case operation a term `E_{s}((Q₁, …, Qₙ)[s])` over a label
    shock denotes: a term in the line's names with the weights the law of `s`
    writes; None for any other term, and on a `WorkingStage`, which holds no
    definitions table yet."""
    if not (
        isinstance(term, T.Operator)
        and term.head == "E"
        and len(term.subs) == 1
        and len(term.args) == 1
    ):
        return None
    name = term.subs[0].var if isinstance(term.subs[0], T.In) else term.subs[0].name
    argument = term.args[0]
    if not (
        isinstance(argument, T.Select)
        and isinstance(argument.family, T.Tuple)
        and isinstance(argument.sel, T.Key)
        and argument.sel.at == name
        and ctx.labels(ctx.resolve(name, block))
    ):
        return None
    if owner is None:
        table = getattr(ctx.stage_object, "definitions", None)
        law = (
            table.get(Identity("distribution", stage=ctx.stage_name, subjects=(name,)))
            if table is not None
            else None
        )
        if law is None:
            return None
        declared = law.equations[0].law
    else:
        declared = owner.term
    if name in ctx.law_formals:
        from bellman.fold.stage_fold import stage_blocks_of
        from bellman.typing.ranges import substituted

        if owner is None:
            owner = next(
                owner
                for owner in stage_blocks_of(ctx.stage_object).owners
                if name in owner.subjects
            )
        replacements = {}
        for formal, actual in zip(owner.formals, owner.actuals):
            supplied = wire_symbol(ctx.function_wire(actual))
            replacements[T.Sym(T.Constant(formal))] = supplied
            replacements[T.Key(formal)] = T.Term(supplied)
        declared = substituted(declared, replacements)
    return weighted_case(declared, argument.family.items)
