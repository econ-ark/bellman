"""The kernels of the laws of motion and of the value aggregators, as records
(AMD-SG-007 §3.1): `_KernelRecord`, the kernel a pullback, a push-forward or an
aggregation applies, with its argument names, its output names, the retained
term of each output, the declared sets and the printed lines, made by
`law_of_motion_kernel` for the law of motion g of a forward builder and by
`aggregator_kernel` for the segment of a value aggregator G an aggregation
applies, and `_KernelParts`, what the printed lines say. `stems_of` and
`distribution_arguments` are the names of a point and the conditioning
arguments of a distribution declaration, which the kernels and the names of
the wires print.
"""

from __future__ import annotations

import collections
import dataclasses
from itertools import zip_longest

from bellman.fold.block_lines import header_of
from bellman.fold.declared_sets import definedness_condition
from bellman.fold.stage_fold import law_of_motion_equations
from bellman.fold.stage_names import StageNames, branches_of, lines_of
from bellman.fold.wire_terms import (
    case_guards,
    expectation_nodes,
    guarded_term_nodes,
    is_wire_symbol,
    label_case,
    symbol_occurrences,
    term_nodes,
    term_of_name,
    wire_symbol,
)
from bellman.native.identity import Identity
from bellman.native.labels import italic, wire_spelling
from bellman.native.predicates import Not, Or
from bellman.native.provenance import source_file
from bellman.refusals import construction_error
from bellman.stage.boxes import builder_rows_of
from bellman.stage.grains import wire_table
from bellman.stage.places import block_box
from bellman.stage.term_operations import relation_of
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    ALIAS,
    PERCH_MARK,
    SHCK,
    VALUE,
    WRITTEN_MARK,
)
from bellman.typing import sets
from bellman.typing.typed_expressions import Unresolved, predicate_text

# --- the kernel records of g and G ---


@dataclasses.dataclass(frozen=True, eq=False)
class _KernelRecord:
    """A kernel as `kernel` prints it and `compile_kernel` writes as a Python function, made when
    asked for and stored nowhere: its letter (`g` or `G`), its title and the
    segment it is, the definition it belongs to and the address it comes
    from, the builder whose names its terms resolve in, the argument names and
    the position of each wire or coordinate identity among the arguments, the
    output names, the retained term of each output, the printed lines and the
    parts they are written from, the address of the statement or line that
    defines each output, and the declared set of each argument and of each
    output, None where none is declared.

    `parts` holds what the printed lines say — the rule, the components of the
    value, the arguments no component reads and what each component reads — so
    that a sheet asks the kernel for a part and never cuts a printed line
    again."""

    letter: str
    title: str
    segment: str
    identity: Identity
    address: str
    builder: str
    names: tuple
    index: dict
    outputs: tuple
    terms: tuple
    lines: tuple
    sources: tuple
    argument_sets: tuple
    output_sets: tuple
    parts: "_KernelParts"
    # the name each argument carries on the printed lines, which for an
    # expectation's result is its authored sub-expression and for every other
    # argument is the name a compiled kernel takes (AMD-SG-019 §2.4)
    shown: tuple = ()
    # the shocks a derivative piece's rule is integrated over, where the
    # derivative line's right side is one expectation (AMD-MB-001; MB-A18)
    integrated: tuple = ()
    # the derivative terms of value wires the terms read, each with the key
    # of the argument that stands for it, `(node, key)` (MB-A16, MB-A19)
    derivative_terms: tuple = ()
    boolean: bool = False
    activation: object = None
    expectations: tuple = ()
    fallback: "_KernelRecord | None" = None


@dataclasses.dataclass(frozen=True)
class _KernelParts:
    """The parts of a printed kernel (AMD-SG-007 §3.1): the rule
    `𝐺(V[>], m_d, c) = (𝑢(c) + V[>], 𝑑𝑢(c))`; the components of its value as
    the rule writes them; its output names; the arguments no component reads;
    what each component reads, where the components read different arguments;
    and whether the outputs are named at all, which a `g` of one output does
    not do."""

    rule: str
    values: tuple
    outputs: tuple
    unused: tuple
    per_output: tuple
    named_outputs: bool
    # the conditions on its arguments under which its rule is defined, where
    # the rule is undefined on part of the printed domain (AMD-SG-019 §2.4)
    restricted: tuple = ()


def kernel_record(stage, row):
    """The `_KernelRecord` of a law of motion or a value aggregator the box of
    a row applies; None where its kernel is neither. The one dispatch on the
    kind of a row, which `kernel` and the denotation of an operator read."""
    if row.kind in ("Pullback", "Pushforward"):
        return (
            law_of_motion_kernel(stage, row.definition)
            if getattr(row, "definition", None) in stage.definitions
            else None
        )
    return aggregator_kernel(stage, row) if row.kind == "Aggregation" else None


def law_of_motion_kernel(stage, identity, label=None, letter=None):
    """The complete law of motion g of a forward builder (AMD-SG-007 §3.1):
    its arguments the builder's listed states and controls and the shocks its
    equations read, in header order, and a branching law its label
    coordinate; one output for each state it produces, in the declared order,
    each an expression in those arguments with the builder's local
    definitions substituted.

    With `label`, a label of a branching law, the law read at that label, its
    section, whose name `letter` gives, `𝑔_keep≻`
    (`defining_expressions.section_identity`): the law's title and argument
    names, its arguments the law's but the label coordinate, as the card's
    `Where` section defines the section, and its outputs the fields the
    branch writes, in the declared order, each with the law's own component.
    A constant is an argument of the section where one of those components
    reads it. The other unused arguments and the reads are the section's
    (unit K of model interface spec 0.4, Task 14; decision K-I203)."""
    ctx = StageNames(stage)
    record = stage.definitions[identity]
    block = record.address
    box = block_box(stage, block)
    declared_in, declared_out = header_of(box)
    outputs = tuple(ob.identity for ob in declared_out)
    found, lines = {}, {}
    equations = law_of_motion_equations(
        ctx, block, tuple(stage.definitions[address].equations[0] for address in record.equations)
    )
    for core, address in zip_longest(equations, record.equations, fillvalue=block):
        equation = relation_of(core)
        defined = ctx.defined(equation, block)
        if defined and defined[0] in outputs:
            found[defined[0]] = equation.rhs
            lines[defined[0]] = address
    produced = tuple(output for output in outputs if output in found)
    terms = tuple(found[output] for output in produced)
    read = {
        ctx.resolve(name, block, side) for term in terms for name, side in symbol_occurrences(term)
    }
    read.update(
        ctx.resolve(node.fun, block)
        for term in terms
        for node in term_nodes(term)
        if isinstance(node, T.Call) and isinstance(node.fun, str)
    )
    # a shock is an argument where a line reads it, and the shock that selects
    # a branch where none does, the branch's section being g at its label
    keys = tuple(
        dict.fromkeys(
            ob.identity
            for ob in declared_in
            if ctx.role(ob.identity) in ("state", "control")
            or (
                ctx.role(ob.identity) == "shock"
                and (ob.identity in read or ctx.labels(ob.identity))
            )
            or (ob.identity in read and getattr(ctx.ports.get(ob.identity), "constant", False))
        )
    )
    names = _argument_names([(key, key.field) for key in keys], ctx.parameter_names)
    if label is not None:
        # The section fixes the label and includes only its own constant inputs.
        written = dict(branches_of(stage, box))[label]
        chosen = tuple(position for position, output in enumerate(produced) if output in written)
        produced = tuple(produced[position] for position in chosen)
        terms = tuple(terms[position] for position in chosen)
        used = set().union(*(_names_read(term, names, ctx, block) for term in terms))
        keys = tuple(
            key for key in keys
            if not ctx.labels(key) and (not ctx.ports[key].constant or key in used)
        )
    displayed = tuple(_displayed(term, names, ctx, block) for term in terms)
    reads = tuple(_names_read(term, names, ctx, block) for term in terms)
    output_names = tuple(wire_spelling(output) for output in produced)
    title = f"{italic('g')} of {block}"
    parts = _kernel_parts(
        letter or italic("g"), keys, names, output_names, displayed, reads, always_outputs=False
    )
    return _KernelRecord(
        letter="g",
        title=title,
        segment=block,
        identity=identity,
        address=block,
        builder=block,
        names=tuple(names[key] for key in keys),
        index={key: position for position, key in enumerate(keys)},
        outputs=output_names,
        terms=terms,
        lines=_formula_lines(title, parts),
        sources=tuple(lines[output] for output in produced),
        argument_sets=tuple(ctx.declared_set(key) for key in keys),
        output_sets=tuple(ctx.declared_set(output) for output in produced),
        parts=parts,
    )


def aggregator_kernel(stage, row):
    """The G segment an aggregation row applies (AMD-SG-007 §3.1): its value
    arguments named by `_value_argument_names`, an expectation's result by its
    authored sub-expression and a sub-builder's output by its declared name,
    then its coordinates; one output per component, in the row's order."""
    from bellman.stage.carriers import result_set

    ctx = StageNames(stage)
    block = row.builder
    rows_open, rows_closed = builder_rows_of(stage, block)
    node_outputs = {
        output
        for other in rows_open + rows_closed
        if other.kind == "Evaluation" and other.node is not None
        for output in other.outputs
    }
    inputs = tuple(row.inputs)
    controls = tuple(
        Identity("field", stage=stage.name, perch=policy.perch, field=policy.field)
        for policy in row.policy
    )
    coordinates = (
        tuple(i for i in row.arguments if i.perch != SHCK)
        + controls
        + tuple(i for i in row.arguments if i.perch == SHCK)
    )
    ordinary = [wire for wire in inputs if wire not in node_outputs]
    # the coordinate names the author wrote, which a chosen letter must
    # not take
    written = tuple(coordinate.field for coordinate in coordinates if coordinate not in inputs)
    rendering = wire_table(stage)
    letters = _value_argument_names(rendering, ordinary, written)
    kept = {
        term.symbol.name
        for term, output in zip(row.maps, row.outputs)
        if is_wire_symbol(term) and term.symbol.name.field == output.field
    }
    for wire in ordinary:
        sort = rendering.sort_of(wire)
        if getattr(sort, "constant", False) and (
            wire in kept or sets.callable_set(sort.domain, ctx.set_terms) is not None
        ):
            letters[wire] = wire.field
    given = [(wire, wire.field if wire in node_outputs else letters[wire]) for wire in inputs]
    given += [
        (coordinate, coordinate.field) for coordinate in coordinates if coordinate not in inputs
    ]
    names = _argument_names(given, ctx.parameter_names)
    keys = tuple(key for key, _ in given)
    # on the printed lines a value argument that is an expectation's result is
    # its authored sub-expression, as the obligations and the WHERE lines write
    # it (§2.4); the argument a compiled kernel takes keeps its letter, which a
    # sub-expression could not be
    shown = _shown_arguments(stage, keys, names)
    terms = tuple(row.maps)
    # a derivative term of a value the row reads, `D_{a}(V≻)`, is one more
    # argument of the kernel, named by the term's printed form, whose value
    # the caller supplies; nothing is differentiated (AMD-MB-001; MB-A16)
    keys, names, shown, terms, derivative_terms = _derivative_arguments(
        stage, keys, names, shown, terms, ctx, block
    )
    displayed = tuple(_displayed(term, shown, ctx, block) for term in terms)
    reads = tuple(_names_read(term, names, ctx, block) for term in terms)
    named = _kernel_output_name if len(row.outputs) > 1 else kernel_output_name
    outputs = tuple(named(stage, output) for output in row.outputs)
    letter = italic("G")
    title = (
        f"{letter} of {block}"
        if row.identity == Identity("Aggregation", address=block)
        else f"{letter} of {block}, segment {row.identity}"
    )
    address = row.statements[0] if row.statements else block
    # an output is defined by the statement in its position when the row
    # represents one statement per output
    sources = (
        tuple(row.statements)
        if len(row.statements) == len(row.outputs)
        else (address,) * len(row.outputs)
    )
    parts = _kernel_parts(letter, keys, shown, outputs, displayed, reads, always_outputs=True)
    input_sets = {
        key: result_set(ctx, sort) if key.kind == "Expectation" else sort.domain
        for key in inputs
        if (sort := rendering.sort_of(key)) is not None
    }
    # an expectation whose result set is not derived is given no set here
    input_sets = {
        key: None if isinstance(found, Unresolved) else found for key, found in input_sets.items()
    }
    return _KernelRecord(
        letter="G",
        title=title,
        segment=row.identity,
        identity=row.definition or Identity("G", stage=stage.name, address=block),
        address=address,
        builder=block,
        names=tuple(names[key] for key in keys),
        index={key: position for position, key in enumerate(keys)},
        outputs=outputs,
        terms=terms,
        lines=_formula_lines(title, parts),
        sources=sources,
        argument_sets=tuple(
            input_sets[key]
            if key in input_sets
            else None
            if key.kind == "function"
            else ctx.declared_set(key)
            for key in keys
        ),
        output_sets=tuple(_evaluated_output_set(ctx, rendering, output) for output in row.outputs),
        parts=parts,
        shown=tuple(shown[key] for key in keys),
        derivative_terms=derivative_terms,
    )


def aggregation_output_record(stage, record, position):
    """One output formula and the arguments needed to evaluate it."""
    ctx = StageNames(stage)
    term = record.terms[position]
    keys = tuple(sorted(record.index, key=record.index.get))
    names = dict(zip(keys, record.names))
    shown = dict(zip(keys, record.shown or record.names))
    read = _names_read(term, names, ctx, record.builder)
    selected = tuple(key for key in keys if key in read)
    if len(record.terms) == 1 and selected == keys:
        return record
    output = (record.outputs[position],)
    displayed = (_displayed(term, shown, ctx, record.builder),)
    parts = _kernel_parts(
        italic(record.letter), selected, shown, output, displayed, (read,), always_outputs=True
    )
    return dataclasses.replace(
        record,
        names=tuple(names[key] for key in selected),
        index={key: position for position, key in enumerate(selected)},
        outputs=output,
        terms=(term,),
        lines=_formula_lines(record.title, parts),
        sources=(record.sources[position],),
        argument_sets=tuple(record.argument_sets[record.index[key]] for key in selected),
        output_sets=(record.output_sets[position],),
        parts=parts,
        shown=tuple(shown[key] for key in selected),
    )


def guard_kernel_record(stage, builder, subject, predicate, term, scope):
    """An explicit Boolean kernel on the coordinates the guard reads."""
    ctx = StageNames(stage)
    table = wire_table(stage)
    known = {} if scope is None else scope.index
    arguments = {}
    for node in term_nodes(term):
        if is_wire_symbol(node):
            key = node.symbol.name
        elif isinstance(node, T.Sym) and isinstance(node.symbol, (T.Constant, T.Variable)):
            key = _argument_identity(node, ctx, builder)
        elif isinstance(node, T.Call):
            key = node.fun if isinstance(node.fun, Identity) else ctx.resolve(node.fun, builder)
        elif isinstance(node, T.Key):
            key = ctx.resolve(node.at, builder)
        else:
            continue
        retained_expectation = (
            scope is not None and isinstance(key, Identity)
            and _expectation_source(stage, key) is not None
        )
        if key in known or key in ctx.ports or key in table.produced or retained_expectation:
            arguments[key] = (
                scope.names[known[key]] if key in known else key.field or str(key)
            )
    names = _argument_names(tuple(arguments.items()), ctx.parameter_names)
    keys = tuple(names)
    shown = names
    keys, names, shown, terms, _ = _derivative_arguments(
        stage, keys, names, shown, (term,), ctx, builder
    )
    read = _names_read(terms[0], names, ctx, builder)
    keys = tuple(key for key in keys if key in read)
    title = f"guard of {subject}"
    return _KernelRecord(
        letter="guard",
        title=title,
        segment=subject,
        identity=subject,
        address=builder,
        builder=builder,
        names=tuple(names[key] for key in keys),
        index={key: position for position, key in enumerate(keys)},
        outputs=("active",),
        terms=terms,
        lines=(title, predicate_text(predicate)),
        sources=(builder,),
        argument_sets=tuple(
            scope.argument_sets[known[key]] if key in known else table.sort_of(key).domain
            for key in keys
        ),
        output_sets=(None,),
        parts=None,
        boolean=True,
    )


def derivative_term_of_field(node):
    """Whether a node is a derivative term of one field, `D_{m_next}V[>]`: the
    operator `D` with one subscript and one argument that is a field symbol
    (AMD-MB-001 §4.2)."""
    return (
        isinstance(node, T.Operator)
        and node.head == "D"
        and len(node.subs) == 1
        and len(node.args) == 1
        and isinstance(node.subs[0], T.Var)
        and isinstance(node.args[0], T.Sym)
        and isinstance(node.args[0].symbol, (T.Variable, T.Constant))
    )


def _replaced(term, replacements):
    """`term` with each symbol or operator node equal to a key of
    `replacements` replaced by its value, the tree rebuilt around it."""
    if isinstance(term, (T.Sym, T.Operator)) and term in replacements:
        return replacements[term]
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return type(term)(
            *(_replaced(getattr(term, f.name), replacements) for f in dataclasses.fields(term))
        )
    if isinstance(term, tuple):
        return tuple(_replaced(item, replacements) for item in term)
    return term


_SIDE_OF_PERCH = {"arvl": T.Arrival(), "cntn": T.Continuation()}


def _derivative_source(stage, block, term, address):
    """A derivative with local aliases resolved and expectations identified."""
    aliases = {}
    for _, line in lines_of(stage, block_box(stage, block)):
        if line.role != ALIAS or not isinstance(line.core, T.Equation):
            continue
        left = line.core.lhs
        if isinstance(left, T.Sym) and isinstance(left.symbol, T.Constant):
            aliases[left.symbol.name] = (line.address, line.core.rhs)
    order = {
        id(node): Identity("Expectation", address=place, occurrence=number)
        for place, body in ((address, term), *aliases.values())
        for number, node in enumerate(expectation_nodes(body), 1)
    }
    identities = {}

    def expand(node, active=frozenset()):
        if isinstance(node, T.Sym) and isinstance(node.symbol, T.Constant):
            name = node.symbol.name
            if name in aliases and name not in active:
                return expand(aliases[name][1], active | {name})
        if isinstance(node, tuple):
            return tuple(expand(item, active) for item in node)
        if not dataclasses.is_dataclass(node) or isinstance(node, type):
            return node
        resolved = dataclasses.replace(
            node,
            **{field.name: expand(getattr(node, field.name), active)
               for field in dataclasses.fields(node)},
        )
        if id(node) in order:
            identities[id(resolved)] = order[id(node)]
        return resolved

    return expand(term), identities


def _derivative_expectation_terms(term, identities):
    """The derivative's integrands and the terms reading their results."""
    from bellman.stage.stage_answers import _add_primitive_guard

    scopes, guards = {}, {}

    def read(node, guard=None):
        if isinstance(node, T.Operator) and node.head == "E":
            integrand = read(node.args[0], guard)
            occurrence = identities[id(node)]
            result = dataclasses.replace(occurrence, mark="result")
            shocks = tuple(sub.var if isinstance(sub, T.In) else sub.name for sub in node.subs)
            fallback = _without_expectations(node.args[0])
            scopes.setdefault(occurrence, (result, shocks, integrand, fallback))
            _add_primitive_guard(guards, occurrence, guard)
            return wire_symbol(result)
        if isinstance(node, T.Conditional):
            test = read(node.test, guard)
            then, otherwise = case_guards(test, guard)
            return T.Conditional(test, read(node.then, then), read(node.otherwise, otherwise))
        if dataclasses.is_dataclass(node) and not isinstance(node, type):
            return dataclasses.replace(
                node,
                **{field.name: read(getattr(node, field.name), guard)
                   for field in dataclasses.fields(node)},
            )
        if isinstance(node, tuple):
            return tuple(read(item, guard) for item in node)
        return node

    value = read(term)
    return value, tuple(
        (occurrence, result, shocks, integrand, guards[occurrence], fallback)
        for occurrence, (result, shocks, integrand, fallback) in scopes.items()
    )


def _without_expectations(term):
    """The derivative where its local expectations are inactive."""
    if not expectation_nodes(term):
        return term
    if not isinstance(term, T.Conditional) or expectation_nodes(term.test):
        return None
    then, otherwise = _without_expectations(term.then), _without_expectations(term.otherwise)
    if then is None:
        return otherwise
    if otherwise is None:
        return then
    return T.Conditional(term.test, then, otherwise)


def derivative_kernel(stage, evaluation, entry, aggregation):
    """The stated derivative, with separate records for distinct expectations.

    A sole expectation at the root keeps the existing integrand calling
    convention. Other expectations have their original occurrence identities,
    and their results are arguments to the terms that read them.
    """
    coordinate, term, address, source, value = entry
    base = aggregator_kernel(stage, aggregation)
    ctx = StageNames(stage)
    block = evaluation.builder
    base_keys = tuple(sorted(base.index, key=base.index.get))
    declared = dict(zip(base_keys, base.argument_sets))
    names = dict(zip(base_keys, base.names))
    shown = dict(zip(base_keys, base.shown or base.names))
    term, identities = _derivative_source(stage, block, term, address)
    expectations = expectation_nodes(term)
    fused = len(expectations) == 1 and expectations[0] is term
    shocks, extracted = (), ()
    if fused:
        shocks = tuple(sub.var if isinstance(sub, T.In) else sub.name for sub in term.subs)
        rule = term.args[0]
    elif expectations:
        rule, extracted = _derivative_expectation_terms(term, identities)
    else:
        rule = term
    replacements = {
        term_of_name(key.field, _SIDE_OF_PERCH.get(key.perch)): wire_symbol(key)
        for key in aggregation.inputs
        if key in base.index and key.field
    }
    derivative_keys = []
    for node in term_nodes(term):
        if not derivative_term_of_field(node) or node in replacements:
            continue
        printed = to_source(node)
        name, side = spelling(node.args[0])
        perch = ctx.resolve(name, block, side).perch
        key = Identity("function", stage=stage.name, perch=perch, field=printed)
        derivative_keys.append(key)
        names[key] = shown[key] = printed
        declared[key] = None
        replacements[node] = wire_symbol(key)

    def coordinate_key(name, side=None):
        key = ctx.resolve(name, block, side)
        if key not in names:
            names[key] = shown[key] = name
            declared[key] = ctx.declared_set(key)
        return key

    if extracted:
        for node in term_nodes(term):
            if isinstance(node, T.Sym) and isinstance(node.symbol, (T.Constant, T.Variable)):
                name, side = spelling(node)
                if isinstance(name, str) and ctx.resolve(name, block, side) in ctx.ports:
                    coordinate_key(name, side)
        for _, result, _, _, _, _ in extracted:
            names[result] = str(result)
            shown[result] = _expectation_source(stage, result) or names[result]
            declared[result] = None
    elif fused:
        for name in shocks:
            coordinate_key(name)

    def record(source_term, output, segment, integrated=(), *, activation=None, exact=True):
        source_term = _replaced(source_term, replacements)
        shock_keys = tuple(coordinate_key(name) for name in integrated)
        read = _names_read(source_term, names, ctx, block)
        if exact:
            keys = tuple(key for key in names if key in read and key not in shock_keys)
            arguments = (
                tuple(key for key in keys if key not in derivative_keys)
                + shock_keys
                + tuple(key for key in derivative_keys if key in read)
            )
        else:
            arguments = base_keys + tuple(derivative_keys)
        displayed = (_displayed(source_term, shown, ctx, block),)
        title = f"derivative of {block} stated at {address}"
        if integrated:
            title += f", the integrand over {', '.join(integrated)}"
        parts = _kernel_parts(
            output, arguments, shown, (output,), displayed, (read,), always_outputs=True
        )
        lines = _formula_lines(title, parts)
        if integrated:
            lines += (f"integrated over {', '.join(integrated)}",)
        return _KernelRecord(
            letter="D",
            title=title,
            segment=segment,
            identity=base.identity,
            address=address,
            builder=block,
            names=tuple(names[key] for key in arguments),
            index={key: position for position, key in enumerate(arguments)},
            outputs=(output,),
            terms=(source_term,),
            lines=lines,
            sources=(address,),
            argument_sets=tuple(declared[key] for key in arguments),
            output_sets=(None,),
            parts=parts,
            shown=tuple(shown[key] for key in arguments),
            integrated=integrated,
            activation=None if activation is None else _replaced(activation, replacements),
        )

    output = f"D_{{{coordinate.field}}}{value.field}{WRITTEN_MARK.get(value.perch, '')}"
    outer = record(rule, output, evaluation.identity, shocks, exact=bool(expectations))
    if not extracted:
        return outer
    parts = []
    for occurrence, result, integrated, integrand, activation, fallback in extracted:
        part = record(integrand, names[result], occurrence, integrated, activation=activation)
        if fallback is not None:
            # A fallback is meaningful only for an integrand that reads a child result.
            if any(key.kind == "Expectation" for key in part.index):
                part = dataclasses.replace(
                    part, fallback=record(fallback, names[result], occurrence)
                )
        parts.append(part)
    fallback = _without_expectations(term)
    return dataclasses.replace(
        outer,
        expectations=tuple(parts),
        fallback=None if fallback is None else record(fallback, output, evaluation.identity),
    )


def _derivative_arguments(stage, keys, names, shown, terms, ctx, block):
    """The keys, names, shown names and terms of a kernel with one argument
    added for each derivative term of a value wire its terms read, `D_{a}(V≻)`
    of the inverse Euler line: the argument is named by the term as the rule
    prints it, keyed by an identity of kind `function` at the value's perch,
    and the term is read as that argument. A derivative of a declared
    function, `D_{c}(𝑢)`, is no such term and stays as written, for the
    writer to refuse under `kernel-form`."""
    keys, names, shown = list(keys), dict(names), dict(shown)
    replacements = {}
    for term in terms:
        for node in term_nodes(term):
            if (
                node in replacements
                or not derivative_term_of_field(node)
                or not is_wire_symbol(node.args[0])
            ):
                continue
            wire = node.args[0].symbol.name
            printed = to_source(_displayed(node, shown, ctx, block))
            key = Identity("function", stage=stage.name, perch=wire.perch, field=printed)
            keys.append(key)
            names[key] = shown[key] = printed
            replacements[node] = wire_symbol(key)
    pairs = tuple((node, symbol.symbol.name) for node, symbol in replacements.items())
    if not replacements:
        return tuple(keys), names, shown, terms, pairs
    return tuple(keys), names, shown, tuple(_replaced(term, replacements) for term in terms), pairs


def _kernel_parts(letter, keys, names, outputs, displayed, reads, *, always_outputs):
    """The parts of a printed kernel (AMD-SG-007 §3.1): the rule
    `letter(arguments) = value`, the value one term or the tuple of the
    components, the outputs, the arguments no component reads, and for several
    components what each component reads. A kernel on a value bundle answers
    per component: each component names its own arguments, in place of the
    arguments it does not read, which on a paired G is every argument of every
    other component (AMD-SG-011 §3)."""
    values = tuple(to_source(term) for term in displayed)
    value = values[0] if len(values) == 1 else "(" + ", ".join(values) + ")"
    rule = f"{letter}({', '.join(names[key] for key in keys)}) = {value}"
    unused = tuple(names[key] for key in keys if not any(key in read for read in reads))
    taken = [tuple(names[key] for key in keys if key in read) for read in reads]
    per_output = tuple(zip(outputs, taken)) if len(outputs) > 1 and len(set(taken)) > 1 else ()
    return _KernelParts(
        rule=rule,
        values=values,
        outputs=tuple(outputs),
        unused=unused,
        per_output=per_output,
        named_outputs=bool(always_outputs or len(outputs) != 1),
        restricted=_restrictions(displayed, {names[key] for key in keys}),
    )


def _restrictions(displayed, arguments):
    """The conditions on a kernel's arguments under which its rule is defined,
    where the rule is undefined on part of the domain its signature prints: the
    guard of each power and of each division inside the rule that reads one of
    the arguments (AMD-SG-019 §2.4). A kernel that carries one is a partial map
    and prints the partial arrow with a `defined where` line for each
    condition. A guard that reads parameters alone restricts the calibration
    and not the domain, and stays under WHERE where the card prints it."""
    found = []
    for term in displayed:
        for node, guard in guarded_term_nodes(term):
            condition = definedness_condition(node)
            if condition is None:
                continue
            if guard is not None:
                condition = Or(Not(guard), condition)
            if not {name for name, _ in symbol_occurrences(condition)} & arguments:
                continue
            text = predicate_text(condition)
            if text not in found:
                found.append(text)
    return tuple(found)


def _formula_lines(title, parts):
    """The printed kernel, written from its parts: the title and the rule, then
    the outputs, the arguments no component reads and what each component
    reads."""
    lines = [f"{title}: {parts.rule}"]
    said = []
    if parts.named_outputs:
        said.append(
            f"output {parts.outputs[0]}"
            if len(parts.outputs) == 1
            else f"outputs ({', '.join(parts.outputs)})"
        )
    if parts.unused:
        said.append(f"unused {', '.join(parts.unused)}")
    for output, read in parts.per_output:
        said.append(f"{output} reads {', '.join(read)}" if read else f"{output} reads no argument")
    if said:
        lines.append("; ".join(said))
    return tuple(lines)


# --- the names of the arguments ---


def _argument_names(pairs, reserved=()):
    """The display names of ordered arguments: each its given name, and a name
    already taken the first free one of `name_1`, `name_2`, …, in argument
    order (AMD-SG-007 §3.1); a parameter's name is taken from the start."""
    used, names = set(reserved), {}
    for key, name in pairs:
        chosen, suffix = name, 0
        while chosen in used:
            suffix += 1
            chosen = f"{name}_{suffix}"
        used.add(chosen)
        names[key] = chosen
    return names


def _displayed(term, names, ctx, block):
    """A retained term with every wire symbol and every renamed or marked
    argument written by its display name."""
    if is_wire_symbol(term):
        return T.Sym(T.Constant(names[term.symbol.name]))
    if isinstance(term, T.Call):
        identity = term.fun if isinstance(term.fun, Identity) else ctx.resolve(term.fun, block)
        function = names.get(identity, term.fun)
        return T.Call(function, tuple(_displayed(arg, names, ctx, block) for arg in term.args))
    if isinstance(term, T.Key):
        identity = ctx.resolve(term.at, block)
        return T.Key(names.get(identity, term.at))
    if isinstance(term, T.Sym):
        identity = _argument_identity(term, ctx, block)
        if identity in names and (names[identity], None) != spelling(term):
            return T.Sym(T.Constant(names[identity]))
        return term
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return type(term)(
            *(
                _displayed(getattr(term, f.name), names, ctx, block)
                for f in dataclasses.fields(term)
            )
        )
    if isinstance(term, tuple):
        return tuple(_displayed(item, names, ctx, block) for item in term)
    return term


def _argument_identity(node, ctx, block):
    """The identity a symbol of a kernel's term reads, or None for a
    parameter or a function name."""
    name, side = spelling(node)
    if side is None and (name in ctx.parameter_names or name in ctx.function_names):
        return None
    return ctx.resolve(name, block, side)


def spelling(symbol):
    """(name, side or None) of a retained symbol term."""
    s = symbol.symbol
    return s.name, (
        s.when.side if isinstance(s, T.Variable) and isinstance(s.when, T.At) else None
    )


def _names_read(term, names, ctx, block):
    """The wires and coordinates among a kernel's arguments that a term
    reads."""
    found = set()
    for node in term_nodes(term):
        if isinstance(node, T.Operator) and node.head == "E":
            case = label_case(ctx, node, block)
            if case is not None:
                found |= _names_read(case, names, ctx, block)
        if is_wire_symbol(node):
            found.add(node.symbol.name)
        elif isinstance(node, T.Call):
            identity = node.fun if isinstance(node.fun, Identity) else ctx.resolve(node.fun, block)
            if identity in names:
                found.add(identity)
        elif isinstance(node, T.Key):
            identity = ctx.resolve(node.at, block)
            if identity in names:
                found.add(identity)
        elif isinstance(node, T.Sym) and isinstance(node.symbol, (T.Constant, T.Variable)):
            identity = _argument_identity(node, ctx, block)
            if identity in names:
                found.add(identity)
    return found


# the letter a value argument of a printed kernel takes, by the role of the
# field its wire carries (AMD-SG-011 §8 item 2): a kernel on a value bundle
# then reads `G(v, w, b, y) = (v, R*w)` and not `G(w_1, w_2, b, y)`, so that a
# reader does not have to match a numbered placeholder to a wire line
_VALUE_LETTERS = {VALUE: "v"}


def _value_argument_names(rendering, ordinary, taken=()):
    """The name of each value argument of a printed kernel. A wire that carries
    a field of the file takes that field's own name with its perch mark
    (AMD-SG-015 §5 item 6h): `𝐺(V[>], w, c)` and never `𝐺(w, w_1, c)`, in which
    the letter `w` stands for the continuation value on a sheet whose perches
    section gives `w` to cash on hand.

    A wire that carries no field — an occurrence's result — has no such name.
    One such input is `w`, the letter of AMD-SG-007's tables and of the central
    page; several are named by the letter of the role each carries, counted
    within one role where a perch declares two fields of it. The numbered
    placeholders `w_1, w_2, …` are used instead where such a wire's role is
    unknown, or where a letter would take a name the author already wrote: on
    a stage that declares a shock `z`, a value named `z` would push the
    author's shock to `z_1`, a name that stands in no stage file. A coordinate
    the author wrote is never renamed."""
    named = {wire: _value_field_name(wire) for wire in ordinary}
    ordinary = tuple(wire for wire in ordinary if named[wire] is None)
    found = {wire: name for wire, name in named.items() if name is not None}
    if not ordinary:
        return found
    taken = tuple(taken) + tuple(found.values())
    if len(ordinary) == 1:
        found[ordinary[0]] = "w"
        return found
    roles = {
        wire: _VALUE_LETTERS.get(getattr(rendering.sort_of(wire), "role", None))
        for wire in ordinary
    }
    if any(letter is None for letter in roles.values()) or set(roles.values()) & set(taken):
        found.update({wire: f"w_{place + 1}" for place, wire in enumerate(ordinary)})
        return found
    held = {}
    for wire, letter in roles.items():
        held.setdefault(letter, []).append(wire)
    found.update(
        {
            wire: letter if len(wires) == 1 else f"{letter}_{wires.index(wire) + 1}"
            for letter, wires in held.items()
            for wire in wires
        }
    )
    return found


def _value_field_name(identity):
    """The name a value or function wire carries as an argument of a printed
    kernel: the field of the file with its perch mark, `V[>]`; None where the
    wire is an occurrence's result and carries no field of the file."""
    if identity.kind in ("function", "choice") and identity.perch is not None:
        return marked_field(identity)
    return None


def marked_field(identity):
    """The field of a wire with the mark of its perch, as the text of a
    kernel writes a function or a choice at a perch."""
    return identity.field + PERCH_MARK.get(identity.perch, "")


def _shown_arguments(stage, keys, names):
    """The name each argument of a value aggregator carries on the printed
    lines: the authored sub-expression of an expectation's result, and the
    argument's own letter otherwise (§2.4). Where two arguments would print one
    sub-expression, both keep their letters: no name stands for two arguments
    (§2.1), and the letters tell the two occurrences apart."""
    authored = {key: _expectation_source(stage, key) for key in keys}
    authored = {
        key: text
        for key, text in authored.items()
        if text is not None and text not in set(names.values())
    }
    counted = collections.Counter(authored.values())
    return {
        key: authored[key] if counted.get(authored.get(key)) == 1 else names[key] for key in keys
    }


def _expectation_source(stage, identity):
    """The authored sub-expression of an expectation's result, `E_{y}(R*dV)`,
    read from the statement the occurrence stands in and its position among the
    `E` operators of that statement in the order the construction numbers them.
    None where the identity is no occurrence's result or the statement is not
    retained. §2.4 writes a kernel's value argument that is an expectation's
    result this way, as the obligations and the WHERE lines already
    write it."""
    if identity.kind != "Expectation" or identity.mark != "result":
        return None
    if identity.address not in stage.definitions:
        return None
    equations = stage.definitions[identity.address].equations
    if not equations:
        return None
    nodes = expectation_nodes(equations[0])
    place = (identity.occurrence or 1) - 1
    return to_source(nodes[place]) if 0 <= place < len(nodes) else None


# --- the names of the outputs ---


def _kernel_output_name(stage, identity):
    """The name the `outputs … reads …` line of a kernel of several outputs
    gives one of them: the field of a function wire with its perch mark, and
    for a result the file does not name the statement the kernel writes there,
    `value`. The line speaks of the kernel's arguments and keeps its words
    (§2.4), and a kernel's arguments are points, in roman, so the line pairs no
    italic function applied at a point with a roman argument it reads (§4). A
    kernel of one output writes no such pairing and keeps the wire's own name,
    which the `out` line above it repeats."""
    if identity.is_result and identity.field:
        return identity.field
    if identity.mark == "result" and identity.address:
        return str(identity.address).split(".", 1)[-1]
    return kernel_output_name(stage, identity)


def kernel_output_name(stage, identity):
    """The name of an output of an aggregation's kernel: a result the file
    names by its field; a function or a choice at a perch by its field with
    its perch mark, `V[<]`; and an unnamed result of an aggregation by the map
    its row writes, so that a reader matches the `outputs` clause to the `out`
    lines above it. The fold writes no other output of an aggregation
    (`fold/backward.py`, `fold/policy.py`); another wire is refused under
    `kernel-target`."""
    if not is_kernel_output(stage, identity):
        raise construction_error(
            f"stage {stage.name!r}: the wire {identity} is no output of the kernel G of an "
            "aggregation, which names as its outputs a result by its field, a function or a "
            "choice at a perch by its field and perch mark, and an unnamed result of an "
            "aggregation by the map its row writes (AMD-SG-007 §3.1, rule kernel-target); "
            "name another wire by the name the stage gives it, `wire_name`",
            stage=stage.name,
            address=identity.address,
            span=None,
            rule="kernel-target",
            file=source_file(stage),
        )
    if identity.is_result and identity.field:
        return identity.field
    if identity.kind in ("function", "choice"):
        return marked_field(identity)
    # an unnamed result of an aggregation by the map its row writes, as the
    # file spells it, the wires it reads by their own names: read here and not
    # through the display's expression query, which reads this kernel in its
    # turn
    row = wire_table(stage).produced[identity]
    position = row.outputs.index(identity) if len(row.maps) == len(row.outputs) else 0
    return to_source(_wires_named(row.maps[position]))


def is_kernel_output(stage, identity):
    """Whether the wire `identity` is of the three kinds an aggregation's
    kernel names as outputs: a result the file names by its field, a function
    or a choice at a perch, and an unnamed result of an aggregation whose row
    writes a map."""
    if identity.is_result and identity.field:
        return True
    if identity.kind in ("function", "choice") and identity.perch is not None:
        return True
    if identity.kind == "Aggregation" and identity.is_result:
        row = wire_table(stage).produced.get(identity)
        return row is not None and bool(row.maps)
    return False


def _wires_named(term):
    """`term` with each wire symbol replaced by the constant that names it."""
    if is_wire_symbol(term):
        return T.Sym(T.Constant(_wire_symbol_name(term.symbol.name)))
    if isinstance(term, T.Call) and isinstance(term.fun, Identity):
        return T.Call(_wire_symbol_name(term.fun), tuple(_wires_named(arg) for arg in term.args))
    if isinstance(term, tuple):
        return tuple(_wires_named(t) for t in term)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term, **{f.name: _wires_named(getattr(term, f.name)) for f in dataclasses.fields(term)}
        )
    return term


def _wire_symbol_name(identity):
    """The name a wire symbol is written by in a kernel's text without any
    display query: a function or a choice by its field and perch mark, a
    result by its field, any other wire by its key."""
    if identity.kind in ("function", "choice") and identity.perch is not None and identity.field:
        return marked_field(identity)
    if identity.field:
        return identity.field
    return str(identity)


def _evaluated_output_set(ctx, rendering, output):
    """The declared result of an evaluated expression or maximand."""
    from bellman.stage.carriers import policy_objective_field

    value = rendering.sort_of(output).domain
    if value is not None:
        return value
    evaluation = next(
        (
            row
            for row in rendering.table.primitive_rows
            if row.kind == "Evaluation" and output in row.inputs
        ),
        None,
    )
    if evaluation is not None:
        return rendering.sort_of(evaluation.outputs[evaluation.inputs.index(output)]).domain
    return ctx.declared_set(policy_objective_field(ctx, rendering, output))


# --- the names of a point and the arguments of a distribution ---


def stems_of(identities):
    """The coordinate names of ordered identities, in roman."""
    return tuple(identity.stem for identity in identities)


def distribution_arguments(definition):
    """The state, control and shock arguments of a distribution declaration,
    its record's coordinates, in order of first occurrence (AMD-SG-009 §1)."""
    return tuple(name for name, _ in definition.coordinates)
