"""The typing walk of the construction. The retained term is the parsed
expression the construction keeps for each item of the file; the walk reads it
once for every function body, distribution declaration, declared set and
authored line. It gives each line its kind (`definition`, `relation` or
`documentation`), its unknowns, the arity and the argument kinds of every
call, the sets a value is required to lie in, and the typed inputs and outputs
of its box as `ResolvedName` records, which `graphs/initial_diagrams.py` reads
when the stored graphs are built.

`type_stage` is the one call the construction makes: the checked declarations,
the fields and the sorts of the wires give the typing context, and its walk
returns the typed lines of every builder and the sort of every wire. The walk
is in source order and refuses where it finds the fault, at the address of the
item it reads: under `well-typed`, a value used as a number that is none (a
function, a tuple, a label), a function applied to arguments of another number
or kind than it declares, `Inv` of anything but one function, a line whose two
sides are of different kinds or whose left side names another number of fields
than its right side has results; under `declared-once`, a binder named twice in
one subscript, and an expectation whose binder is a name already bound where
it stands, by an enclosing operator or by the parameters of the definition,
so that it is no subject of its distribution; under `definition-order`, a
recursive definition; under `not-constructed`, a definition whose right side
is not a function of the stage; and under `readable-form`, the forms only a
term decoded from a saved AST can hold. The `KeyError` of a name that resolves
to no input is no refusal: `_binder_input` and a dynamic selection read it as
a signal, and the declaration pass has refused a name nothing declares before
the walk. One condition raises a `ValueError` and names no rule, an input
that two sub-expressions read at two types. The walk records no condition:
the conditions of a stage are computed by the fold from the same terms and
answered by `stage.stage_answers.obligations`.
"""

from __future__ import annotations

import contextlib
import dataclasses
from typing import NamedTuple

from bellman.distributions.edges import shock_application
from bellman.native.identity import Identity
from bellman.native.records import ExpressionType, ResolvedName, Sort, construction_typing_table
from bellman.refusals import NotConstructed
from bellman.syntax import terms
from bellman.syntax.source import comprehension_text, condition_text, to_source
from bellman.syntax.vocabulary import (
    CONTINUATION,
    CONTROL,
    DECISION,
    DOC,
    PRIMITIVE_SETS,
    SHCK,
    SHOCK,
    STATE,
    WRITTEN_MARK,
)
from bellman.typing import sets
from bellman.typing.declarations import TOP_LEVEL
from bellman.typing.line_unknowns import derivative_left_side
from bellman.typing.line_unknowns import (
    CALL_OPERATORS,
    INPUT,
    OUTPUT,
    coordinate_set_term,
    field_spelling,
    listed_identity,
    names_fields,
    outputs_and_unknowns,
    unreadable_form_refusal,
)

# --- the typing call of the construction ---


def type_stage(*, declarations, fields, wire_sorts, hypergraph) -> TypedStage:
    """The typing of one stage: the checked declarations, the fields and the
    sorts of the wires give the typing context, and its walk of the retained
    term gives the typed lines of every builder.

    The table of one typing per identity is opened and closed here, by the one
    phase that writes it. A `Sort` the fold or the construction of the graphs
    builds afterwards, and a `Sort` built outside a construction, is checked
    against no table.
    """
    with construction_typing_table():
        semantics = TypingContext(declarations, fields, wire_sorts)
        return TypedStage(semantics.typed_builders(hypergraph), dict(semantics.sorts))


@dataclasses.dataclass(frozen=True)
class TypedStage:
    """What the typing call returns: the typed lines of every builder, by the
    builder's name, and the sort of every wire, the local aliases of the
    builders' interiors included."""

    builders: dict
    sorts: dict


@dataclasses.dataclass(frozen=True)
class TypedBuilder:
    """The typed lines of one builder: the lines its block states
    (`statements_outside_nodes`), each with its typed inputs and outputs, and
    its authored nodes with the identities each reads and writes."""

    statements_outside_nodes: tuple
    nodes: tuple


# --- the walk ---


class _Typed(NamedTuple):
    """What the walk answers for one expression: the inputs it reads and the
    types of its results."""

    inputs: tuple
    results: tuple


# The words a refusal under `well-typed` names the kind of a value with, one
# for each kind of `ExpressionType` the walk assigns.
_KIND_WORDS = {
    "scalar": "a number",
    "state": "a tuple of values",
    "function": "a function",
    "set": "a set",
    "relation": "the solutions of an argmax or a solve",
    "distribution": "a distribution",
    "opaque": "a value of a set the file does not state",
}
# What to write in place of a value of each kind that is read as a number.
_NUMBER_ADVICE = {
    "function": "apply the function to its arguments, `{operand}(…)`",
    "state": "select one of its coordinates, `{operand}[1]`",
    "relation": "state the argmax or the solve on a line of its own and read the field it defines",
    "set": "write a number, or a field whose values lie in the set",
    "distribution": "take the expectation of a function of its shocks, `E_{{…}}(…)`",
}
# The type of a real number, the result of the arithmetic and the default of a
# declaration that writes no set.
_REAL_TYPE = ExpressionType("scalar", "primitive:real")
_EXTENDED_REAL = ExpressionType("scalar", "primitive:extended-real")
# the words of the refusal of two parts of different kinds (`_cast`): the
# part read, the part it is compared with, and the rule they break
_SIDES = "the two sides of a line are of one kind"
_BRANCHES = "the branches of a formula by cases are of one kind"
_CAST_WORDS = {
    "left": ("the left side", "the right side", _SIDES),
    "right": ("the right side", "the left side", _SIDES),
    "then": ("the branch after `then`", "the branch after `else`", _BRANCHES),
    "else": ("the branch after `else`", "the branch after `then`", _BRANCHES),
}
_BOOLEAN = ExpressionType("scalar", "primitive:boolean")
# The name of the domain of each spelling of a primitive set whose members are
# numbers, read from the one table of the primitive sets
# (`vocabulary.PRIMITIVE_SETS`); an extended real carries no such name and is
# named after its spelling.
_PRIMITIVE_DOMAINS = {
    spelling: primitive.domain
    for spelling, primitive in PRIMITIVE_SETS.items()
    if primitive.domain is not None
}


class TypingContext:
    """The declared sets, fields, parameters and shocks of one stage, with the
    types computed so far, while its lines are typed.

    `type_stage` builds it from the checked declarations, the fields and the
    sorts of the wires, and calls `typed_builders`, which returns each
    builder's lines with their inputs, outputs and value types. The tables
    below exist only while a stage is constructed and are stored on no
    stage. `typed_builders` is the one method the construction calls and
    `sorts` the one attribute it reads; every other method serves the walk
    and is internal.
    """

    def __init__(self, declarations, fields, sorts):
        self.declarations, self.fields = declarations, fields
        # the sorts of the wires: the fields, then every local
        # alias as its line is read
        self.sorts = dict(sorts)
        self.definitions, self.inputs, self.domain_sites = {}, {}, {}
        self.pending_domains, self.domain_terms = {}, {}
        self.equations, self.equation_outputs = {}, {}
        self.aliases = {}
        self.address, self.block_id = "stage", None
        self.local = ()
        self.law_result, self.law_head = None, None
        self.active = set()
        self.expression_roots = {}
        # the definitions the expression under the walk calls, in the order the
        # walk meets them; one list per line and per definition body
        self.calls = []
        for identity, field in fields.items():
            sites = []
            for index, term in enumerate(field.domain_terms):
                if term is None:
                    continue
                domain_id = f"{identity}:domain-site:{index}"
                address, _ = field.sites[index]
                if address == TOP_LEVEL:
                    # a site at the top level is typed at the address of the
                    # field's declaration, where a refusal of its set stands
                    address = declarations.scalars[field.stem].address
                self.pending_domains[domain_id] = (term, address, ("domain", identity, index), ())
                self.domain_terms[domain_id] = term
                sites.append(domain_id)
            self.domain_sites[identity] = tuple(sites)
            domain_id = f"{identity}:domain" if sites else "primitive:real"
            self.domain_terms[domain_id] = tuple(field.domain_terms)
            self.inputs[identity] = ResolvedName(
                identity=identity,
                value_type=self._value_type(tuple(field.domain_terms), domain_id, str(identity)),
                role=declarations.field_roles[field.stem],
                perch=field.perch,
            )
        for name, declaration in declarations.scalars.items():
            if declarations.declared_as(name) == "parameter":
                identity = Identity("parameter", stage=declarations.stage, field=name)
                term = declaration.domain_term
                domain_id = (
                    self._domain(term, declaration.address, ("domain", name))
                    if term
                    else "primitive:real"
                )
                self.inputs[identity] = ResolvedName(
                    identity=identity,
                    value_type=self._value_type(term, domain_id, declaration.address),
                    role="parameter",
                    perch=None,
                )
        for name, definition in declarations.functions.items():
            if definition.declared_set is not None:
                # the set a derived parameter's definition declares, `q :
                # (0,1) := (β*R)^(1/ρ)/R`, is typed with the declared sets of
                # the stage, as a parameter's set is
                self._domain(definition.declared_set, definition.address, ("domain", name))
        for name in declarations.shocks:
            identity = Identity("field", stage=declarations.stage, perch=SHCK, field=name)
            if identity not in self.inputs:
                term = declarations.declared_set_of(name)
                address = declarations.shock_address(name)
                domain_id = (
                    self._domain(term, address, ("domain", name)) if term else "primitive:real"
                )
                self.inputs[identity] = ResolvedName(
                    identity=identity,
                    value_type=ExpressionType(self._value_kind(term), domain_id),
                    role=SHOCK,
                    perch=SHCK,
                )

    # -- the walk --
    # definitions and distributions, every line, the declared sets

    def typed_builders(self, hypergraph):
        """The typed lines of every builder, by the builder's name: the
        definitions and the distribution declarations typed first, then the
        lines of every block in source order, then every declared set. Each
        builder receives its lines with their inputs, outputs and value types,
        and a builder with `!node` lines its nodes with the identities each
        reads and writes."""
        for name in self.declarations.definition_order:
            self._typed_function(name)
        for name in self.declarations.law_of:
            self._typed_distribution(name)
        records = {}
        for box in hypergraph.boxes:
            for record in box.data.statements_outside_nodes:
                records[record.address] = record
            for node in box.data.nodes:
                for record in node.statements:
                    records[record.address] = record
        items = {}
        for block_id, _ in self.declarations.blocks:
            self.block_id, self.aliases = block_id, {}
            for _, address, item in self.declarations.bodies[block_id]:
                self.equations[address] = self._typed_line(records[address], item)
                items[address] = item
        self._type_declared_sets()

        def with_record(record):
            # The working line keeps the statement as its retained term, with
            # the kind, the unknowns and the typed inputs and outputs the pass
            # resolved.
            equation = self.equations[record.address]
            return dataclasses.replace(
                record,
                core=items[record.address].core,
                equation_kind=equation.kind,
                unknowns=tuple(equation.unknowns),
                inputs=equation.context,
                outputs=self.equation_outputs[record.address],
            )

        calls = {address: equation.calls for address, equation in self.equations.items()}
        builders = {}
        for box in hypergraph.boxes:
            data = box.data
            boundary = tuple(with_record(r) for r in data.statements_outside_nodes)
            nodes = tuple(
                dataclasses.replace(
                    node, statements=tuple(with_record(r) for r in node.statements)
                )
                for node in data.nodes
            )
            if nodes:
                nodes = _builder_nodes(
                    box,
                    nodes,
                    boundary=boundary,
                    declarations=self.declarations,
                    calls=calls,
                    definitions=self.definitions,
                )
            builders[box.name] = TypedBuilder(boundary, nodes)
        return builders

    def _typed_line(self, record, item):
        """One authored line typed: its inputs, the fields it defines, the
        types of its results, its kind and its unknowns."""
        core = item.core.core if isinstance(item.core, terms.Slack) else item.core
        self.address = record.address
        self.expression_roots[record.address] = (core.rhs, ("rhs",))
        self.calls = []
        rhs = self._typed_expression(core.rhs, address=record.address, position=("rhs",))
        if isinstance(core, terms.Equation) and derivative_left_side(core.lhs):
            # a derivative line, `D_{m_d}V = 𝑑𝑢(c)`, states a derivative of the
            # value the builder writes and defines no field and no unknown
            # (AMD-MB-001 §4.3): its right side is typed as an expression over
            # the names in scope, and its left side for its coordinate; the
            # fold records it at the builder's Evaluation
            left = self._typed_expression(core.lhs, address=record.address, position=("lhs",))
            self.equation_outputs[record.address] = ()
            context = self._with_clause(_merge((left.inputs, rhs.inputs)), item, record.address)
            return _TypedLine(
                context=context,
                value_types=(_BOOLEAN,),
                kind=_line_kind(record.role, relation=True),
                unknowns=(),
                calls=tuple(self.calls),
            )
        spellings = outputs_and_unknowns(
            core.lhs,
            record.address,
            self.declarations,
            core.rhs,
            relation=not isinstance(core, terms.Equation),
        )
        result_types = (
            rhs.results[0].results
            if len(rhs.results) == 1 and rhs.results[0].kind == "relation"
            else rhs.results
        )
        # a candidate statement states one scalar residual in the unknowns its
        # two sides mention, so its left side names as many fields as the
        # system has and its right side one result
        candidate = isinstance(core, terms.Equation) and not names_fields(core.lhs)
        if candidate:
            result_types = result_types[:1] * len(spellings)
        if not spellings and not candidate:
            # an inequality whose left side is not a name states a relation and
            # defines no field; both its sides are typed and the line is
            # retained with no output
            left = self._typed_expression(core.lhs, address=record.address, position=("lhs",))
            self.equation_outputs[record.address] = ()
            context = self._with_clause(_merge((left.inputs, rhs.inputs)), item, record.address)
            return _TypedLine(
                context=context,
                value_types=(_BOOLEAN,),
                kind=_line_kind(record.role, relation=True),
                unknowns=(),
                calls=tuple(self.calls),
            )
        if len(spellings) != len(result_types):
            raise self.declarations.error(
                "well-typed",
                record.address,
                (
                    f"the left side of `{to_source(core)}` names {len(spellings)} "
                    f"fields, and its right side has {len(result_types)} results; "
                    f"a line names one field for each result of its right side"
                ),
            )
        outputs = self._output_inputs(spellings, result_types, record.address)
        self.equation_outputs[record.address] = outputs
        values = tuple(output.value_type for output in outputs)
        lhs = _Typed(outputs, values)
        if len(rhs.results) == 1 and rhs.results[0].kind == "relation":
            lhs = self._cast(lhs, rhs.results[0].results, record.address, core, "left")
            context = self._with_clause(_merge((lhs.inputs, rhs.inputs)), item, record.address)
            return _TypedLine(
                context=context,
                value_types=(_BOOLEAN,),
                kind=_line_kind(record.role, relation=True),
                unknowns=tuple(output.identity for output in outputs),
                calls=tuple(self.calls),
            )
        if not candidate:
            rhs = self._cast(rhs, lhs.results, record.address, core, "right")
        context = _merge((lhs.inputs, rhs.inputs))
        implicit = candidate or any(
            op.head == "solve" and op.position == () for op in record.operators
        )
        context = self._with_clause(context, item, record.address)
        kind = _line_kind(record.role, relation=implicit or isinstance(item.core, terms.Slack))
        return _TypedLine(
            context=context,
            value_types=lhs.results,
            kind=kind,
            unknowns=tuple(output.identity for output in outputs) if implicit else (),
            calls=tuple(self.calls),
        )

    def _output_inputs(self, spellings, result_types, address):
        """The typed records of the fields a line's left side names, one for
        each result of its right side: a field the block lists is its
        declared input; any other name is a local alias, or a field at the
        perch its mark names, typed by the result it takes, and is recorded
        as such."""
        outputs = []
        for spelling, value_type in zip(spellings, result_types):
            output_id = listed_identity(
                spelling, self.declarations.side_entries(self.block_id, OUTPUT), self.declarations
            )
            if output_id is None:
                identity = (
                    Identity(
                        "field",
                        stage=self.declarations.stage,
                        perch=spelling.mark,
                        field=spelling.stem,
                    )
                    if spelling.mark
                    else Identity(
                        "alias",
                        stage=self.declarations.stage,
                        address=address,
                        field=spelling.stem,
                    )
                )
                role = self.declarations.field_roles.get(spelling.stem, "alias")
                output = ResolvedName(
                    identity=identity, value_type=value_type, role=role, perch=spelling.mark
                )
                self.aliases[spelling] = output
                self.sorts.setdefault(
                    identity, Sort(identity, "field", perch=spelling.mark, role=role)
                )
            else:
                output = self.inputs[output_id]
            outputs.append(output)
        return tuple(outputs)

    def _with_clause(self, context, item, address):
        """The inputs `context` of a line with those its clause, the relation
        after `⟂`, reads, where the line has one."""
        if not isinstance(item.core, terms.Slack):
            return context
        condition = self._typed_expression(item.core.bound, address=address, position=("bound",))
        return _merge((context, condition.inputs))

    def _type_declared_sets(self):
        """Type every declared set of the stage and every set written at a
        lexical position inside one, until no new position is reached."""
        for name, term in self.declarations.space_terms.items():
            identity = Identity("set", stage=self.declarations.stage, field=name)
            address = self.declarations.spaces[name]
            self.pending_domains.setdefault(identity, (term, address, ("value", "s"), ()))
            self.domain_terms[identity] = term
        done = set()
        while any(identity not in done for identity in self.pending_domains):
            identity = next(identity for identity in self.pending_domains if identity not in done)
            term, address, position, local = self.pending_domains[identity]
            self.address, self.block_id = address, None
            self.calls = []
            if isinstance(term, terms.Tuple):
                # A tuple's ordered value types determine its product domain.
                for i, item in enumerate(term.items):
                    self._typed_expression(
                        item, address=address, position=position + ("items", i), local=local
                    )
            else:
                method = (
                    self._typed_set_expression
                    if isinstance(term, terms.setexpr)
                    else self._typed_expression
                )
                method(term, address=address, position=position, local=local)
            done.add(identity)

    def _typed_function(self, name):
        """The typed definition of a named function, correspondence or alias,
        computed once per stage."""
        identity = Identity("function", stage=self.declarations.stage, field=name)
        if identity in self.definitions:
            return self.definitions[identity]
        source = self.declarations.functions[name]
        self.expression_roots[source.address] = (source.body, (source.slot,))
        if identity in self.active:
            raise self.declarations.error(
                "definition-order", source.address, f"recursive semantic definition {name!r}"
            )
        self.active.add(identity)
        with self._walking_at(source.address, local=self.local):
            parameters, local = [], ()
            for i, (param, domain) in enumerate(source.domains):
                domain_id = (
                    self._domain(domain, source.address, ("params", i), local=local)
                    if domain
                    else "primitive:real"
                )
                port = ResolvedName(
                    identity=Identity(
                        "function-parameter", owner=identity, occurrence=i, field=param
                    ),
                    value_type=ExpressionType(self._value_kind(domain), domain_id),
                    role="argument",
                    perch=None,
                )
                parameters.append(port)
                local += ((param, port),)
            parameters = tuple(parameters)
            self.local = local
            method = (
                self._typed_set_expression
                if isinstance(source.body, terms.setexpr)
                else self._typed_expression
            )
            context, values = method(
                source.body, address=source.address, position=(source.slot,), local=local
            )
            free = tuple(p for p in context if p not in parameters)
            kind = (
                "correspondence"
                if isinstance(source.body, terms.setexpr)
                else "function_alias"
                if source.slot == "value"
                else "function"
            )
            if (
                kind == "function_alias"
                and not (len(values) == 1 and values[0].kind == "function")
                and self.declarations.defines_a_derived_parameter(source)
            ):
                # `h := 1/(1 - Γ/R)`: a derived parameter, a constant of the
                # stage that its definition writes from the parameters, read
                # as the scalar it writes; the fold checks what it reads and
                # the calibration evaluates it (AMD-MT-003, build contract §5)
                kind = "derived_parameter"
            if kind == "function_alias" and not (
                len(values) == 1 and values[0].kind == "function"
            ):
                # `XH := linspace(H_min, H_max, n_H)`: a definition without
                # parameters whose right side is not a function of the
                # stage. A set defined by a grid constructor has no
                # construction rule yet; refuse at the span instead of
                # failing inside the definition record.
                applied = getattr(source.body, "fun", None)
                written = f"{name!r} writes `{to_source(source.body)}`"
                forms = (
                    "a definition without arguments defines a set, as `Xa := ℝ₊` does, or a "
                    "function of the stage, as `𝑑𝑢 := D_{c}(𝑢)` does, or a derived parameter, "
                    "arithmetic of parameters and numbers whose only calls are log, exp, min "
                    "and max, or a definition by cases of such arithmetic, as "
                    "`h := 1/(1 - Γ/R)` does"
                )
                raise self.declarations.error(
                    "not-constructed",
                    source.address,
                    (
                        f"the definition {written}, a call of {applied}, whose value is no "
                        f"function of the stage; {forms}, and the construction defines no set by "
                        f"a call such as a grid constructor"
                        if applied is not None
                        else f"the definition {written}, whose value is no function of the stage; "
                        f"{forms}"
                    ),
                    error_class=NotConstructed,
                )
            definition = _TypedDefinition(
                identity=identity,
                address=source.address,
                kind=kind,
                parameters=parameters,
                context=free,
                value_types=values,
                calls=tuple(self.calls),
            )
            self.definitions[identity] = definition
            self.active.remove(identity)
        return definition

    def _typed_distribution(self, name):
        """The typed distribution declaration of one shock, computed once per
        stage; its result is the distribution over the sets of its subjects."""
        address = self.declarations.law_of[name]
        identity = Identity("law", stage=self.declarations.stage, address=address)
        if identity in self.definitions:
            return self.definitions[identity]
        subjects = next(
            subjects
            for subjects, declaration in self.declarations.laws.items()
            if declaration.address == address
        )
        term = next(term for term, site in self.declarations.law_terms if site == address)
        subject_ids = tuple(
            Identity("field", stage=self.declarations.stage, perch=SHCK, field=subject)
            for subject in subjects
        )
        domain_id = f"{identity}:subjects"
        formals = self.declarations.parameterized_laws.get(name, ())
        actuals = self.declarations.law_actuals.get(name, ())
        parameters = ()
        if actuals:
            local = tuple(
                (formal, self.inputs[actual])
                for formal, actual in zip(formals, actuals, strict=True)
            )
        else:
            parameters = tuple(
                ResolvedName(
                    identity=Identity(
                        "function-parameter", owner=identity, occurrence=i, field=formal
                    ),
                    value_type=ExpressionType("opaque", _binder_set(address, ("law", i))),
                    role="argument",
                    perch=None,
                )
                for i, formal in enumerate(formals)
            )
            local = tuple(zip(formals, parameters, strict=True))
        with self._walking_at(
            address,
            law_head=term.fun if isinstance(term, terms.Call) else None,
            law_result=ExpressionType("distribution", domain_id),
        ):
            context, values = self._typed_expression(
                term, address=address, position=("law",), local=local
            )
            if actuals:
                context = _merge((context, tuple(port for _, port in local)))
            else:
                context = tuple(port for port in context if port not in parameters)
            definition = _TypedDefinition(
                identity=identity,
                address=address,
                kind="law",
                parameters=parameters,
                context=context,
                value_types=values,
                subjects=subject_ids,
                calls=tuple(self.calls),
            )
            self.definitions[identity] = definition
        return definition

    @contextlib.contextmanager
    def _walking_at(self, address, **state):
        """The walk at the definition at `address`, in no block and with no
        call recorded yet, with each field of `state` set; its position, its
        calls and those fields are restored when the definition is typed. A
        refusal ends the walk, and nothing is restored then."""
        saved = {key: getattr(self, key) for key in ("address", "block_id", "calls", *state)}
        self.address, self.block_id, self.calls = address, None, []
        for key, value in state.items():
            setattr(self, key, value)
        yield
        for key, value in saved.items():
            setattr(self, key, value)

    def _typed_expression(self, expr, *, address, position=(), local=()):
        """The inputs one expression reads and the types of its results, by the
        typing of its constructor."""

        def visit(term, suffix):
            return self._typed_expression(
                term, address=address, position=position + suffix, local=local
            )

        where = {"address": address, "position": position, "local": local}
        if isinstance(expr, terms.Number):
            return _Typed((), (_REAL_TYPE,))
        if isinstance(expr, terms.Sym):
            return self._typed_symbol(expr, address=address, local=local)
        if isinstance(expr, (terms.Add, terms.Sub, terms.Mul, terms.Div, terms.Pow, terms.Neg)):
            return self._typed_arithmetic(expr, **where)
        if isinstance(expr, terms.Tuple):
            args = tuple(visit(item, ("items", i)) for i, item in enumerate(expr.items))
            value = ExpressionType("state", self._domain(expr, address, position, local=local))
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        shock = shock_application(expr, self.declarations.parameterized_laws)
        if shock is not None:
            name, arguments = shock
            draw = self._typed_symbol(terms.Sym(terms.Constant(name)), address=address, local=local)
            supplied = tuple(visit(arg, ("law-argument", i)) for i, arg in enumerate(arguments))
            return _Typed(_merge((draw.inputs, *(arg.inputs for arg in supplied))), draw.results)
        if isinstance(expr, terms.Select):
            return self._typed_selection(expr, **where)
        if isinstance(expr, terms.Call):
            return self._typed_call(expr, **where)
        if isinstance(expr, terms.Operator):
            return self._typed_operator(expr, address=address, position=position, local=local)
        if isinstance(expr, (terms.Space, terms.setexpr)):
            return self._typed_set_expression(
                expr, address=address, position=position, local=local
            )
        if isinstance(expr, (terms.Rel, terms.Between)):
            return self._typed_relation(expr, **where)
        if isinstance(expr, terms.Conditional):
            sides = self._numeric_arguments(
                expr.test,
                (expr.test.left, expr.test.right),
                (
                    visit(expr.test.left, ("test", "left")),
                    visit(expr.test.right, ("test", "right")),
                ),
                address=address,
            )
            then = visit(expr.then, ("then",))
            otherwise = visit(expr.otherwise, ("otherwise",))
            if self.block_id is None:
                then, otherwise = self._numeric_arguments(
                    expr, (expr.then, expr.otherwise), (then, otherwise), address=address
                )
            results = then.results
            if any(value.kind == "opaque" for value in results):
                self._cast(then, otherwise.results, address, expr, "then")
                results = otherwise.results
            else:
                self._cast(otherwise, results, address, expr, "else")
            if then.results == (_EXTENDED_REAL,) or otherwise.results == (_EXTENDED_REAL,):
                results = (_EXTENDED_REAL,)
            inputs = _merge(part.inputs for part in (*sides, then, otherwise))
            return _Typed(inputs, results)
        raise self.declarations.error(
            "readable-form",
            address,
            (
                f"the expression holds a {type(expr).__name__}, which only a term decoded from a "
                f"saved AST can hold; no construction rule reads one"
            ),
        )

    def _typed_symbol(self, expr, *, address, local):
        """A name: its input, or no input where it names a function or a set;
        `inf` is an extended real. A variable with a time index or a shift and
        a symbol that is no name are refused under `readable-form`."""
        symbol = expr.symbol
        if isinstance(symbol, terms.Constant) and symbol.name == "inf":
            return _Typed((), (_EXTENDED_REAL,))
        if isinstance(symbol, terms.Variable):
            if not isinstance(symbol.when, terms.At) or symbol.shift != 0:
                raise self.declarations.error(
                    "readable-form",
                    address,
                    (
                        f"the variable {symbol.name} carries a time index or a "
                        f"shift, which only a term decoded from a saved AST can "
                        f"hold; no construction rule reads one. A field is written "
                        f"by its name and its perch mark, `{symbol.name}[>]`"
                    ),
                )
        elif not isinstance(symbol, terms.Constant):
            raise self.declarations.error(
                "readable-form",
                address,
                (
                    f"the symbol is a {type(symbol).__name__}, which only a term decoded from a "
                    f"saved AST can hold; no construction rule reads one. A symbol is a name"
                ),
            )
        bound = dict(local).get(symbol.name) if isinstance(symbol, terms.Constant) else None
        port = bound if bound is not None else self._input_named(symbol, local)
        if port.role == "function" and bound is None:
            return _Typed((), (port.value_type,))
        if port.value_type.kind == "set" and bound is None:
            return _Typed((), (port.value_type,))
        return _Typed((port,), (port.value_type,))

    def _typed_arithmetic(self, expr, *, address, position, local):
        """An arithmetic operation, whose operands are read as numbers and
        whose result is a real, or an extended real where an operand is one."""

        def visit(term, suffix):
            return self._typed_expression(
                term, address=address, position=position + suffix, local=local
            )

        if isinstance(expr, terms.Neg):
            operands = (expr.operand,)
            args = (visit(expr.operand, ("operand",)),)
        elif isinstance(expr, terms.Pow):
            operands = (expr.base, expr.exponent)
            args = (visit(expr.base, ("base",)), visit(expr.exponent, ("exponent",)))
        else:
            operands = (expr.left, expr.right)
            args = (visit(expr.left, ("left",)), visit(expr.right, ("right",)))
        args = self._numeric_arguments(expr, operands, args, address=address)
        result = (
            _EXTENDED_REAL if any(_EXTENDED_REAL in arg.results for arg in args) else _REAL_TYPE
        )
        return _Typed(_merge(arg.inputs for arg in args), (result,))

    def _typed_selection(self, expr, *, address, position, local):
        """A selection from a family by a position or by a name: the
        type of the selected member, and the name that selects,
        where it is an input."""

        def visit(term, suffix):
            return self._typed_expression(
                term, address=address, position=position + suffix, local=local
            )

        family = visit(expr.family, ("family",))
        if isinstance(expr.sel, terms.Pos):
            if isinstance(expr.family, terms.Tuple):
                if not 1 <= expr.sel.at <= len(expr.family.items):
                    raise self.declarations.error(
                        "family-selection",
                        address,
                        (
                            f"the selection {to_source(expr)} selects position {expr.sel.at} from "
                            f"{len(expr.family.items)} coordinates"
                        ),
                    )
                value = visit(
                    expr.family.items[expr.sel.at - 1], ("family", "items", expr.sel.at - 1)
                ).results[0]
            else:
                value = self._selected_type(family.results[0], expr.sel)
            return _Typed(_merge((family.inputs,)), (value,))
        if isinstance(expr.sel, terms.Term):
            value = self._selected_type(family.results[0], expr.sel)
            key = visit(expr.sel.at, ("sel", "at"))
            return _Typed(_merge((family.inputs, key.inputs)), (value,))
        if isinstance(expr.sel, terms.Key):
            value = self._selected_type(family.results[0], expr.sel)
            try:
                selector = dict(local).get(expr.sel.at)
                if selector is None:
                    selector = self._input_named(terms.Constant(expr.sel.at), local)
            except KeyError:
                return _Typed(_merge((family.inputs,)), (value,))
            return _Typed(_merge((family.inputs, (selector,))), (value,))
        raise self.declarations.error(
            "readable-form",
            address,
            (
                f"the selection selects by a {type(expr.sel).__name__}, which only a term decoded "
                f"from a saved AST can hold; a selection reads a position or a name"
            ),
        )

    def _typed_call(self, expr, *, address, position, local):
        """A call: the inverse of one function, a numerical operator's result,
        or the results of the definition it names, recorded as a call of the
        walk; any other call is external and opaque."""

        def visit(term, suffix):
            return self._typed_expression(
                term, address=address, position=position + suffix, local=local
            )

        args = tuple(visit(arg, ("args", i)) for i, arg in enumerate(expr.args))
        types = tuple(value for arg in args for value in arg.results)
        if expr.fun == "Inv":
            if len(types) != 1 or types[0].kind != "function":
                given = (
                    f"{_KIND_WORDS.get(types[0].kind, types[0].kind)}"
                    if len(types) == 1
                    else f"{len(types)} arguments"
                )
                raise self.declarations.error(
                    "well-typed",
                    address,
                    (
                        f"`{to_source(expr)}` inverts {given}; `Inv` inverts one function. Write "
                        f"the function to invert, as in `Inv(𝑑𝑢)`"
                    ),
                )
            function = types[0]
            return _Typed(
                _merge(arg.inputs for arg in args),
                (
                    ExpressionType(
                        kind="function",
                        domain=None,
                        arguments=function.results,
                        results=function.arguments,
                    ),
                ),
            )
        if expr.fun in ("evaluate", "upper_env"):
            _, values, _ = self._called_definition(expr.fun, types)
            return _Typed(_merge(arg.inputs for arg in args), values)
        if expr.fun not in self.declarations.functions and expr.fun not in CALL_OPERATORS:
            try:
                callee = self._input_named(terms.Constant(expr.fun), local)
            except KeyError:
                pass
            else:
                if callee.value_type.kind == "function":
                    self._check_arguments(expr.fun, types, callee.value_type.arguments)
                    return _Typed(
                        _merge(((callee,), *(arg.inputs for arg in args))),
                        callee.value_type.results,
                    )
        reference, values, external = self._called_definition(expr.fun, types)
        if not external:
            self._note_call(reference)
        return _Typed(_merge(arg.inputs for arg in args), values)

    def _typed_relation(self, expr, *, address, position, local):
        """A relation or a two-bound clause, which states a truth value; the
        terms of an ordered relation and of a clause are read as numbers."""
        if isinstance(expr, terms.Rel):
            args = (
                self._typed_expression(
                    expr.left, address=address, position=position + ("left",), local=local
                ),
                self._typed_expression(
                    expr.right, address=address, position=position + ("right",), local=local
                ),
            )
            if not isinstance(expr.op, terms.Eq):
                args = self._numeric_arguments(
                    expr, (expr.left, expr.right), args, address=address
                )
            return _Typed(_merge(arg.inputs for arg in args), (_BOOLEAN,))
        # a two-bound clause is typed as a relation is: its three terms are
        # numbers and it states a truth value
        args = tuple(
            self._typed_expression(part, address=address, position=position + (name,), local=local)
            for name, part in (
                ("lower", expr.lower),
                ("middle", expr.middle),
                ("upper", expr.upper),
            )
        )
        args = self._numeric_arguments(
            expr, (expr.lower, expr.middle, expr.upper), args, address=address
        )
        return _Typed(_merge(arg.inputs for arg in args), (_BOOLEAN,))

    def _typed_operator(self, expr, *, address, position, local):
        """One binding operator — an expectation, a root finding, a maximizer
        or a derivative — with its binders bound and its body typed under
        them."""
        if expr.head not in ("E", "solve", "argmax", "D"):
            raise self.declarations.error(
                "readable-form",
                address,
                (
                    f"the operator {expr.head}_ is none of `E_`, `solve_`, `argmax_` and `D_`, "
                    f"the operators written with a subscript; no construction rule reads another"
                ),
            )
        if expr.head == "D" and len(expr.subs) > 1:
            names = ", ".join(
                sub.name if isinstance(sub, terms.Var) else sub.var for sub in expr.subs
            )
            raise self.declarations.error(
                "derivative-one-name",
                address,
                (
                    f"the derivative {to_source(expr)} names {len(expr.subs)} formal "
                    f"arguments ({names}); a derivative names exactly one formal argument"
                ),
                write=(
                    "Write one derivative for one formal argument, "
                    + " or ".join(
                        f"`{to_source(dataclasses.replace(expr, subs=(sub,)))}`"
                        for sub in expr.subs
                    )
                ),
            )
        bound, additions, laws, domain_contexts = [], [], [], []
        original_inputs = self._local_shocks(local)
        for i, sub in enumerate(expr.subs):
            name, domain = self._subscript(expr, sub, additions, address)
            domain_local = local + tuple(additions)
            if domain is not None:
                domain_context, _ = self._typed_expression(
                    domain,
                    address=address,
                    position=position + ("subs", i, "set"),
                    local=domain_local,
                )
                domain_contexts.append(domain_context)
            template = self._binder_input(
                name, domain, address, position + ("subs", i), local=domain_local
            )
            self._check_derivative_binder(expr, name, template, address)
            port = dataclasses.replace(template, identity=_binder_name(address, position, i))
            bound.append(port)
            original_inputs[template.identity] = port
            additions.append((name, port))
            if domain is not None:
                self._domain(domain, address, position + ("subs", i, "set"), local=domain_local)
            if expr.head == "E":
                if name not in self.declarations.law_of:
                    # an expectation in a declared set, `β : (0, E_{w}(w^2))`,
                    # is refused here in the words the declaration pass uses
                    # for one on a line or in a definition
                    raise self.declarations.error(
                        "not-constructed",
                        address,
                        f"the expectation over {name!r} needs a declared distribution",
                        error_class=NotConstructed,
                        write=(
                            f"Declare the distribution of {name}, `{name} ~ …`, or write the "
                            f"set without the expectation over {name}"
                        ),
                    )
                law = self._typed_distribution(name)
                if template.identity not in law.subjects:
                    # the binder resolves to a name already bound where the
                    # expectation stands, by an enclosing operator or by the
                    # parameters of the definition, and not to the shock
                    raise self.declarations.error(
                        "declared-once",
                        address,
                        (
                            f"the expectation `{to_source(expr)}` binds {name!r}, a name "
                            f"already bound where it stands, so it integrates no shock; a nest "
                            f"of binders binds each name once; remove the inner "
                            f"`E_{{{name}}}`, or bind another shock"
                        ),
                        write=f"Remove the inner `E_{{{name}}}`, or bind another shock",
                    )
                if law.identity not in [entry.identity for entry in laws]:
                    laws.append(law)
        body_parts = tuple(
            self._typed_expression(
                arg,
                address=address,
                position=position + ("args", i),
                local=local + tuple(additions),
            )
            for i, arg in enumerate(expr.args)
        )
        body_context = _merge(part.inputs for part in body_parts)
        body_types = tuple(value for part in body_parts for value in part.results)
        bound_ids = {port.identity for port in bound}
        law_contexts = tuple(
            tuple(original_inputs.get(port.identity, port) for port in law.context) for law in laws
        )
        context = _merge(
            (
                tuple(p for p in body_context if p.identity not in bound_ids),
                *(
                    tuple(p for p in law_context if p.identity not in bound_ids)
                    for law_context in law_contexts
                ),
                *(
                    tuple(p for p in domain_context if p.identity not in bound_ids)
                    for domain_context in domain_contexts
                ),
            )
        )
        if expr.head in ("solve", "argmax"):
            values = (
                ExpressionType(
                    kind="relation",
                    domain=None,
                    arguments=(),
                    results=tuple(port.value_type for port in bound),
                ),
            )
        else:
            values = body_types
        return _Typed(context, values)

    def _local_shocks(self, local):
        """The shocks an enclosing expectation binds, each by the input of the
        stage's shock it rebinds."""
        found = {}
        for name, port in local:
            try:
                original = self._input_named(terms.Constant(name), ())
                if original.role == "shock" and port.role == "shock":
                    found[original.identity] = port
            except KeyError:
                pass
        return found

    def _subscript(self, expr, sub, additions, address):
        """The name one entry of an operator's subscript binds and its set,
        None where it writes none; an entry that is no name, and a name the
        subscript binds twice, are refused."""
        if isinstance(sub, terms.Var):
            name, domain = sub.name, None
        elif isinstance(sub, terms.In):
            name, domain = sub.var, sub.set
        else:
            raise self.declarations.error(
                "readable-form",
                address,
                (
                    f"the subscript of {expr.head}_ holds a {type(sub).__name__}, which only a "
                    f"term decoded from a saved AST can hold; a subscript names variables, `x`, "
                    f"or variables with their sets, `x : X`"
                ),
            )
        if name in dict(additions):
            once = ", ".join(
                dict.fromkeys(s.name if isinstance(s, terms.Var) else s.var for s in expr.subs)
            )
            raise self.declarations.error(
                "declared-once",
                address,
                (
                    f"`{to_source(expr)}` names {name} twice in its subscript; an operator's "
                    f"subscript names each variable once. Write `{expr.head}_{{{once}}}(…)`"
                ),
                write=f"Write `{expr.head}_{{{once}}}(…)`",
            )
        return name, domain

    def _check_derivative_binder(self, expr, name, template, address):
        """A derivative names one scalar formal argument of the function it
        differentiates; a product-valued one is refused under
        `derivative-scalar-coordinate`. A derivative of a field, `D_{a}V[>]`,
        names a state coordinate of the perch at which the field is read, and
        not a discrete one; for the value of a branch, `D_{a_w}V_w[>]`, a
        state the branch writes, not one of another branch of the same perch.
        Any other name is refused under `derivative-coordinate`, naming the
        coordinates of the perch or of the branch (AMD-MB-001 §4.2)."""
        perch = self._derivative_field_perch(expr, address)
        if perch is not None:
            field = to_source(expr.args[0])
            states = self._state_names_at(perch)
            where, read = f"the {perch} perch", f"at which {field} is read"
            branch = (
                self.declarations.branch_of_value(expr.args[0].symbol.name)
                if perch == CONTINUATION
                else None
            )
            if branch is not None:
                label, states = branch
                where = f"the branch {label!r} of the {perch} perch"
                read = f"whose fields {field} is a function of"
            discrete = name in states and self._is_discrete_field(name)
            if name not in states or discrete:
                listed = ", ".join(states) if states else "none"
                what = (
                    f"a discrete coordinate of {where}, over which no derivative is defined"
                    if discrete
                    else f"no state coordinate of {where}, {read}"
                )
                admitted = [state for state in states if not self._is_discrete_field(state)]
                raise self.declarations.error(
                    "derivative-coordinate",
                    address,
                    (
                        f"the derivative {to_source(expr)} names {name!r}, which is {what}; "
                        f"a derivative of a value is taken in a state coordinate of the perch "
                        f"at which the value is read, written without its mark, and the "
                        f"coordinates of {where} are {listed}"
                    ),
                    write=(
                        f"Name a state coordinate of {where}, "
                        + " or ".join(f"`D_{{{state}}}{field}`" for state in admitted)
                        if admitted
                        else None
                    ),
                )
            return
        if (
            expr.head == "D"
            and isinstance(template.identity, Identity)
            and template.identity.kind == "function-parameter"
            and template.value_type.kind == "state"
        ):
            function = (
                expr.args[0].symbol.name
                if len(expr.args) == 1
                and isinstance(expr.args[0], terms.Sym)
                and isinstance(expr.args[0].symbol, terms.Constant)
                else to_source(expr.args[0])
            )
            raise self.declarations.error(
                "derivative-scalar-coordinate",
                address,
                (
                    f"the derivative {to_source(expr)} names the formal argument {name!r} "
                    f"of function {function!r}, which is product-valued; a derivative names "
                    f"one scalar formal argument"
                ),
                write=(
                    f"Declare {function!r} with a scalar formal argument for each coordinate "
                    f"of {name!r}, reading them in its body in place of those coordinates, "
                    f"and take the derivative in one of them"
                ),
            )

    def _derivative_field_perch(self, expr, address):
        """The perch at which the one argument of a derivative term is read,
        where that argument is a field: the perch its mark names, `V[>]`, or
        the decision perch for a bare field name, `V`; None where the operator
        is not `D_` with one argument or the argument is no field, as a
        declared function `D_{c}(𝑢)` is none."""
        if expr.head != "D" or len(expr.args) != 1 or not isinstance(expr.args[0], terms.Sym):
            return None
        symbol = expr.args[0].symbol
        if isinstance(symbol, terms.Variable) and isinstance(symbol.when, terms.At):
            return self.declarations.perch_token(symbol.when.side, address, to_source(expr.args[0]))
        if isinstance(symbol, terms.Constant) and self.declarations.declared_as(symbol.name) == "field":
            return DECISION
        return None

    def _state_names_at(self, perch):
        """The names of the state fields at `perch`, each once, in the order of
        their first listing on a block header."""
        declarations = self.declarations
        roles = declarations.field_roles
        found = []
        for listing in declarations.listings:
            if roles.get(listing.stem) != STATE or listing.stem in found:
                continue
            if declarations.perch_of(listing, roles) == perch:
                found.append(listing.stem)
        return tuple(found)

    def _is_discrete_field(self, name):
        """Whether the set a field is declared on is discrete: a finite set of
        labels or of points, an integer range, or the integers, read through
        the named spaces of the stage."""
        term = self.declarations.declared_set_of(name)
        seen = set()
        while True:
            if isinstance(term, terms.Space):
                term = term.set
            if isinstance(term, terms.Named) and term.name in self.declarations.space_terms:
                if term.name in seen:
                    return False
                seen.add(term.name)
                term = self.declarations.space_terms[term.name]
                continue
            break
        if isinstance(term, (terms.FiniteSet, terms.IntegerRange, terms.Points)):
            return True
        return isinstance(term, terms.Named) and term.name in ("ℕ", "ℤ")

    def _typed_set_expression(self, setexpr, *, address, position=(), local=()):
        """The inputs one set expression reads and the type of the set it
        denotes, its endpoint expressions included."""
        if isinstance(setexpr, terms.Space):
            return self._typed_set_expression(
                setexpr.set, address=address, position=position + ("set",), local=local
            )
        value = ExpressionType("set", self._domain(setexpr, address, position, local=local))
        if isinstance(setexpr, terms.Named):
            return _Typed((), (value,))
        if isinstance(setexpr, terms.Interval) and isinstance(setexpr.bounds, terms.Range):
            _refuse_literal_faults(self.declarations, setexpr, address)
            bounds = setexpr.bounds
            args = tuple(
                self._typed_expression(
                    endpoint, address=address, position=position + ("bounds", name), local=local
                )
                for name, endpoint in (("lower", bounds.lower), ("upper", bounds.upper))
            )
            args = self._numeric_arguments(
                setexpr, (bounds.lower, bounds.upper), args, address=address
            )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.FiniteSet):
            args = tuple(
                _Typed((), (ExpressionType("scalar", value.domain),))
                if isinstance(member, str)
                else self._typed_expression(
                    member, address=address, position=position + ("members", i), local=local
                )
                for i, member in enumerate(setexpr.members)
            )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.Product):
            args = tuple(
                self._typed_set_expression(
                    factor, address=address, position=position + ("factors", i), local=local
                )
                for i, factor in enumerate(setexpr.factors)
            )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.IntegerRange):
            _refuse_literal_faults(self.declarations, setexpr, address)
            _refuse_non_parameter_terms(
                self.declarations, setexpr, (setexpr.lower, setexpr.upper), address
            )
            # the two bounds are read as numbers, like an interval's endpoints
            args = tuple(
                self._typed_expression(
                    bound, address=address, position=position + (name,), local=local
                )
                for name, bound in (("lower", setexpr.lower), ("upper", setexpr.upper))
            )
            args = self._numeric_arguments(
                setexpr, (setexpr.lower, setexpr.upper), args, address=address
            )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.Points):
            _refuse_literal_faults(self.declarations, setexpr, address)
            _refuse_non_parameter_terms(self.declarations, setexpr, setexpr.members, address)
            # each member is read as a number, and the set the members lie in
            # as a set
            args = tuple(
                self._typed_expression(
                    member, address=address, position=position + ("members", i), local=local
                )
                for i, member in enumerate(setexpr.members)
            )
            args = self._numeric_arguments(setexpr, setexpr.members, args, address=address)
            if setexpr.superset is not None:
                args = args + (
                    self._typed_set_expression(
                        setexpr.superset,
                        address=address,
                        position=position + ("superset",),
                        local=local,
                    ),
                )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.Functions):
            args = tuple(
                self._typed_set_expression(
                    part, address=address, position=position + (name,), local=local
                )
                for name, part in (("domain", setexpr.domain), ("codomain", setexpr.codomain))
            )
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        if isinstance(setexpr, terms.Comprehension):
            if any(isinstance(condition, terms.Between) for condition in setexpr.conds):
                # the grammar writes no two-bound condition in a set; a term
                # decoded from a saved AST alone can hold one
                raise self.declarations.error(
                    "readable-form",
                    address,
                    (
                        "a set written by comprehension holds a condition with two bounds; no "
                        "construction rule reads one there. Write the two bounds as two conditions"
                    ),
                    write="Write the two bounds as two conditions",
                )
            if (
                not isinstance(setexpr.bound, terms.Subject)
                or len(setexpr.bound.coordinates) != 1
                or not isinstance(setexpr.bound.coordinates[0], terms.Coordinate)
                or setexpr.bound.coordinates[0].at is not None
                or setexpr.base is None
                or not setexpr.conds
                or not all(isinstance(condition, terms.Rel) for condition in setexpr.conds)
            ):
                raise self.declarations.error(
                    "readable-form",
                    address,
                    (
                        "a set written by comprehension binds one bare name, typed by one set, "
                        "under conditions that are relations, `{c : ℝ₊ | c < x}`; no construction "
                        "rule reads another comprehension"
                    ),
                )
            coordinate = setexpr.bound.coordinates[0]
            template = self._binder_input(
                coordinate.stem, setexpr.base, address, position + ("bound",), local=local
            )
            bound = dataclasses.replace(template, identity=_binder_name(address, position, 0))
            base_context, _ = self._typed_set_expression(
                setexpr.base, address=address, position=position + ("base",), local=local
            )
            parts = tuple(
                self._typed_expression(
                    condition,
                    address=address,
                    position=position + ("conds", i),
                    local=local + ((coordinate.stem, bound),),
                )
                for i, condition in enumerate(setexpr.conds)
            )
            body_context = _merge(part.inputs for part in parts)
            context = _merge(
                (
                    tuple(port for port in body_context if port.identity != bound.identity),
                    base_context,
                )
            )
            self._domain(setexpr.base, address, position + ("base",), local=local)
            return _Typed(context, (value,))
        if isinstance(setexpr, (terms.SetUnion, terms.SetDifference)):
            # refuses a member or a side that names a set of labels, a
            # product or a set of functions
            union = isinstance(setexpr, terms.SetUnion)
            parts = (
                tuple((("members", i), member) for i, member in enumerate(setexpr.members))
                if union
                else ((("left",), setexpr.left), (("right",), setexpr.right))
            )
            definitions = self.declarations.space_terms
            for step, part in parts:
                kind = sets.kind_without_numbers(part, definitions)
                if kind is None:
                    continue
                whole, place = ("union", "member") if union else ("difference", f"{step[0]} side")
                is_what = f"which is {kind}"
                if isinstance(part, terms.Named) and part.name in definitions:
                    defined = definitions[part.name]
                    conditioned = isinstance(defined, terms.Comprehension)
                    printed = comprehension_text(defined) if conditioned else to_source(defined)
                    is_what = f"which the file defines as `{printed}`, {kind}"
                raise self.declarations.error(
                    "readable-form",
                    address,
                    (
                        f"the {whole} `{to_source(setexpr)}` has the {place} `{to_source(part)}`, "
                        f"{is_what}; a union and a difference are formed among sets of numbers"
                    ),
                    write=(
                        "Write a set of numbers on each side of the sign: an interval, a "
                        "reserved set, a list of integers, `{1, 2}`, or a named set of numbers"
                    ),
                )
            # each member and each side is typed as a set of its own
            args = tuple(
                self._typed_set_expression(
                    part, address=address, position=position + step, local=local
                )
                for step, part in parts
            )
            if not union and "members" not in position:
                # a difference holds a number; one inside a union, whose
                # position holds the step `members`, is not judged, since
                # another member of the union may hold a number
                _refuse_literal_faults(self.declarations, setexpr, address)
            return _Typed(_merge(arg.inputs for arg in args), (value,))
        raise self.declarations.error(
            "readable-form",
            address,
            (
                f"the set is a {type(setexpr).__name__}, which only a term decoded from a saved "
                f"AST can hold; no construction rule reads one"
            ),
        )

    # -- the lookups the walk reads --

    def _value_type(self, term, domain_id, address, position=(), local=()):
        """The value type, with domain and codomain if callable."""
        candidates = term if isinstance(term, tuple) else (term,)
        for candidate in candidates:
            function = sets.callable_set(candidate, self.declarations.space_terms)
            if function is None:
                continue
            argument_position = position + ("function-domain", domain_id)
            result_position = position + ("function-codomain", domain_id)
            argument = self._domain(function.domain, address, argument_position, local=local)
            result = self._domain(function.codomain, address, result_position, local=local)
            return ExpressionType(
                "function",
                None,
                arguments=(
                    self._value_type(function.domain, argument, address, argument_position, local),
                ),
                results=(
                    self._value_type(function.codomain, result, address, result_position, local),
                ),
            )
        return ExpressionType(self._value_kind(term), domain_id)

    def _value_kind(self, term, active=frozenset()):
        """The kind of a coordinate's value by its set: `state` for a
        product or a tuple with a product among its entries, `scalar`
        otherwise."""
        if isinstance(term, tuple):
            return (
                "state" if any(self._value_kind(t, active) == "state" for t in term) else "scalar"
            )
        if isinstance(term, terms.Call):
            base = coordinate_set_term(term, self.declarations)
            if base is not term:
                return self._value_kind(base, active)
        if isinstance(term, terms.Space):
            return self._value_kind(term.set, active)
        if isinstance(term, terms.Comprehension):
            return self._value_kind(term.base, active)
        if isinstance(term, (terms.Product, terms.Functions)):
            # a collection on an index set carries one entry per member, as a
            # product carries one value per coordinate
            return "state"
        if (
            isinstance(term, terms.Named)
            and term.name in self.declarations.space_terms
            and term.name not in active
        ):
            return self._value_kind(self.declarations.space_terms[term.name], active | {term.name})
        return "scalar"

    def _domain(self, term, address, position, local=()):
        if isinstance(term, terms.Space):
            return self._domain(term.set, address, position + ("set",), local=local)
        if (
            isinstance(term, terms.Sym)
            and isinstance(term.symbol, terms.Constant)
            and term.symbol.name in self.declarations.spaces
        ):
            return Identity("set", stage=self.declarations.stage, field=term.symbol.name)
        if isinstance(term, terms.Named):
            if term.name in self.declarations.spaces:
                return Identity("set", stage=self.declarations.stage, field=term.name)
            return _PRIMITIVE_DOMAINS.get(
                term.name, Identity("primitive", field=term.name, mark="set")
            )
        identity = Identity(
            "set", stage=self.declarations.stage, address=address, mark=repr(position)
        )
        entry = (term, address, position, local)
        if identity in self.pending_domains and self.pending_domains[identity] != entry:
            raise self.declarations.error(
                "not-constructed",
                address,
                "a domain identity has inconsistent lexical scope",
                error_class=NotConstructed,
            )
        self.pending_domains[identity] = entry
        self.domain_terms[identity] = term
        return identity

    def _input_named(self, symbol, local):
        if isinstance(symbol, terms.Constant) and symbol.name in dict(local):
            return dict(local)[symbol.name]
        name = symbol.name
        kind = self.declarations.declared_as(name)
        if isinstance(symbol, terms.Constant) and kind == "function":
            definition = self._typed_function(name)
            # a derived parameter is read as the scalar its definition
            # writes, and a function alias as the function it names
            if definition.kind == "derived_parameter" or (
                definition.kind == "function_alias"
                and definition.value_types[0].kind == "function"
            ):
                value_type = definition.value_types[0]
            else:
                value_type = ExpressionType(
                    kind="function",
                    domain=None,
                    arguments=tuple(p.value_type for p in definition.parameters),
                    results=definition.value_types,
                )
            return ResolvedName(
                identity=definition.identity, value_type=value_type, role="function", perch=None
            )
        if isinstance(symbol, terms.Constant) and kind == "space":
            identity = Identity("set", stage=self.declarations.stage, field=name)
            return ResolvedName(
                identity=identity,
                value_type=ExpressionType("set", identity),
                role="set",
                perch=None,
            )
        if isinstance(symbol, terms.Constant) and kind == "parameter":
            return self.inputs[Identity("parameter", stage=self.declarations.stage, field=name)]
        spelling = field_spelling(terms.Sym(symbol), self.address, self.declarations)
        if spelling in self.aliases:
            return self.aliases[spelling]
        listings = []
        if self.block_id is not None:
            listings = self.declarations.side_entries(
                self.block_id, INPUT
            ) + self.declarations.side_entries(self.block_id, OUTPUT)
        identity = listed_identity(spelling, listings, self.declarations)
        if identity is None:
            identity = listed_identity(spelling, self.declarations.listings, self.declarations)
        if (
            identity is None
            and spelling.mark == CONTINUATION
            and name in self.declarations.multipliers
        ):
            # a multiplier a block body declares is a field no side lists,
            # which the fields table holds
            identity = Identity(
                "field", stage=self.declarations.stage, perch=CONTINUATION, field=name
            )
        if identity is None and kind == "shock":
            identity = Identity("field", stage=self.declarations.stage, perch=SHCK, field=name)
        if identity in self.inputs:
            return self.inputs[identity]
        raise KeyError(f"unresolved semantic input {spelling!r} at {self.address}")

    def _called_definition(self, name, argument_types):
        """The definition a call names, the types of its results, and whether
        it is external. The arity and the kind of each argument are checked
        here; a set inclusion the pass cannot decide is no refusal.

        A parameter required to be opaque is a parameter whose set comes
        from a function with an external body, or from a derivative or an
        inverse of one: the file states no set for it, and a scalar argument
        is admitted there, so that `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)` over an external `𝑢`
        may be applied."""
        if name == self.law_head and self.law_result is not None:
            return Identity("external", field=name), (self.law_result,), True
        if name in self.declarations.functions:
            definition = self._typed_function(name)
            values = definition.value_types
            expected = tuple(p.value_type for p in definition.parameters)
            if definition.kind == "function_alias" and values[0].kind == "function":
                expected, values = values[0].arguments, values[0].results
            self._check_arguments(name, argument_types, expected)
            return definition.identity, values, False
        if name in CALL_OPERATORS:
            return name, (_REAL_TYPE,), False
        identity = Identity("external", field=name)
        result = Identity("external", field=name, mark="result")
        return identity, (ExpressionType("opaque", result),), True

    def _check_arguments(self, name, argument_types, expected):
        """The arity and kinds of a function call's arguments."""
        if len(argument_types) != len(expected):
            raise self.declarations.error(
                "well-typed",
                self.address,
                (
                    f"the call to {name} gives it {len(argument_types)} "
                    f"arguments, and {name} takes {len(expected)}; write "
                    f"one argument for each formal argument of {name}"
                ),
            )
        for i, (actual, required) in enumerate(zip(argument_types, expected)):
            admitted = (actual.kind, required.kind) == ("scalar", "opaque")
            if actual.kind != required.kind and actual.kind != "opaque" and not admitted:
                raise self.declarations.error(
                    "well-typed",
                    self.address,
                    (
                        f"argument {i + 1} of the call to {name} is "
                        f"{_KIND_WORDS[actual.kind]}, and {name} takes "
                        f"{_KIND_WORDS[required.kind]} there; write an argument of that kind"
                    ),
                )

    def _numeric(self, domain):
        """Whether the values of a domain are numbers, by the one decision
        `sets.numeric`: the domain identity is resolved to its
        set term first, and the sets the stage defines by name resolve a name
        inside it."""
        if domain == "primitive:extended-real" or domain in _PRIMITIVE_DOMAINS.values():
            return True
        term = self.domain_terms.get(domain)
        if term is None and isinstance(domain, Identity) and domain.kind == "set":
            term = self.declarations.space_terms.get(domain.field)
        return sets.numeric(term, self.declarations.space_terms)

    def _require_scalar(self, value_type, operand, expr, address):
        """The type a numeric use reads the value at: the value's own type
        where its set holds numbers, the real line where the pass cannot
        decide. A value in a set of labels carries no arithmetic and is
        refused under `well-typed`, naming the operand and the expression
        that reads it."""
        numeric = self._numeric(value_type.domain) if value_type.kind == "scalar" else None
        if numeric is False:
            raise self.declarations.error(
                "well-typed",
                address,
                (
                    f"`{to_source(operand)}` is a label, a member of a finite set "
                    f"of names, and `{_reading_text(expr)}` reads it as a number; a "
                    f"label carries no arithmetic. Select by the label, "
                    f"`(…)[{to_source(operand)}]`, where a value depends on it"
                ),
            )
        if numeric is True:
            return value_type
        return _REAL_TYPE

    def _binder_input(self, name, set_term, address, position, *, local=()):
        root, prefix = self.expression_roots.get(address, (None, ()))
        operator = root if position[: len(prefix)] == prefix else None
        for component in position[len(prefix) : -2]:
            if operator is None:
                break
            operator = (
                operator[component] if isinstance(component, int) else getattr(operator, component)
            )
        if isinstance(operator, terms.Operator) and operator.head == "E":
            identity = Identity("field", stage=self.declarations.stage, perch=SHCK, field=name)
            if identity not in self.inputs or name not in self.declarations.law_of:
                raise self.declarations.error(
                    "not-constructed",
                    address,
                    f"expectation subject {name!r} has no declared distribution",
                    error_class=NotConstructed,
                )
            return self.inputs[identity]
        if (
            isinstance(operator, terms.Operator)
            and operator.head == "D"
            and len(operator.args) == 1
            and isinstance(operator.args[0], terms.Sym)
            and isinstance(operator.args[0].symbol, terms.Constant)
            and operator.args[0].symbol.name in self.declarations.functions
        ):
            function_name = operator.args[0].symbol.name
            declared = self.declarations.functions[function_name]
            for i, (param, domain) in enumerate(declared.domains):
                if param == name:
                    domain_id = (
                        self._domain(domain, declared.address, ("params", i))
                        if domain
                        else "primitive:real"
                    )
                    return ResolvedName(
                        identity=Identity(
                            "function-parameter",
                            owner=Identity(
                                "function", stage=self.declarations.stage, field=function_name
                            ),
                            occurrence=i,
                            field=param,
                        ),
                        value_type=ExpressionType(self._value_kind(domain), domain_id),
                        role="argument",
                        perch=None,
                    )
        try:
            if self.declarations.declared_as(name) == "function":
                raise KeyError(name)
            port = self._input_named(terms.Constant(name), local)
        except KeyError:
            port = ResolvedName(
                identity=name,
                value_type=ExpressionType("scalar", _binder_set(address, position)),
                role="bound",
                perch=None,
            )
        if set_term is not None:
            port = dataclasses.replace(
                port,
                value_type=ExpressionType(
                    self._value_kind(set_term),
                    self._domain(set_term, address, position + ("set",), local=local),
                ),
            )
        return port

    def _selected_type(self, value_type, selector):
        declaration = self.pending_domains.get(value_type.domain)
        local = declaration[3] if declaration is not None else ()
        term = self.domain_terms.get(value_type.domain)
        if isinstance(term, tuple):
            term = next((t for t in term if self._value_kind(t) == "state"), None)
        if isinstance(term, terms.Named) and term.name in self.declarations.space_terms:
            term = self.declarations.space_terms[term.name]
        domain = value_type.domain
        if term is None and isinstance(domain, Identity) and domain.kind == "set":
            term = self.declarations.space_terms.get(domain.field)
        term = coordinate_set_term(term, self.declarations)
        indexed = (
            sets.index_sets(term, self.declarations.space_terms)
            if isinstance(term, terms.setexpr)
            else None
        )
        if indexed is not None and isinstance(selector, (terms.Key, terms.Term)):
            # one key of a collection fixed: the entry lies in the entry set,
            # or in the collection on the remaining factors
            _, rest = indexed
            position = ("selected", selector.at)
            domain = self._domain(rest, self.address, position, local=local)
            return self._value_type(rest, domain, self.address, position, local)
        if isinstance(term, terms.Product) and isinstance(selector, terms.Pos):
            factor = term.factors[selector.at - 1]
            return ExpressionType(
                self._value_kind(factor),
                self._domain(factor, self.address, ("selected", selector.at), local=local),
            )
        if isinstance(term, terms.Product) and isinstance(selector, terms.Key):
            # A key selects a coordinate the construction cannot fix in
            # advance; when every factor is the same set, the selected value
            # lies in that set whatever the key (the key's set and arity are
            # checked by check_selections_and_calls).
            factors = term.factors
            if factors and all(factor == factors[0] for factor in factors):
                return ExpressionType(
                    self._value_kind(factors[0]),
                    self._domain(factors[0], self.address, ("selected", selector.at), local=local),
                )
        if isinstance(term, terms.Tuple):
            _, address, position, local = self.pending_domains[value_type.domain]
            values = tuple(
                self._typed_expression(
                    item, address=address, position=position + ("items", i), local=local
                ).results[0]
                for i, item in enumerate(term.items)
            )
            if isinstance(selector, terms.Pos):
                return values[selector.at - 1]
            if values and all(value == values[0] for value in values):
                return values[0]
        return ExpressionType(
            "opaque", _selected_set(value_type.domain, selector.at, self.address)
        )

    def _note_call(self, reference):
        """Record that the expression under the walk calls a definition of the
        stage; the interior of a `!node` box follows the record to the inputs
        the called definition reads."""
        self.calls.append(reference)

    def _numeric_arguments(self, expr, operands, args, *, address):
        """The typed operands of an arithmetic operation, an ordered
        comparison, a two-bound clause or an interval, each read as a number
        (`_require_scalar`). An operand that is no number is refused under
        `well-typed` where it is read, the refusal naming the operand, what it
        is, the expression that reads it and what to write instead."""
        converted = []
        for operand, (context, values) in zip(operands, args):
            if len(values) != 1 or values[0].kind not in ("scalar", "opaque"):
                kind = values[0].kind if len(values) == 1 else None
                what = _KIND_WORDS.get(kind, f"{len(values)} values")
                advice = _NUMBER_ADVICE.get(kind, "write one number").format(
                    operand=to_source(operand)
                )
                raise self.declarations.error(
                    "well-typed",
                    address,
                    (
                        f"`{to_source(operand)}` is {what}, and `{_reading_text(expr)}` reads it "
                        f"as a number; arithmetic, an ordered comparison and the bounds of an "
                        f"interval read numbers. {advice[0].upper()}{advice[1:]}"
                    ),
                )
            converted.append(
                _Typed(context, (self._require_scalar(values[0], operand, expr, address),))
            )
        return tuple(converted)

    def _cast(self, result, values, address, core, side):
        """The result of one side of the line `core`, the side `side` names
        (`left` or `right`), read at the types the other side requires; two
        sides of different kinds are refused under `well-typed`. For a
        formula by cases `core`, `side` names one of its two branches
        (`then` or `else`), read at the types of the other branch."""
        context, old = result
        if old == values:
            return result
        if (
            len(old) != len(values)
            or any(t.kind == "relation" for t in old + values)
            or any(a.kind != b.kind and a.kind != "opaque" for a, b in zip(old, values))
        ):
            this, other = (
                " and ".join(_KIND_WORDS.get(t.kind, t.kind) for t in kinds) or "nothing"
                for kinds in (old, values)
            )
            here, there, rule = _CAST_WORDS[side]
            raise self.declarations.error(
                "well-typed",
                address,
                f"{here} of `{to_source(core)}` is {this}, and {there} {other}; {rule}",
            )
        return _Typed(context, values)


@dataclasses.dataclass(frozen=True)
class _TypedDefinition:
    """One typed definition of the stage, held while it is constructed: a
    function, a function alias, a correspondence, a distribution declaration
    or a declared set. `context` are the free inputs its body reads, `calls`
    the definitions its body calls in the order the walk meets them, and
    `value_types` the types of its results. The interior of a `!node` box
    follows `context` and `calls` to the inputs a node reads through the
    functions it names."""

    identity: object
    address: object
    kind: str
    parameters: tuple
    context: tuple
    value_types: tuple
    subjects: tuple = ()
    calls: tuple = ()


@dataclasses.dataclass(frozen=True)
class _TypedLine:
    """One typed authored line: the inputs its two sides read, the types of its
    results, the kind of statement it is, the identities it leaves unknown, and
    the definitions it calls."""

    context: tuple
    value_types: tuple
    kind: str
    unknowns: tuple = ()
    calls: tuple = ()


def _reading_text(expr):
    """The text of the expression that reads an operand as a number, as a
    refusal quotes it: a comparison as a condition is written, `d < R` or,
    for the test of a definition by cases, `d = R`, and any other expression
    as the source printer writes it."""
    return condition_text(expr) if isinstance(expr, terms.Rel) else to_source(expr)


def _merge(contexts):
    """Ordered resolved inputs of several sub-expressions, or of the two sides
    of one line, one entry per identity: an identity is read at one type,
    and two entries of one identity that disagree have no common type."""
    ports = {}
    for context in contexts:
        for port in context:
            if port.identity in ports and ports[port.identity] != port:
                raise ValueError(f"incompatible input records for {port.identity!r}")
            ports.setdefault(port.identity, port)
    return tuple(ports.values())


def _line_kind(role, *, relation) -> str:
    """The kind of a typed line: `documentation` for a line of the
    documentation role, otherwise `relation` for a line that states a
    relation, solves for its unknowns or has a clause after `⟂`, and
    `definition` for any other."""
    if role == DOC:
        return "documentation"
    return "relation" if relation else "definition"


def _binder_name(address, position, index) -> str:
    """The name of a binder's own input inside the operator that binds it. The
    operator's context excludes it, so it names no wire, box or record of the
    stage; it is written as a sentence, since it is no spelling of a field."""
    return f"binder {index} of {position!r} in {address}"


def _binder_set(address, position) -> str:
    """The name of the set a binder ranges over where the declarations fix
    none. It names a set term and no wire, box or definition."""
    return f"the set of the binder at {position!r} in {address}"


def _selected_set(domain, selector, address) -> str:
    """The name of the set a selection from a family lies in where the family's
    own set does not fix it. It names a set term and no wire, box or
    definition."""
    return f"the set of member {selector!r} of {domain} in {address}"


# --- the interior of a builder that holds `!node` lines ---


def _builder_nodes(box, nodes, *, boundary, declarations, calls, definitions) -> tuple:
    """The authored nodes of one builder, each with the ordered local
    identities it reads and the identities its own line defines.

    The builder's inputs and outputs are the fields its block's header lists.
    Parameters and function definitions remain in each line's typed inputs. The
    order of a node's inputs is the order of the interior's wires: the names of
    the builder's two sides, then every node's outputs in the order of the
    nodes, then each unlisted state, shock or decision control read by a
    node, in the order of first use.

    The checks of the interior stand here, on the records: two nodes producing
    one identity is refused under `declared-once`, and a node reading an
    identity that is neither a builder input nor an earlier node output,
    reading an output before the node that produces it, or reading it at a type
    differing from its producer's, is refused as unreadable.
    """
    lines = {
        record.address: record
        for record in tuple(boundary)
        + tuple(record for node in nodes for record in node.statements)
    }
    identities = list(dict.fromkeys(ob.name for ob in box.dom.inside + box.cod.inside))
    known = set(identities)
    inputs = {ob.name for ob in box.dom.inside}
    aliases = {}
    for record in lines.values():
        if record.role == "alias":
            for output in record.outputs:
                aliases.setdefault(output.identity, []).append(record.address)
    producers = _node_producers(nodes, lines, declarations)
    at_policy = (
        declarations.block_is_backward(box.name)
        and declarations.backward_perches(box.name)[1] == DECISION
    )
    for identity in producers:
        if identity not in known:
            known.add(identity)
            identities.append(identity)
    written, found = set(), []
    for node in nodes:
        dependencies = _node_inputs(
            node,
            lines=lines,
            aliases=aliases,
            declarations=declarations,
            calls=calls,
            definitions=definitions,
        )
        read = set()
        for port in dependencies:
            identity = port.identity
            if identity not in known:
                if port.role in ("parameter", "function", "set"):
                    continue
                if port.role in (STATE, SHOCK) or (
                    at_policy and port.role == CONTROL and identity.perch == DECISION
                ):
                    # A declared shock law can read the control at which the builder is stated.
                    known.add(identity)
                    identities.append(identity)
                    inputs.add(identity)
                else:
                    raise unreadable_form_refusal(
                        declarations,
                        node.node_id,
                        f"the node reads {_written(identity)}, which is neither an input of "
                        f"the block nor an output of an earlier node",
                    )
            _check_node_read(
                node,
                port,
                producers=producers,
                lines=lines,
                inputs=inputs,
                written=written,
                declarations=declarations,
            )
            read.add(identity)
        node_cod = tuple(output.identity for output in lines[node.node_id].outputs)
        found.append(
            dataclasses.replace(
                node,
                inputs=tuple(identity for identity in identities if identity in read),
                outputs=node_cod,
            )
        )
        written.update(node_cod)
    return tuple(found)


def _written(identity):
    """The name of a field as a line writes it, with the mark of its perch,
    `V[>]` or `c`, for a refusal of an authored node."""
    return f"{identity.field}{WRITTEN_MARK.get(identity.perch, '')}"


def _node_producers(nodes, lines, declarations) -> dict:
    """The node that produces each identity, in the order of the nodes and of
    their outputs; two nodes that produce one identity are refused under
    `declared-once`."""
    producers = {}
    for node in nodes:
        for output in lines[node.node_id].outputs:
            if output.identity in producers:
                raise declarations.error(
                    "declared-once",
                    node.node_id,
                    f"the nodes {producers[output.identity]!r} and {node.node_id!r} both "
                    f"write {_written(output.identity)}",
                )
            producers[output.identity] = node.node_id
    return producers


def _check_node_read(node, port, *, producers, lines, inputs, written, declarations) -> None:
    """A node reads a builder input or the output of an earlier node, at the
    type the node that produces it gives it; any other read is refused as
    unreadable."""
    identity = port.identity
    if identity not in inputs and identity not in written:
        raise unreadable_form_refusal(
            declarations,
            node.node_id,
            f"the node reads {_written(identity)} before an earlier node writes it",
        )
    if identity in producers and port.value_type != next(
        output.value_type
        for output in lines[producers[identity]].outputs
        if output.identity == identity
    ):
        raise unreadable_form_refusal(
            declarations,
            node.node_id,
            f"the node reads {_written(identity)} at another type than the node that writes "
            f"it gives",
        )


def _node_inputs(node, *, lines, aliases, declarations, calls, definitions) -> tuple:
    """The inputs one authored node reads, from the typed records of its lines.

    A line reads the inputs its record holds, less the fields it defines
    itself; an unmarked alias is expanded at every use, so the line that
    defines it is read in its place; and a line that calls a definition of the
    stage reads what that definition's body reads, through the definitions it
    calls in turn. The output of another node is read as it stands and is not
    expanded; the node's own outputs are not among its inputs.
    """
    result, visited_definitions = {}, set()

    def supply(port, active):
        local = aliases.get(port.identity, ())
        if local:
            if len(local) != 1:
                raise declarations.error(
                    "declared-once",
                    node.node_id,
                    f"the node reads {_written(port.identity)}, which {len(local)} lines of "
                    f"its block define",
                )
            visit(local[0], active)
        else:
            previous = result.setdefault(port.identity, port)
            if previous != port:
                raise unreadable_form_refusal(
                    declarations,
                    node.node_id,
                    f"the node reads {_written(port.identity)} at two different types",
                )
            if port.role == "function":
                function(port.identity, active)

    def function(identity, active):
        if identity in visited_definitions or identity not in definitions:
            return
        visited_definitions.add(identity)
        definition = definitions[identity]
        for port in definition.context:
            supply(port, active)
        for reference in definition.calls:
            function(reference, active)

    def visit(address, active):
        if address in active:
            raise unreadable_form_refusal(
                declarations,
                node.node_id,
                f"the node's local definitions contain a cycle through {address!r}",
            )
        line = lines[address]
        for reference in calls[address]:
            function(reference, active | {address})
        defined = {port.identity for port in line.outputs}
        for port in line.inputs:
            if port.identity in defined:
                continue
            supply(port, active | {address})

    for record in node.statements:
        visit(record.address, frozenset())
    for port in lines[node.node_id].outputs:
        result.pop(port.identity, None)
    return tuple(result.values())


def _refuse_non_parameter_terms(declarations, setexpr, parts, address):
    """A bound of a range or a member of a listed set is a number or arithmetic
    of parameters, so that its value is decided at calibration and the kernel
    reads it as an argument: a term that reads a name the stage does not
    declare is refused under `name-in-scope`, and one that applies a function
    or reads a field, a shock or a set under `readable-form`."""
    for part in parts:
        names = sets.parameters_read(part)
        undeclared = [name for name in (names or ()) if declarations.declared_as(name) is None]
        if undeclared:
            raise declarations.error(
                "name-in-scope",
                address,
                (
                    f"the set {to_source(setexpr)} reads {undeclared[0]!r}, which the stage does "
                    "not declare; a bound or a member is a number or arithmetic of declared "
                    "parameters"
                ),
            )
        if names is None or any(declarations.declared_as(name) != "parameter" for name in names):
            raise declarations.error(
                "readable-form",
                address,
                (
                    f"the set {to_source(setexpr)} reads {to_source(part)}, which is no number "
                    "and no arithmetic of parameters; a bound or a member is a number or "
                    "arithmetic of parameters, `{0, …, J}`, so that its value is decided at "
                    "calibration"
                ),
            )


def _refuse_literal_faults(declarations, setexpr, address):
    """A range or a listed set whose written numbers already break its
    conditions, a bound that is no integer, an empty range, two members that
    are one number or a member outside the set the members lie in, is refused
    under `readable-form` where it is typed; a condition that reads a
    parameter is recorded by the fold and decided at calibration. An interval
    whose written endpoints leave it no number, `(2, 1)` or `[1, 1)`, is
    refused under the same rule, and so is a difference whose left side lies
    within its right side, `(0, 1) \\ ℝ₊`."""
    interval = isinstance(setexpr, terms.Interval)
    difference = isinstance(setexpr, terms.SetDifference)
    for fault in sets.literal_faults(setexpr, to_source, declarations.space_terms):
        raise declarations.error(
            "readable-form",
            address,
            (
                f"the set {to_source(setexpr)} {fault}; "
                + (
                    "an interval of numbers holds at least one number, so its lower endpoint "
                    "is below its upper endpoint, or equal to it where both ends are closed"
                    if interval
                    else "a difference holds at least one number, so its left side holds a "
                    "number that its right side does not hold"
                    if difference
                    else "a range has integer bounds in order, and a listed set has distinct "
                    "integer members in the set it names"
                )
            ),
            write=(
                "Write the smaller endpoint first, or `[x, x]` for the set of the one number x"
                if interval
                else "Write a left side that holds a number outside the right side"
                if difference
                else None
            ),
        )
