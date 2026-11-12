"""The expressions the elaboration adds to the parsed AST (maps,
compositions, integrals, suprema, measures, finite products of measures, and
the sets of functions and measures that type them), the operations that
respect their bound variables, and the printer that writes a term as the
mathematical text of a card.

The constructors are generated from `syntax/grammars/semantic.asdl`. A binding
is a pair of a `ResolvedName`, the bound variable, and the set expression it
ranges over. The operations on bound variables rewrite structured terms; they
evaluate no mathematical operation.

The expressions of this module print themselves in the notation of
`format_expression`. A term of `bellman.syntax.terms` and a predicate of
`bellman.native.predicates` print as the dataclasses they are, whichever
modules are imported; their mathematical text is asked for by name,
`format_expression(term)`. An obligation writes its entries by
`obligation_entry` and a predicate by `predicate_text`, in the glyphs the
semgraph documents use. `WireType`, the answer record of a wire's
carrier, stands at the end: it compares two carriers by the alpha-equivalence
of their expressions and prints its carrier in their notation.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, fields, is_dataclass, replace
from numbers import Number as Numeric
from typing import NamedTuple

from bellman.native import predicates as P
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.labels import italic
from bellman.native.predicates import And, Compare, IsInteger, Member, Not, Or, Predicate
from bellman.native.records import (
    ArithmeticHead,
    Condition,
    ExpressionType,
    Record,
    ResolvedName,
    UndeclaredSet,
    require_tuple,
)
from bellman.syntax import layout
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import EXTENDED_REAL, PERCH_MARK
from bellman.typing.sets import endpoints, primitive_of

# --- the expressions and their checks ---


class _Expression:
    __slots__ = ()

    def __post_init__(self):
        if isinstance(self, Apply):
            object.__setattr__(self, "args", tuple(self.args))
        if isinstance(self, Lambda):
            bindings = tuple(_binding(binding) for binding in self.bindings)
            names = tuple(variable.identity for variable, _ in bindings)
            if len(set(names)) != len(names):
                raise ValueError("Lambda bindings must have distinct identities")
            object.__setattr__(self, "bindings", bindings)
        if isinstance(self, (Integral, Sup, Measure, ProductMeasure)):
            object.__setattr__(self, "binding", _binding(self.binding))
        if isinstance(self, Compose):
            object.__setattr__(self, "outputs", tuple(_binding(held) for held in self.outputs))
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in ("domain", "codomain") and not denotes_a_set(value, unresolved=True):
                raise TypeError(f"{type(self).__name__}.{field.name} must be a set expression")
            if field.name in ("body", "measure", "function", "outer", "inner"):
                _require_expression(value, f"{type(self).__name__}.{field.name}")
            _immutable(value)
        if isinstance(self, Apply):
            for argument in self.args:
                _require_expression(argument, "Apply.args")
        if isinstance(self, Unresolved):
            if not isinstance(self.identity, (Identity, str)) or not str(self.identity):
                raise TypeError(
                    "Unresolved.identity must be an existing identity or nonempty name"
                )
            if not isinstance(self.missing, str) or not self.missing.strip():
                raise TypeError("Unresolved.missing must describe the missing information")

    def __str__(self):
        return format_expression(self)

    __repr__ = __str__

    def _repr_markdown_(self):
        return format_expression(self)


# fmt: off
# BEGIN GENERATED SEMANTIC CONSTRUCTORS
@dataclass(frozen=True, slots=True, repr=False)
class Apply(_Expression, T.expr):
    function: T.expr
    args: tuple[T.expr, ...] = ()


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class Lambda(_Expression, T.expr):
    bindings: tuple[tuple[ResolvedName, T.setexpr], ...]
    body: T.expr

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return alpha_equivalent(self, other)

    def __hash__(self):
        return hash(_alpha_key(self))


@dataclass(frozen=True, slots=True, repr=False)
class Compose(_Expression, T.expr):
    outer: T.expr
    inner: T.expr
    outputs: tuple[tuple[ResolvedName, T.setexpr], ...]


@dataclass(frozen=True, slots=True, repr=False)
class Integral(_Expression, T.expr):
    binding: tuple[ResolvedName, T.setexpr]
    measure: T.expr
    body: T.expr


@dataclass(frozen=True, slots=True, repr=False)
class Sup(_Expression, T.expr):
    binding: tuple[ResolvedName, T.setexpr]
    body: T.expr


@dataclass(frozen=True, slots=True, repr=False)
class Measure(_Expression, T.expr):
    domain: T.setexpr
    binding: tuple[ResolvedName, T.setexpr]
    body: T.expr


@dataclass(frozen=True, slots=True, repr=False)
class ProductMeasure(_Expression, T.expr):
    binding: tuple[ResolvedName, T.setexpr]
    body: T.expr


@dataclass(frozen=True, slots=True, repr=False)
class Unresolved(_Expression, T.expr, T.setexpr):
    identity: Identity | str
    missing: str


@dataclass(frozen=True, slots=True, repr=False)
class FunctionSet(_Expression, T.setexpr):
    domain: T.setexpr
    codomain: T.setexpr


@dataclass(frozen=True, slots=True, repr=False)
class MeasurableMapSet(_Expression, T.setexpr):
    domain: T.setexpr
    codomain: T.setexpr


@dataclass(frozen=True, slots=True, repr=False)
class StochasticKernelSet(_Expression, T.setexpr):
    domain: T.setexpr
    codomain: T.setexpr


@dataclass(frozen=True, slots=True, repr=False)
class FiniteMeasureSet(_Expression, T.setexpr):
    domain: T.setexpr


@dataclass(frozen=True, slots=True, repr=False)
class ProbabilityMeasureSet(_Expression, T.setexpr):
    domain: T.setexpr


@dataclass(frozen=True, slots=True, repr=False)
class PowerSet(_Expression, T.setexpr):
    domain: T.setexpr

# END GENERATED SEMANTIC CONSTRUCTORS
# fmt: on


def denotes_a_set(expression, unresolved=False) -> bool:
    """Whether a term denotes a set: a set expression of the abstract
    grammar, a named set, a product, an interval, a finite set, a
    comprehension or a set of maps or measures, or one set of a tuple of
    sets read by a key, with no part left unresolved, or with `unresolved` a
    part held unresolved admitted. It is the sort by which a card spells an
    abbreviation, one of a set in roman and one of a function in italic, and
    the check of the domain and the codomain of a map or a measure."""
    if isinstance(expression, T.Select) and isinstance(expression.family, T.Tuple):
        # one set of a tuple of sets read by a key, `(X_keep, X_adjust)[d]`,
        # the codomain of a law of motion whose lines stand in branches
        return bool(expression.family.items) and all(
            denotes_a_set(item, unresolved) for item in expression.family.items
        )
    return isinstance(expression, T.setexpr) and (
        unresolved or not isinstance(expression, Unresolved)
    )


def _binding(value):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise TypeError("a binding is (ResolvedName, carrier expression)")
    variable, domain = value
    # one variable, or several coordinates bound as one `Subject` of
    # variables, `∫_{(m_d, ν) ∈ ℝ₊₊ × ℝ}`
    bound = variable.coordinates if isinstance(variable, T.Subject) else (variable,)
    if not bound or not all(isinstance(held, ResolvedName) for held in bound):
        raise TypeError("a binding variable must be an existing ResolvedName")
    if not isinstance(domain, T.setexpr):
        raise TypeError("a binding domain must be a set expression")
    return variable, domain


def _require_expression(value, location):
    if not isinstance(value, (T.expr, T.setexpr, P.Predicate, ResolvedName)):
        raise TypeError(f"{location} must be a structured expression or resolved input")


def _immutable(value):
    if value is None or isinstance(value, (str, bytes, Numeric, Identity)):
        return
    if isinstance(value, (tuple, frozenset)):
        for child in value:
            _immutable(child)
        return
    if is_dataclass(value) and not isinstance(value, type) and value.__dataclass_params__.frozen:
        for field in fields(value):
            _immutable(getattr(value, field.name))
        return
    raise TypeError(f"semantic expressions require immutable children; got {type(value).__name__}")


# --- comparison up to the names of bound variables ---


def alpha_equivalent(left, right):
    """Whether two expressions are equal once the names of their bound
    variables are set aside: `x ↦ x²` equals `y ↦ y²` when `x` and `y` range
    over one set."""
    return _alpha_key(left) == _alpha_key(right)


def alpha_key(expression):
    """A hashable structural comparison key with positional bound references.

    Consumers whose record comparison inspects dataclass fields directly can
    compare this key without bypassing the binding rules of Lambda equality.
    Alias expansion remains the caller's responsibility.
    """
    return _alpha_key(expression)


def free_identities(expression):
    """References outside every enclosing binder, including carrier
    references."""
    free = set()
    _alpha_key(expression, collect_free=free)
    return frozenset(free)


def _alpha_key(value, bound=(), collect_free=None):
    """The comparison key of `value`, each bound reference written by the
    position of its binder; every free identity met is added to the set
    `collect_free` when one is given."""

    def reference(identity):
        for index, name in enumerate(reversed(bound)):
            if identity == name:
                return "bound", index
        if collect_free is not None:
            collect_free.add(identity)
        return "free", identity

    def child(item):
        return _alpha_key(item, bound, collect_free)

    if isinstance(value, Identity):
        return reference(value)
    if isinstance(value, ResolvedName):
        return type(value), reference(value.identity), child(variable_metadata(value))
    if isinstance(value, (T.Constant, T.Named)):
        return type(value), reference(variable_identity(value.name))
    if isinstance(value, T.Coordinate):
        return (
            type(value),
            reference(variable_identity(value.stem)),
            child(value.at),
            child(value.classifiers),
            child(variable_metadata(value.stem)),
        )
    if isinstance(value, T.Variable):
        return (
            type(value),
            reference(variable_identity(value.name)),
            child(value.when),
            value.shift,
        )
    if isinstance(value, T.TimeValue):
        return type(value), reference(variable_identity(value.name)), value.time
    if isinstance(value, T.Call):
        return type(value), reference(variable_identity(value.fun)), child(value.args)
    if isinstance(value, Unresolved):
        return type(value), value.identity, value.missing
    parts = binder_parts(value)
    if parts is not None:
        inner = bound + tuple(variable_identity(v) for v in parts.variables)
        shape = (
            _bound_key(value.bound, inner, collect_free, bound)
            if isinstance(value, T.Comprehension)
            else tuple(type(s) for s in value.subs)
            if isinstance(value, T.Operator)
            else ()
        )
        return (
            type(value),
            shape,
            child(tuple(variable_metadata(v) for v in parts.variables)),
            child(parts.outside),
            _alpha_key(parts.bodies, inner, collect_free),
        )
    if isinstance(value, (tuple, frozenset)):
        values = (child(item) for item in value)
        return (type(value), frozenset(values) if isinstance(value, frozenset) else tuple(values))
    if is_dataclass(value) and not isinstance(value, type):
        return type(value), tuple((f.name, child(getattr(value, f.name))) for f in fields(value))
    return value


def variable_metadata(variable):
    if isinstance(variable, ResolvedName):
        return variable.value_type, variable.role, variable.perch
    if isinstance(variable, T.Coordinate):
        return variable.at, variable.classifiers, variable_metadata(variable.stem)
    if isinstance(variable, T.Sym):
        return variable_metadata(variable.symbol)
    if isinstance(variable, T.Constant):
        return variable_metadata(variable.name)
    return ()


def variable_identity(variable):
    if isinstance(variable, ResolvedName):
        return variable.identity
    if isinstance(variable, T.Coordinate):
        return variable_identity(variable.stem)
    if isinstance(variable, T.Sym):
        return variable_identity(variable.symbol)
    if isinstance(variable, T.Constant):
        return variable_identity(variable.name)
    return variable


class _BinderParts(NamedTuple):
    """The parts of an expression that binds variables: the variables it
    binds, its parts outside their scope in the order the expression holds
    them, and its parts inside their scope. The parts outside are the sets
    of a Lambda's variables; the set of an integral's variables and its
    measure; the set of a supremum's variable; the index set of a product of
    measures; the space of a measure and the set of its variable; the base
    of a comprehension; the head of an operator and the set of each variable
    its subscript binds."""

    variables: tuple
    outside: tuple
    bodies: tuple


def binder_parts(value):
    """The `_BinderParts` of an expression that binds variables; None for
    any other expression."""
    if isinstance(value, Lambda):
        return _BinderParts(
            variables=tuple(v for v, _ in value.bindings),
            outside=tuple(d for _, d in value.bindings),
            bodies=(value.body,),
        )
    if isinstance(value, (Integral, Sup, Measure, ProductMeasure)):
        variable, domain = value.binding
        outside = (
            (domain, value.measure)
            if isinstance(value, Integral)
            else (value.domain, domain)
            if isinstance(value, Measure)
            else (domain,)
        )
        # an integral over a point of several coordinates binds them one
        # variable each, as a `Subject`, `∫_{(m_d, ν) ∈ ℝ₊₊ × ℝ} […]`,
        # as a comprehension binds its coordinates
        variables = (
            subject_coordinates(variable) if isinstance(variable, T.Subject) else (variable,)
        )
        return _BinderParts(variables=variables, outside=outside, bodies=(value.body,))
    if isinstance(value, T.Comprehension):
        return _BinderParts(
            variables=subject_coordinates(value.bound), outside=(value.base,), bodies=value.conds
        )
    if isinstance(value, T.Operator):
        return _BinderParts(
            variables=tuple(s.name if isinstance(s, T.Var) else s.var for s in value.subs),
            outside=(value.head, *(None if isinstance(s, T.Var) else s.set for s in value.subs)),
            bodies=value.args,
        )
    return None


def _set_of(value, outside, index):
    """The set the variable at `index` of a binding expression ranges over,
    read from the parts outside its scope as `binder_parts` orders them: its
    own set for a Lambda or an operator, the one set of every variable for an
    integral, a supremum, a measure, a product of measures or a
    comprehension."""
    if isinstance(value, Lambda):
        return outside[index]
    if isinstance(value, T.Operator):
        return outside[index + 1]
    return outside[1] if isinstance(value, Measure) else outside[0]


def subject_coordinates(subject):
    if isinstance(subject, T.Tuple):
        return tuple(variable for item in subject.items for variable in subject_coordinates(item))
    if isinstance(subject, T.Subject):
        return tuple(
            variable
            for coordinate in subject.coordinates
            for variable in subject_coordinates(coordinate)
        )
    if isinstance(subject, T.Group):
        return subject_coordinates(subject.inner)
    if isinstance(subject, (T.Coordinate, T.Sym, T.Constant, ResolvedName, Identity, str)):
        return (subject,)
    raise TypeError("a comprehension binds a structured Subject or resolved reference")


def _bound_key(subject, bound, collect_free, outer_bound):
    if isinstance(subject, str):
        return str, _alpha_key(T.Constant(subject), bound, collect_free)
    if isinstance(subject, (T.Tuple, T.Subject)):
        entries = subject.items if isinstance(subject, T.Tuple) else subject.coordinates
        return type(subject), tuple(
            _bound_key(v, bound, collect_free, outer_bound) for v in entries
        )
    if isinstance(subject, T.Group):
        return (
            type(subject),
            _bound_key(subject.inner, bound, collect_free, outer_bound),
            _alpha_key(subject.classifiers, outer_bound, collect_free),
        )
    if isinstance(subject, T.Coordinate):
        return (
            type(subject),
            _bound_key(subject.stem, bound, collect_free, outer_bound),
            _alpha_key((subject.at, subject.classifiers), outer_bound, collect_free),
        )
    if isinstance(subject, T.Sym):
        return type(subject), _bound_key(subject.symbol, bound, collect_free, outer_bound)
    if isinstance(subject, T.Constant):
        return type(subject), _bound_key(subject.name, bound, collect_free, outer_bound)
    if isinstance(subject, ResolvedName):
        return (
            type(subject),
            _alpha_key(T.Constant(subject.identity), bound, collect_free),
            _alpha_key(variable_metadata(subject), outer_bound, collect_free),
        )
    return _alpha_key(subject, bound, collect_free)


# --- substitution and rebinding ---


def substitute(expression, replacements):
    """Replace each free occurrence of each identity by its expression, all at
    once, first renaming any bound variable whose name an inserted expression
    uses.

    Keys are existing identities or formal names; values are structured
    expressions. Named sets require set-valued replacements. This operation
    does not perform application, alias expansion or mathematical evaluation. A
    replacement of an identity by a reference to itself is no replacement and
    renames no binder.
    """
    replacements = _checked_replacements(replacements)
    if not replacements:
        return expression
    used = _all_names(expression) | _all_names(tuple(replacements.items()))

    def fresh():
        index = 0
        while f"_bound_{index}" in used:
            index += 1
        name = f"_bound_{index}"
        used.add(name)
        return name

    def replace_type(value, mapping, renames):
        domain = value.domain
        if domain in mapping:
            replacement = mapping[domain]
            replacement = replacement.set if isinstance(replacement, T.Space) else replacement
            if not isinstance(replacement, T.setexpr):
                raise TypeError("a ExpressionType domain requires a set-expression replacement")
            if not isinstance(replacement, T.Named) or value.kind == "opaque":
                return semantic_type_of(replacement)
            domain = replacement.name
        elif domain in renames:
            domain = renames[domain]
        return replace(
            value,
            domain=domain,
            arguments=tuple(replace_type(t, mapping, renames) for t in value.arguments),
            results=tuple(replace_type(t, mapping, renames) for t in value.results),
        )

    def replace_metadata(variable, mapping, renames):
        if isinstance(variable, ResolvedName):
            return replace(
                variable, value_type=replace_type(variable.value_type, mapping, renames)
            )
        if isinstance(variable, T.Coordinate):
            return replace(
                variable,
                stem=replace_metadata(variable.stem, mapping, renames),
                at=visit(variable.at, mapping, renames),
                classifiers=visit(variable.classifiers, mapping, renames),
            )
        if isinstance(variable, T.Sym):
            return replace(variable, symbol=replace_metadata(variable.symbol, mapping, renames))
        if isinstance(variable, T.Constant):
            return replace(variable, name=replace_metadata(variable.name, mapping, renames))
        return variable

    def visit(value, mapping, renames, profiles=None):
        profiles = {} if profiles is None else profiles

        def child(item):
            return visit(item, mapping, renames, profiles)

        if isinstance(value, Unresolved):
            return value
        if isinstance(value, T.Sym):
            symbol = value.symbol
            identity = (
                variable_identity(symbol.name)
                if isinstance(symbol, (T.Constant, T.Variable, T.TimeValue))
                else symbol.identity
                if isinstance(symbol, (ResolvedName, Identity))
                else None
            )
            if identity in mapping:
                return mapping[identity]
            return replace(value, symbol=child(symbol))
        if isinstance(
            value, (T.Constant, T.Named, T.Variable, T.TimeValue, ResolvedName, Identity)
        ):
            identity = (
                variable_identity(value.name)
                if isinstance(value, (T.Constant, T.Named, T.Variable, T.TimeValue))
                else value.identity
            )
            if identity in mapping:
                result = mapping[identity]
                if isinstance(value, T.Named):
                    result = result.set if isinstance(result, T.Space) else result
                    if not isinstance(result, T.setexpr):
                        raise TypeError("a named set must be replaced by a set expression")
                return result
            if isinstance(value, ResolvedName):
                value = (
                    replace(value, value_type=profiles[identity])
                    if identity in profiles
                    else replace_metadata(value, mapping, renames)
                )
            if identity in renames:
                if isinstance(value, (T.Constant, T.Named, T.Variable, T.TimeValue)):
                    return replace(value, name=_rename_variable(value.name, renames[identity]))
                return _rename_variable(value, renames[identity])
            return value
        if isinstance(value, T.Call):
            args = child(value.args)
            identity = variable_identity(value.fun)
            if identity in mapping:
                return Apply(mapping[identity], args)
            function = (
                _rename_variable(value.fun, renames[identity])
                if identity in renames
                else value.fun
            )
            return replace(value, fun=function, args=args)
        parts = binder_parts(value)
        if parts is not None:
            names = tuple(variable_identity(v) for v in parts.variables)
            outside = tuple(child(part) for part in parts.outside)
            inner_mapping = {k: v for k, v in mapping.items() if k not in names}
            inner_renames = {k: v for k, v in renames.items() if k not in names}
            inner_profiles = {k: v for k, v in profiles.items() if k not in names}
            occurring = _free_references(parts.bodies)
            captures = set().union(
                *(_free_references(v) for k, v in inner_mapping.items() if k in occurring)
            )
            updated = []
            for index, (variable, name) in enumerate(zip(parts.variables, names)):
                variable = replace_metadata(variable, mapping, renames)
                if isinstance(variable, ResolvedName):
                    if variable.value_type.kind == "function" and isinstance(
                        value, (Lambda, Integral, Sup, Measure, ProductMeasure)
                    ):
                        held = _set_of(value, outside, index)
                        if not alpha_equivalent(held, _set_of(value, parts.outside, index)):
                            variable = replace(variable, value_type=semantic_type_of(held))
                    inner_profiles[name] = variable.value_type
                if name in captures:
                    identity = fresh()
                    inner_renames[name] = identity
                    variable = _rename_variable(variable, identity)
                updated.append(variable)
            inner = tuple(
                visit(body, inner_mapping, inner_renames, inner_profiles) for body in parts.bodies
            )
            return _rebuilt(
                value,
                _BinderParts(variables=tuple(updated), outside=outside, bodies=inner),
                visit_outside=child,
            )
        return _with_children(value, child)

    return visit(expression, replacements, {})


def rebind(expression, new_bindings):
    """Replace bound variables by the caller's bound variables.

    `new_bindings` maps the identity of a bound variable to the bindings,
    `(ResolvedName, domain)` pairs, that stand in its place, one or several.
    Where several stand for one, a Lambda binds them in order, a quantifier
    binds each in its own subscript, a comprehension binds them as its
    coordinates over the product of their domains, and every reference to
    the replaced variable in its scope reads as the tuple of references to
    the new ones; an Integral, a Sup, a Measure and a ProductMeasure bind one
    variable and admit one. A new variable whose name is the name of an
    identity free in the scope it is bound over is primed, `c′`, so that the
    two are told apart. Bindings the caller gives are kept as given; nothing
    else in the expression changes.
    """
    replacements = {
        identity: tuple(_binding(held) for held in bindings)
        for identity, bindings in new_bindings.items()
    }

    def reference(bindings):
        refs = tuple(T.Sym(T.Constant(variable.identity)) for variable, _ in bindings)
        return refs[0] if len(refs) == 1 else T.Tuple(refs)

    def free_names(bodies, mapping, own):
        names = set()
        for identity in free_identities(bodies):
            held = free_identities(mapping[identity]) if identity in mapping else {identity}
            names.update(printed_name(item) for item in held if item not in own)
        return names

    def visit(value, mapping):
        def child(item):
            return visit(item, mapping)

        if isinstance(value, Unresolved):
            return value
        if isinstance(value, T.Sym):
            symbol = value.symbol
            if isinstance(symbol, (T.Constant, ResolvedName, Identity)):
                identity = variable_identity(symbol)
                if identity in mapping:
                    return mapping[identity]
            return replace(value, symbol=child(symbol))
        if isinstance(value, (T.Constant, ResolvedName, Identity)):
            identity = variable_identity(value)
            return mapping[identity] if identity in mapping else value
        if isinstance(value, T.Call):
            identity = variable_identity(value.fun)
            args = child(value.args)
            if identity in mapping:
                return Apply(mapping[identity], args)
            return replace(value, args=args)
        parts = binder_parts(value)
        if parts is not None:
            names = tuple(variable_identity(v) for v in parts.variables)
            outside = tuple(child(part) for part in parts.outside)
            inner = {k: v for k, v in mapping.items() if k not in names}
            groups = [replacements.get(name) for name in names]
            own = {
                variable.identity for group in groups if group is not None for variable, _ in group
            }
            taken = free_names(parts.bodies, inner, own | set(names))
            for index, group in enumerate(groups):
                if group is None:
                    continue
                group = tuple(
                    (_primed(variable), domain)
                    if printed_name(variable.identity) in taken
                    else (variable, domain)
                    for variable, domain in group
                )
                groups[index] = group
                inner[names[index]] = reference(group)
            inner_bodies = tuple(visit(body, inner) for body in parts.bodies)
            return _rebuilt(
                value,
                parts._replace(outside=outside, bodies=inner_bodies),
                visit_outside=child,
                groups=groups,
            )
        return _with_children(value, child)

    return visit(expression, {})


def bound_domains(expression):
    """Every bound variable of an expression with the set it ranges over, by
    identity: the domain of a Lambda binding, of an Integral, Sup, Measure or
    ProductMeasure binding and of a quantifier's subscript, and the base of a
    comprehension over one variable, each read through its restricting
    comprehensions. The first declaration of an identity is kept; a variable
    bound with no set, such as `argmax_{c}`, is recorded with None."""
    found = {}

    def visit(value):
        parts = binder_parts(value)
        if parts is not None:
            variables = parts.variables
            if isinstance(value, (Lambda, T.Operator)):
                domains = tuple(
                    _set_of(value, parts.outside, index) for index in range(len(variables))
                )
            elif isinstance(value, (Integral, Sup, Measure, ProductMeasure)):
                domain = _set_of(value, parts.outside, 0)
                # several coordinates bound as one `Subject` range over the
                # factors of their product, where the domain is one
                domains = (
                    (domain,)
                    if len(variables) == 1
                    else tuple(domain.factors)
                    if isinstance(domain, T.Product) and len(domain.factors) == len(variables)
                    else (None,) * len(variables)
                )
            else:
                domains = parts.outside if len(variables) == 1 else (None,) * len(variables)
            for variable, domain in zip(variables, domains):
                found.setdefault(
                    variable_identity(variable), None if domain is None else _carrier_of(domain)
                )
            for part in parts.outside + tuple(parts.bodies):
                visit(part)
            return
        if isinstance(value, (tuple, frozenset)):
            for item in value:
                visit(item)
        elif (
            is_dataclass(value) and not isinstance(value, type) and not isinstance(value, Identity)
        ):
            for field in fields(value):
                visit(getattr(value, field.name))

    visit(expression)
    return found


def renamed_bound(expression, identity, renamed):
    """An alpha-renaming of one bound identity: `expression` with the bound
    variable `identity` written as the identity `renamed` at each of its
    binders and at every reference to it. The answer is alpha-equivalent to
    `expression` where no name in the scope of those binders is `renamed`;
    the caller chooses `renamed` so, `z′` for the bound `z` of a measure
    whose argument reads a free `z`."""
    if isinstance(expression, Identity):
        return renamed if expression == identity else expression
    if isinstance(expression, ResolvedName) and expression.identity == identity:
        return replace(expression, identity=renamed)
    return _with_children(expression, lambda child: renamed_bound(child, identity, renamed))


def semantic_type_of(carrier):
    """The `ExpressionType` of the values of a carrier set: a function of its
    factors for a set of maps or kernels, a distribution for a set of
    measures, a set for a power set, a scalar for a primitive set or an
    interval, a state for a product, and opaque for any other set."""
    if isinstance(carrier, T.Space):
        return semantic_type_of(carrier.set)
    if isinstance(carrier, T.Comprehension):
        return semantic_type_of(carrier.base)
    if isinstance(carrier, (FunctionSet, MeasurableMapSet)):
        factors = (
            carrier.domain.factors if isinstance(carrier.domain, T.Product) else (carrier.domain,)
        )
        return ExpressionType(
            kind="function",
            domain=None,
            arguments=tuple(map(semantic_type_of, factors)),
            results=(semantic_type_of(carrier.codomain),),
        )
    if isinstance(carrier, StochasticKernelSet):
        return semantic_type_of(
            FunctionSet(carrier.domain, ProbabilityMeasureSet(carrier.codomain))
        )
    if isinstance(carrier, (ProbabilityMeasureSet, FiniteMeasureSet)):
        domain = carrier.domain.name if isinstance(carrier.domain, T.Named) else "measure-space"
        return ExpressionType("distribution", domain)
    if isinstance(carrier, PowerSet):
        return ExpressionType("set", None)
    if carrier == T.FiniteSet((T.Number(0), T.Number(1))):
        return ExpressionType("scalar", "primitive:boolean")
    if isinstance(carrier, T.Named):
        primitive = primitive_of(carrier)
        if primitive is not None:
            return ExpressionType(
                "scalar",
                "primitive:extended-real" if primitive.kind == EXTENDED_REAL else primitive.domain,
            )
        return ExpressionType("opaque", carrier.name)
    if isinstance(carrier, T.Interval):
        bounds = endpoints(carrier)
        extended = (
            bounds is None
            or bounds.lower == -float("inf")
            and bounds.lower_closed
            or bounds.upper == float("inf")
            and bounds.upper_closed
        )
        return ExpressionType(
            "scalar", "primitive:extended-real" if extended else "primitive:real"
        )
    if isinstance(carrier, T.Product):
        return ExpressionType("state", "product")
    return ExpressionType("opaque", "unspecified-carrier")


def _checked_replacements(replacements):
    """The replacements of a substitution, each key checked to be an identity
    or a formal name and each value a structured, immutable expression, less
    the replacements of an identity by a reference to itself."""
    replacements = dict(replacements)
    for identity, value in replacements.items():
        if not isinstance(identity, (Identity, str)) or not str(identity):
            raise TypeError("substitution keys must be identities or nonempty formal names")
        _require_expression(value, "substitution value")
        _immutable(value)
    return {
        identity: value
        for identity, value in replacements.items()
        if not _same_reference(identity, value)
    }


def _same_reference(identity, value):
    """Whether `value` is a reference to `identity` itself, so that replacing
    the one by the other changes nothing."""
    if isinstance(value, T.Sym):
        value = value.symbol
    if isinstance(value, T.Constant):
        return variable_identity(value.name) == identity
    if isinstance(value, T.Named):
        return value.name == identity
    return False


def _all_names(value):
    if isinstance(value, (Identity, str)):
        return {value}
    if isinstance(value, (tuple, frozenset)):
        return set().union(*(_all_names(v) for v in value))
    if is_dataclass(value) and not isinstance(value, type):
        return set().union(*(_all_names(getattr(value, f.name)) for f in fields(value)))
    return set()


def _free_references(value):
    """The identities an expression reads free, those its types name
    included."""
    return free_identities(value) | _type_references(value)


def _type_references(value, bound=()):
    """The set identities the types of an expression name, less those its
    binders bind."""
    if isinstance(value, ExpressionType):
        names = {value.domain} if value.domain is not None and value.domain not in bound else set()
        return names | _type_references(value.arguments + value.results, bound)
    parts = binder_parts(value)
    if parts is not None:
        inner = bound + tuple(variable_identity(v) for v in parts.variables)
        return _type_references(
            tuple(variable_metadata(v) for v in parts.variables) + parts.outside, bound
        ) | _type_references(parts.bodies, inner)
    if isinstance(value, (tuple, frozenset)):
        return set().union(*(_type_references(child, bound) for child in value))
    if is_dataclass(value) and not isinstance(value, type):
        return set().union(
            *(_type_references(getattr(value, f.name), bound) for f in fields(value))
        )
    return set()


def _rename_variable(variable, identity):
    if isinstance(variable, ResolvedName):
        return replace(variable, identity=identity)
    if isinstance(variable, T.Coordinate):
        return replace(variable, stem=_rename_variable(variable.stem, identity))
    if isinstance(variable, T.Sym):
        return replace(variable, symbol=_rename_variable(variable.symbol, identity))
    if isinstance(variable, T.Constant):
        return replace(variable, name=_rename_variable(variable.name, identity))
    return identity


def _with_children(value, child):
    """`value` with `child` applied to each item of a tuple or a frozenset or
    to each field of a dataclass instance; any other value unchanged."""
    if isinstance(value, tuple):
        return tuple(child(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(child(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return replace(value, **{f.name: child(getattr(value, f.name)) for f in fields(value)})
    return value


def _rebuilt(value, parts, *, visit_outside, groups=None):
    """The expression `value` binds variables in, rebuilt from `parts`, its
    `_BinderParts` with the parts outside visited and the bodies rebuilt.
    `groups[i]`, where given, is the bindings that replace the variable
    `parts.variables[i]`, one or several; a variable with no group stays, as
    every variable does where no groups are given. `visit_outside` rebuilds
    the sets the typed group of a comprehension's binder writes."""
    groups = [None] * len(parts.variables) if groups is None else groups
    outside = parts.outside
    if isinstance(value, Lambda):
        bindings = []
        for index, (variable, group) in enumerate(zip(parts.variables, groups)):
            bindings.extend(
                group if group is not None else ((variable, _set_of(value, outside, index)),)
            )
        return replace(value, bindings=tuple(bindings), body=parts.bodies[0])
    if isinstance(value, (Integral, Sup, Measure, ProductMeasure)):
        group = groups[0]
        if group is None:
            binding = (
                _binder(value.binding[0], parts.variables, visit_outside),
                _set_of(value, outside, 0),
            )
        elif len(group) == 1:
            binding = group[0]
        else:
            raise ValueError(
                f"{type(value).__name__} binds one variable; {len(group)} were given for it"
            )
        if isinstance(value, Integral):
            return replace(value, binding=binding, measure=outside[1], body=parts.bodies[0])
        if isinstance(value, (Sup, ProductMeasure)):
            return replace(value, binding=binding, body=parts.bodies[0])
        return replace(value, domain=outside[0], binding=binding, body=parts.bodies[0])
    if isinstance(value, T.Comprehension):
        if all(group is None for group in groups):
            return replace(
                value,
                bound=_replace_coordinates(value.bound, iter(parts.variables), visit_outside),
                base=outside[0],
                conds=parts.bodies,
            )
        return _comprehension_rebound(value, parts, groups)
    subs = []
    for index, (sub, variable, group) in enumerate(zip(value.subs, parts.variables, groups)):
        if group is not None:
            subs.extend(T.In(held, held_domain) for held, held_domain in group)
        elif isinstance(sub, T.Var):
            subs.append(replace(sub, name=variable))
        else:
            subs.append(replace(sub, var=variable, set=_set_of(value, outside, index)))
    return replace(value, head=outside[0], subs=tuple(subs), args=parts.bodies)


def _binder(original, variables, visit_outside=lambda value: value):
    """The binder of an integral, a supremum, a measure or a product of
    measures rebuilt with `variables`: a `Subject` with its coordinates
    replaced in order, one variable otherwise."""
    if isinstance(original, T.Subject):
        return _replace_coordinates(original, iter(variables), visit_outside)
    return variables[0]


def _replace_coordinates(subject, variables, visit_outside=lambda value: value):
    if isinstance(subject, T.Tuple):
        return replace(
            subject,
            items=tuple(_replace_coordinates(c, variables, visit_outside) for c in subject.items),
        )
    if isinstance(subject, T.Subject):
        return replace(
            subject,
            coordinates=tuple(
                _replace_coordinates(c, variables, visit_outside) for c in subject.coordinates
            ),
        )
    if isinstance(subject, T.Group):
        return replace(
            subject,
            inner=_replace_coordinates(subject.inner, variables, visit_outside),
            classifiers=visit_outside(subject.classifiers),
        )
    return next(variables)


def _primed(variable):
    """The same bound variable under its name with a prime, `c′` for `c`."""
    return replace(
        variable, identity=replace(variable.identity, field=variable.identity.field + "′")
    )


def _comprehension_rebound(value, parts, groups):
    """A comprehension with some of its bound coordinates replaced by
    several: the coordinates flattened in order, the base a product of the
    replacing domains where it was one of the replaced, and the bound written
    in the form it had."""
    variables = parts.variables
    flat = tuple(
        held
        for variable, group in zip(variables, groups)
        for held in ((variable,) if group is None else tuple(v for v, _ in group))
    )
    base = parts.outside[0]
    if isinstance(base, T.Product) and len(base.factors) == len(variables):
        factors = tuple(
            factor
            for factor, group in zip(base.factors, groups)
            for factor in ((factor,) if group is None else tuple(d for _, d in group))
        )
        base = factors[0] if len(factors) == 1 else T.Product(factors)
    elif len(variables) == 1:
        domains = tuple(d for _, d in groups[0])
        base = domains[0] if len(domains) == 1 else T.Product(domains)
    if isinstance(value.bound, T.Tuple):
        bound = T.Tuple(tuple(T.Sym(T.Constant(variable_identity(v))) for v in flat))
    elif len(flat) == 1 and not isinstance(value.bound, T.Subject):
        bound = flat[0]
    else:
        bound = T.Subject(flat)
    return replace(value, bound=bound, base=base, conds=parts.bodies)


def _carrier_of(domain):
    """The set a bound variable ranges over, read through the comprehensions
    that restrict it: `{w ∈ (D → L) | guard}` binds `w` over `D → L`."""
    while isinstance(domain, T.Comprehension):
        domain = domain.base
    return domain


# --- the queries of a set of policies ---


class PolicySetParts(NamedTuple):
    """The parts a signature writes a set of functions in: the variables it
    binds, the set of maps they range over and the conditions on them."""

    variables: tuple
    base: object
    conditions: tuple


def policy_set_parts(carrier):
    """The parts a signature writes a set of functions in, since a policy
    prints as its type and its rules: for a set of policies `{c ∈ (Xm → ℝ₊₊)
    | c(m_d) ∈ Γ(m_d)}`, or the power set of one, the bound variables, the
    set of maps and the conditions, `((c,), Xm → ℝ₊₊, (c(m_d) ∈ Γ(m_d),))`,
    so that a card writes `𝑐 : Xm → ℝ₊₊, 𝑐(m_d) ∈ Γ(m_d)`; for any other
    set, no variable, the set itself and no condition. Nothing is rewritten:
    the three parts are the held term's own."""
    while isinstance(carrier, PowerSet):
        carrier = carrier.domain
    if isinstance(carrier, T.Comprehension) and _is_set_of_maps(carrier.base):
        return PolicySetParts(
            variables=tuple(variable_identity(v) for v in subject_coordinates(carrier.bound)),
            base=carrier.base,
            conditions=tuple(carrier.conds),
        )
    return PolicySetParts(variables=(), base=carrier, conditions=())


def _is_set_of_maps(term):
    """Whether a set is a set of maps, `Xm → ℝ₊₊`, or a joint policy's set of
    tuples of functions, a product of sets of maps, `(X → ℝ₊₊) × (X →
    ℝ₊₊)`."""
    maps = (FunctionSet, MeasurableMapSet, StochasticKernelSet)
    if isinstance(term, T.Product):
        return bool(term.factors) and all(isinstance(factor, maps) for factor in term.factors)
    return isinstance(term, maps)


class MembershipParts(NamedTuple):
    subject: object
    base: object
    conditions: tuple


def membership_parts(statement):
    """The parts a card writes a statement that functions lie in a set of maps
    with their feasibility in, as a signature writes a set of policies (the
    rule of an Evaluation, the identity into the declared carrier): for `𝑐 ∈
    (Xm → ℝ₊₊) ∧ 𝑐(m_d) ∈ Γ(m_d)`, a conjunction nested on the left whose
    first term is the membership, the functions, the set of maps and the
    conditions, `(𝑐, Xm → ℝ₊₊, (𝑐(m_d) ∈ Γ(m_d),))`, so that a card writes
    `𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)`; None for any other statement. Nothing
    is rewritten: the three parts are the held term's own."""
    conditions = []
    while isinstance(statement, And):
        conditions.insert(0, statement.right)
        statement = statement.left
    if not isinstance(statement, Member) or not _is_set_of_maps(statement.set):
        return None
    return MembershipParts(statement.subject, statement.set, tuple(conditions))


def stated_function(statement):
    """The identity whose value at a point a relation states: the function
    its left side applies, the name an Evaluation gives a result in `𝑉(m_d)
    = …`, a result's own reference in `(2)(k_d) = E_{Ψ, θ}[…]`, or the
    function its left side names bare, which stands for its value at a point
    of several coordinates that the rule's region note names, `𝑉 = …` on
    `(m, z_d) ∈ ℝ₊₊ × ℝ₊₊` (`card-redesign.md` §2, change 4); None for a
    statement of any other form."""
    if not isinstance(statement, Compare):
        return None
    left = statement.left.function if isinstance(statement.left, Apply) else statement.left
    identity = variable_identity(left)
    return identity if isinstance(identity, Identity) else None


def policy_fields(carrier):
    """The functions a set of policies binds, each as `(field, perch)`: the
    coordinates of the comprehension's subject, `(("c", "dcsn"), ("h_choice",
    "dcsn"))` for a joint policy's set; nothing for any other set."""
    while isinstance(carrier, PowerSet):
        carrier = carrier.domain
    if not isinstance(carrier, T.Comprehension) or not isinstance(carrier.bound, T.Subject):
        return ()
    held = tuple(carrier.bound.coordinates)
    if not all(isinstance(variable, ResolvedName) for variable in held):
        return ()
    return tuple((variable.identity.field, variable.perch) for variable in held)


def projected_policy_set(carrier, controls, position):
    """The set of policies of one component of a joint choice, projected
    from the set of joint policies `carrier`, with the component's own set
    of values. Where the joint policies are one function into the product of
    the controls' sets, its components named by the controls, the component
    is the function of the state into its control's set and the projection
    quantifies the others, `{c ∈ (X → ℝ₊₊) | ∃ h ∈ (X → ℝ₊), …}`; where the
    carrier has another shape, both answers are one unresolved reference to
    the control. `controls` are the identities of the controls of the joint
    choice and `position` the index of the component among them;
    `Wire.component` wraps the answer in the wire's type record."""
    joint = carrier.domain if isinstance(carrier, PowerSet) else carrier
    result = Unresolved(controls[position], "joint relation projection")
    target = result
    if (
        isinstance(joint, T.Comprehension)
        and isinstance(joint.bound, T.Subject)
        and isinstance(joint.base, (MeasurableMapSet, FunctionSet))
        and isinstance(joint.base.codomain, T.Product)
        and len(joint.bound.coordinates) == len(joint.base.codomain.factors) == len(controls)
    ):
        maps = type(joint.base)
        functions = tuple(
            (function, maps(joint.base.domain, codomain))
            for function, codomain in zip(joint.bound.coordinates, joint.base.codomain.factors)
        )
        component, domain = functions[position]
        others = tuple(held for n, held in enumerate(functions) if n != position)
        image = T.Operator(
            "exists", tuple(T.In(function, held) for function, held in others), tuple(joint.conds)
        )
        result = PowerSet(T.Comprehension(T.Subject((component,)), domain, (image,)))
        target = domain.codomain
    return result, target


# --- the printer ---


def format_expression(expression, *, names=(), width=78):
    """Mathematical text for an answer: the document of `format_document` on
    one line where `width` is None, and otherwise laid out within `width`
    columns by the layout engine, breaking at the outermost group first.
    """
    document = format_document(expression, names=names)
    if width is None:
        return layout.flat(document)
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("expression display width must be a positive integer or None")
    return layout.render(document, width=width)


def format_document(expression, *, names=()):
    """The layout document of an expression, laid out by
    `bellman.syntax.layout.render` at a width. A group is a part the layout
    sets on one line where it fits and breaks otherwise; its nest is the
    indentation of its continuation lines. The document holds a group at every
    relation, every operator and the bar of every comprehension, each with a
    nest of two columns.

    `names` is an ordered iterable of `(structured child, declared name)`
    pairs. Recursive structured equality, including alpha equality, selects the
    first matching declared name.
    """
    names = tuple(names.items()) if hasattr(names, "items") else tuple(names)
    return _document_at(expression, names, BOTTOM)


# The precedence of the printed forms, from the forms
# that bind loosest to the ones that bind tightest. A child stands in
# parentheses exactly where its own level is below the level its position
# asks for; a position asks for the level of the operator around it, and one
# more on the right of a left-associative operator, so that `a − (b − c)` keeps
# its parentheses and `a − b − c` drops them.
BOTTOM = 0  # a whole expression, an argument, an item of a tuple
LAMBDA = 1  # a map `x ↦ body`, a quantifier, a measure phrase
ARROW = 2  # a set of maps `A → B`, of measurable maps or of kernels
OR = 3
AND = 4
RELATION = 5  # =, ≤, ∈ and the other relations
ADD = 6  # + and −
PRODUCT = 7  # a product of sets `A × B`
MUL = 8  # · and /
NEG = 9  # the sign −x
POW = 10  # x^y
ATOM = 11  # a name, a number, an application, a bracketed form
SET_CHILD = ARROW + 1  # the position of a set beside ∈, →, × or a binder


# the heads whose operand stands in square brackets: the
# maximand of argmax, max and sup, the summand of a sum, the integrand of an
# expectation
_BRACKETED_HEADS = frozenset({"argmax", "argmin", "max", "min", "sup", "inf", "sum", "E"})


_RELATION_SIGNS = {T.Lt: "<", T.Le: "≤", T.Eq: "=", T.Ge: "≥", T.Gt: ">"}

# the signs of a relation, whose right-hand side `_binary` sets on the line
# after the sign, at the sign's column, where it fits on one line there and
# not after the sign
_RELATIONS = frozenset(_RELATION_SIGNS.values()) | {"∈"}


def _document_at(expression, names=(), precedence=BOTTOM):
    """The layout document of an expression, read directly from its structured
    children.

    `precedence` is the level of the position the expression stands in; the
    expression is set in parentheses exactly when its own form binds looser
    than that level. The maximand of `argmax`, `max` and `sup` and the operand
    of a sum, an expectation and an integral stand in square brackets; a
    quantifier's body keeps its parentheses, since they delimit its scope; a
    sign standing directly after an operator sign is set in parentheses. A map
    prints its binders by name, `m_d ↦ body`, the binders' sets standing on the
    type line of the card that prints it. Every relation, every operator and
    the bar of a comprehension is a group of the document, with a nest of two.

    Existing source terms keep their own printing behavior. This display does
    not provide a source serialization or a parser for mathematical text.
    """
    document, level = _document_and_level(expression, names)
    if level < precedence:
        return layout.concat("(", document, ")")
    return document


class _Printed(NamedTuple):
    """The layout document of an expression and the level at which it binds."""

    document: object
    level: int


# the families of the printed forms, each the classes one printer writes, in
# the order `_document_and_level` tests them
_MAPS = (Apply, Lambda, Compose, Integral, Sup, Measure, ProductMeasure)
_SETS_OF_MAPS = (
    FunctionSet,
    MeasurableMapSet,
    StochasticKernelSet,
    FiniteMeasureSet,
    ProbabilityMeasureSet,
    PowerSet,
)
_STATEMENTS = (T.Slack, T.Equation, T.Inequality, T.Rel, T.Between)
_NAMES = (
    Unresolved,
    Identity,
    ResolvedName,
    T.Coordinate,
    T.Constant,
    T.Named,
    T.Sym,
    T.Variable,
    T.TimeValue,
    T.Number,
    ArithmeticHead,
    UndeclaredSet,
    str,
    Numeric,
)
_ARITHMETIC = (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)
_APPLICATIONS = (T.Call, T.Operator, T.Tuple, T.Select)
_SETS = (
    T.Space,
    T.Product,
    T.Interval,
    T.FiniteSet,
    T.Comprehension,
    T.IntegerRange,
    T.Points,
    T.Functions,
    T.SetUnion,
    T.SetDifference,
)
_PREDICATES = (P.Member, P.Compare, P.Complementarity, P.Not, P.And, P.Or, P.IsInteger)


def _document_and_level(expression, names):
    """The document of `expression` and the level at which it binds: the name
    `names` declares for it, or the document of the printer of its family."""
    contextual = _context_name(expression, names)
    if contextual is not None:
        return _Printed(layout.text(contextual), ATOM)
    for family, printer in (
        (_MAPS, _maps_document),
        (_SETS_OF_MAPS, _sets_of_maps_document),
        (_STATEMENTS, _statements_document),
        (_NAMES, _names_document),
        (_ARITHMETIC, _arithmetic_document),
        (_APPLICATIONS, _applications_document),
        (_SETS, _sets_document),
        (_PREDICATES, _predicates_document),
        ((Condition,), _obligations_document),
    ):
        if isinstance(expression, family):
            return printer(expression, names)
    raise TypeError(f"no mathematical display for {type(expression).__name__}")


def _maps_document(expression, names):
    """The document of an application, a composition, a Lambda, an integral,
    a supremum, a measure or a product of measures, and its level."""
    if isinstance(expression, Apply):
        function = (
            _document_at(expression.function, names)
            if _callable(expression.function, names)
            else layout.concat("(", _document_at(expression.function, names), ")")
        )
        return _Printed(
            layout.concat(
                function, _enclosed("(", _arguments_document(expression.args, names), ")")
            ),
            ATOM,
        )
    if isinstance(expression, Lambda):
        # several binders stand as a list in parentheses, which may break
        # after a comma like an argument list where the column is deep
        binders = [
            layout.text(printed_name(variable, names)) for variable, _ in expression.bindings
        ]
        head = binders[0] if len(binders) == 1 else layout.concat("(", _listed(binders), ")")
        return _Printed(_binary(head, "↦", _document_at(expression.body, names)), LAMBDA)
    if isinstance(expression, Compose):
        # the composition of two maps, `𝑉≻ ∘ 𝑔≻`: a part that is a name
        # stands as it is; an inner map that reads a named function at the
        # point it binds stands as that function with the point left open,
        # `𝑉≻ ∘ 𝑔≻(·, 𝑐)` for the law at the policy written out (RL14;
        # `_opened_document`); any other part stands in parentheses, as the
        # function of an application does
        opened = _opened_document(expression.inner, names)
        parts = [
            opened
            if part is expression.inner and opened is not None
            else _document_at(part, names)
            if _callable(part, names)
            else layout.concat("(", _document_at(part, names), ")")
            for part in (expression.outer, expression.inner)
        ]
        return _Printed(_binary(parts[0], "∘", parts[1]), ATOM)
    if isinstance(expression, Integral):
        variable, _ = expression.binding
        measure = (
            _document_at(expression.measure, names)
            if _callable(expression.measure, names)
            else layout.concat("(", _document_at(expression.measure, names), ")")
        )
        # the integrand follows the binder after a space where it fits on the
        # line, and otherwise stands on a line of its own two columns in from
        # the integral sign; the measure follows the integrand where it fits
        # and stands on the next line otherwise
        return _Printed(
            layout.concat(
                _head_and_operand(
                    layout.concat("∫_{", _bound_document(expression.binding, names), "}"),
                    _enclosed("[", _document_at(expression.body, names), "]"),
                ),
                layout.group(
                    layout.nest(
                        2, layout.line(), measure, "(d", printed_name(variable, names), ")"
                    )
                ),
            ),
            ATOM,
        )
    if isinstance(expression, Sup):
        return _Printed(
            layout.concat(
                "sup_{",
                _bound_document(expression.binding, names),
                "}",
                layout.softline(" "),
                _enclosed("[", _document_at(expression.body, names), "]"),
            ),
            ATOM,
        )
    if isinstance(expression, Measure):
        # a measure by the mass it gives an event, `measure on Xa given by
        # B ↦ μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})`: the event's set, the
        # measurable sets of the space, is held on the binding and printed
        # nowhere, as a map's binders' sets are not
        variable, _ = expression.binding
        return _Printed(
            layout.group(
                "measure on ",
                _document_at(expression.domain, names, SET_CHILD),
                " given by",
                layout.nest(
                    2,
                    layout.line(),
                    printed_name(variable, names),
                    layout.group(
                        layout.nest(2, layout.line(), "↦ ", _document_at(expression.body, names))
                    ),
                ),
            ),
            LAMBDA,
        )
    if isinstance(expression, ProductMeasure):
        # the product of the coordinate laws over a finite index set,
        # `⊗_{i ∈ I_J} TypeIExtremeValue(0, 1)`: the law follows the binder
        # after a space where it fits and on the next line otherwise
        return _Printed(
            layout.group(
                "⊗_{",
                _bound_document(expression.binding, names),
                "}",
                layout.nest(2, layout.line(), _document_at(expression.body, names, LAMBDA)),
            ),
            LAMBDA,
        )


def _sets_of_maps_document(expression, names):
    """The document of a set of maps, measurable maps or kernels, of finite
    measures, of probability measures, or of subsets, and its level."""
    if isinstance(expression, (FunctionSet, MeasurableMapSet)):
        # maps into the subsets of a set are the correspondences into that
        # set, `Xa ⇉ ℝ₊₊`
        several = isinstance(expression.codomain, PowerSet)
        return _Printed(
            _joined(
                (
                    _document_at(expression.domain, names, SET_CHILD),
                    _document_at(
                        expression.codomain.domain if several else expression.codomain,
                        names,
                        SET_CHILD,
                    ),
                ),
                "⇉" if several else "→",
            ),
            ARROW,
        )
    if isinstance(expression, StochasticKernelSet):
        return _Printed(
            layout.concat(
                _document_at(expression.domain, names, SET_CHILD),
                layout.group(
                    layout.nest(
                        2,
                        layout.line(),
                        "→ probability measure on ",
                        _document_at(expression.codomain, names, SET_CHILD),
                    )
                ),
            ),
            ARROW,
        )
    if isinstance(expression, FiniteMeasureSet):
        return _Printed(
            layout.concat("finite measure on ", _document_at(expression.domain, names, SET_CHILD)),
            ATOM,
        )
    if isinstance(expression, ProbabilityMeasureSet):
        return _Printed(
            layout.concat(
                "probability measure on ", _document_at(expression.domain, names, SET_CHILD)
            ),
            ATOM,
        )
    if isinstance(expression, PowerSet):
        return _Printed(
            layout.concat("\U0001d4ab(", _document_at(expression.domain, names), ")"), ATOM
        )


def _clause_document(expression, names):
    """The document of a relation and its bound, `r ⟂ s`, at the level of a
    relation."""
    return _Printed(
        _binary(
            _document_at(expression.core, names, RELATION),
            "⟂",
            _document_at(expression.bound, names, RELATION),
        ),
        RELATION,
    )


def _statements_document(expression, names):
    """The document of a clause, an equation, an inequality, a relation or a
    two-bound clause, and its level."""
    if isinstance(expression, T.Slack):
        # a clause statement, the relation with its complementary inequality,
        # `𝑑𝑢(𝑐(m_r)) = β · 𝑑𝑉_f≻(𝑔≻(m_r, 𝑐(m_r))) ⟂ y_f_ret ≥ 0`
        return _clause_document(expression, names)
    if isinstance(expression, T.Equation):
        return _Printed(
            _binary(
                _document_at(expression.lhs, names, ADD),
                "=",
                _document_at(expression.rhs, names, ADD),
            ),
            RELATION,
        )
    if isinstance(expression, T.Inequality):
        sign = _RELATION_SIGNS[type(expression.op)]
        return _Printed(
            _binary(
                _document_at(expression.lhs, names, ADD),
                sign,
                _document_at(expression.rhs, names, ADD),
            ),
            RELATION,
        )
    if isinstance(expression, T.Rel):
        sign = _RELATION_SIGNS[type(expression.op)]
        return _Printed(
            _binary(
                _document_at(expression.left, names, ADD),
                sign,
                _document_at(expression.right, names, ADD),
            ),
            RELATION,
        )
    if isinstance(expression, T.Between):
        # a two-bound clause, `0 ≤ 𝑐_p(m_f, m_p, w_d) ≤ w_d`,
        # breaking before a sign where long, two columns in
        low, high = _RELATION_SIGNS[type(expression.lo)], _RELATION_SIGNS[type(expression.hi)]
        return _Printed(
            layout.group(
                _document_at(expression.lower, names, ADD),
                layout.nest(
                    2, layout.line(), low + " ", _document_at(expression.middle, names, ADD)
                ),
                layout.nest(
                    2, layout.line(), high + " ", _document_at(expression.upper, names, ADD)
                ),
            ),
            RELATION,
        )


def _names_document(expression, names):
    """The document of a name, a reference, a number or an unresolved
    reference, and its level."""
    if isinstance(expression, Unresolved):
        # the identity may follow the bracket, and what is missing the
        # identity, on the next line
        return _Printed(
            layout.concat(
                "UNRESOLVED[",
                layout.group(
                    layout.nest(2, layout.line(""), f"{printed_name(expression.identity, names)};")
                ),
                layout.group(layout.nest(2, layout.line(), f"{expression.missing}]")),
            ),
            ATOM,
        )
    if isinstance(expression, (Identity, ResolvedName)):
        return _Printed(layout.text(printed_name(expression, names)), ATOM)
    if isinstance(expression, T.Coordinate):
        return _Printed(layout.text(printed_name(expression, names)), ATOM)
    if isinstance(expression, T.Constant) and expression.name == "inf":
        return _Printed(layout.text("∞"), ATOM)
    if isinstance(expression, (T.Constant, T.Named)):
        return _Printed(layout.text(printed_name(expression.name, names)), ATOM)
    if isinstance(expression, T.Sym):
        return _document_and_level(expression.symbol, names)
    if isinstance(expression, T.Variable):
        at = {T.Arrival: "<", T.Decision: "|", T.Continuation: ">"}
        when = (
            at[type(expression.when.side)]
            if isinstance(expression.when, T.At)
            else "~"
            if isinstance(expression.when, T.SteadyState)
            else "t"
        )
        shift = f"{expression.shift:+d}" if expression.shift else ""
        return _Printed(
            layout.text(f"{printed_name(expression.name, names)}[{when}{shift}]"), ATOM
        )
    if isinstance(expression, T.TimeValue):
        return _Printed(
            layout.text(f"{printed_name(expression.name, names)}[{expression.time}]"), ATOM
        )
    if isinstance(expression, T.Number):
        if expression.value in (float("inf"), "inf"):
            return _Printed(layout.text("∞"), ATOM)
        if expression.value in (-float("inf"), "-inf"):
            return _Printed(layout.text("−∞"), NEG)
        negative = isinstance(expression.value, Numeric) and expression.value < 0
        return _Printed(layout.text(str(expression.value)), (NEG if negative else ATOM))
    if isinstance(expression, ArithmeticHead):
        return _Printed(layout.text(expression.head), ATOM)
    if isinstance(expression, UndeclaredSet):
        return _Printed(layout.text("undeclared"), ATOM)
    if isinstance(expression, (str, Numeric)):
        return _Printed(layout.text(str(expression)), ATOM)


def _arithmetic_document(expression, names):
    """The document of a sum, a difference, a product, a quotient, a power
    or a sign, and its level."""
    if isinstance(expression, (T.Add, T.Sub)):
        # a chain of sums and differences is one group: on one line where it
        # fits, and otherwise broken before every sign together, the
        # continuation two columns in
        parts = []
        head, tail = expression, []
        while isinstance(_unwrapped(head), (T.Add, T.Sub)):
            head = _unwrapped(head)
            tail.append(("+" if isinstance(head, T.Add) else "−", head.right))
            head = head.left
        parts.append(_document_at(head, names, ADD))
        for sign, operand in reversed(tail):
            parts.append(
                layout.nest(
                    2,
                    layout.line(),
                    sign + " ",
                    _document_at(operand, names, _right_of(operand, ADD)),
                )
            )
        return _Printed(layout.group(*parts), ADD)
    if isinstance(expression, (T.Mul, T.Div)):
        # a product or a quotient breaks before its sign only where the text
        # up to the next possible break, an argument list's, does not fit,
        # so that `β · 𝑑𝑉_a≻(a_nxt_adj,` keeps its factors together and no
        # factor stands alone on a line
        right = _document_at(expression.right, names, _right_of(expression.right, MUL))
        if isinstance(expression, T.Mul):
            return _Printed(
                layout.concat(
                    _document_at(expression.left, names, MUL),
                    layout.nest(2, layout.softline(), "· ", right),
                ),
                MUL,
            )
        return _Printed(
            layout.concat(
                _document_at(expression.left, names, MUL),
                layout.nest(2, layout.softline(""), "/", right),
            ),
            MUL,
        )
    if isinstance(expression, T.Pow):
        digits = _superscript(expression.exponent)
        if digits is not None:
            # an integer exponent prints as superscript digits, `σ_ψ²`, `c⁻²`;
            # a symbolic
            # exponent keeps the caret, `r^(1 − γ)`
            return _Printed(layout.concat(_document_at(expression.base, names, ATOM), digits), POW)
        return _Printed(
            layout.concat(
                _document_at(expression.base, names, ATOM),
                "^",
                _document_at(expression.exponent, names, ATOM),
            ),
            POW,
        )
    if isinstance(expression, T.Neg):
        # the operand of a sign stands in parentheses where it binds looser
        # than a product, `−(a + b)`, and where it is itself a sign, `−(−a)`;
        # a product or a quotient keeps none, `−σ_ψ²/2`
        operand = _document_at(expression.operand, names, _right_of(expression.operand, MUL - 1))
        if layout.flat(operand) == "∞":
            return _Printed(layout.text("−∞"), NEG)
        return _Printed(layout.concat("−", operand), NEG)


def _applications_document(expression, names):
    """The document of a call, an operator, a tuple or a selection, and its
    level."""
    if isinstance(expression, T.Call):
        return _Printed(
            layout.concat(
                printed_name(expression.fun, names),
                _enclosed("(", _arguments_document(expression.args, names), ")"),
            ),
            ATOM,
        )
    if isinstance(expression, T.Operator):
        subs = _listed(
            layout.text(printed_name(s.name, names))
            if isinstance(s, T.Var)
            else _bound_document((s.var, s.set), names)
            for s in expression.subs
        )
        if expression.head in ("forall", "exists"):
            # the body stands in parentheses, which delimit the quantifier's
            # scope; one statement needs no parentheses of its own inside them,
            # several are conjoined and each stands at the level of a conjunct
            quantifier = "∀" if expression.head == "forall" else "∃"
            body = (
                _document_at(expression.args[0], names)
                if len(expression.args) == 1
                else _conjunction(
                    _document_at(argument, names, AND) for argument in expression.args
                )
            )
            return _Printed(layout.concat(quantifier, " ", subs, ": (", body, ")"), LAMBDA)
        if (
            expression.head == "D"
            and len(expression.args) == 1
            and (
                isinstance(expression.args[0], (Apply, Identity, ResolvedName))
                or (
                    isinstance(expression.args[0], T.Sym)
                    and isinstance(expression.args[0].symbol, T.Constant)
                    and isinstance(expression.args[0].symbol.name, Identity)
                )
            )
        ):
            # the derivative of a value read at a point, `D_{m_next}𝑉≻(𝑔≻(k, ς, Ψ, θ))`,
            # or of the value as a function, `D_{a}𝑉≻`: the operator roman, the
            # function after it with no further parentheses (AMD-MB-001 §4.2; MB-A19)
            applied = _document_at(expression.args[0], names)
            return _Printed(layout.concat("D_{", subs, "}", applied), ATOM)
        head = layout.concat(printed_name(expression.head, names), "_{", subs, "}")
        args = _listed(_document_at(argument, names) for argument in expression.args)
        if expression.head in _BRACKETED_HEADS:
            # the operand of an expectation or a sum follows its head
            # directly, `E_{Ψ}[…]`; a maximand
            # follows its binders after a space, `argmax_{cp ∈ Γ(m_d)} […]`
            if expression.head in ("E", "sum"):
                return _Printed(layout.concat(head, _enclosed("[", args, "]")), ATOM)
            # a maximand follows its binders after a space where it fits on
            # the line, and otherwise stands on a line of its own two columns
            # in from the head
            return _Printed(_head_and_operand(head, _enclosed("[", args, "]")), ATOM)
        if expression.head == "D" and len(expression.args) == 1 and isinstance(expression.args[0], Apply):
            # the derivative of a function read at a point follows its head
            # bare, `D_{m_d}𝑉(m_d)`, the spelling of a derivative term on a
            # value (AMD-MB-001 §4.2, D2); the point's parentheses are the
            # function's own
            return _Printed(layout.concat(head, _document_at(expression.args[0], names)), ATOM)
        return _Printed(layout.concat(head, _enclosed("(", args, ")")), ATOM)
    if isinstance(expression, T.Tuple):
        return _Printed(
            _enclosed("(", _listed(_document_at(item, names) for item in expression.items), ")"),
            ATOM,
        )
    if isinstance(expression, T.Select):
        family = (
            _document_at(expression.family, names)
            if _callable(expression.family, names) or isinstance(expression.family, T.Tuple)
            else layout.concat("(", _document_at(expression.family, names), ")")
        )
        # a key that holds a term is printed as every term is, with the names
        # the card gives it: a function of the card in italic, `[𝑑(a_d)]`;
        # a key that is a name or a position as written
        at = expression.sel.at
        key = (
            _document_at(at, names)
            if isinstance(at, (T.expr, T.setexpr))
            else printed_name(at, names)
        )
        return _Printed(layout.concat(family, "[", key, "]"), ATOM)


def _sets_document(expression, names):
    """The document of a set written as a space, a product, an interval, a
    finite set, a set of functions, a union, a difference or a
    comprehension, and its level."""
    if isinstance(expression, T.Space):
        return _document_and_level(expression.set, names)
    if isinstance(expression, T.Product):
        if not expression.factors:
            return _Printed(layout.text("{()}"), ATOM)
        return _Printed(
            _joined((_document_at(part, names, PRODUCT + 1) for part in expression.factors), "×"),
            PRODUCT,
        )
    if isinstance(expression, T.Interval):
        r = expression.bounds
        left, right = (
            "[" if isinstance(r.left, T.Closed) else "(",
            "]" if isinstance(r.right, T.Closed) else ")",
        )
        return _Printed(
            layout.concat(
                left, _document_at(r.lower, names), ", ", _document_at(r.upper, names), right
            ),
            ATOM,
        )
    if isinstance(expression, T.FiniteSet):
        return _Printed(
            layout.concat(
                "{", _listed(_document_at(member, names) for member in expression.members), "}"
            ),
            ATOM,
        )
    if isinstance(expression, T.IntegerRange):
        return _Printed(
            layout.concat(
                "{",
                _document_at(expression.lower, names),
                ", …, ",
                _document_at(expression.upper, names),
                "}",
            ),
            ATOM,
        )
    if isinstance(expression, T.Points):
        listed = layout.concat(
            "{", _listed(_document_at(member, names) for member in expression.members), "}"
        )
        if expression.superset is None:
            return _Printed(listed, ATOM)
        return _Printed(
            layout.concat(listed, " ⊂ ", _document_at(expression.superset, names, PRODUCT + 1)),
            PRODUCT,
        )
    if isinstance(expression, T.Functions):
        # the arrow binds looser than the product and associates to the right
        return _Printed(
            layout.concat(
                _document_at(expression.domain, names, PRODUCT),
                " → ",
                _document_at(expression.codomain, names, PRODUCT - 1),
            ),
            PRODUCT - 1,
        )
    if isinstance(expression, (T.SetUnion, T.SetDifference)):
        # `A ∪ B` and `A ∖ B` bind looser than the product; an operand that
        # is itself a union, a difference or a set of functions stands in
        # parentheses, so that the text is read one way
        union = isinstance(expression, T.SetUnion)
        operands = expression.members if union else (expression.left, expression.right)

        def operand_level(operand):
            # a listed set with the set its members lie in, `{θ} ⊂ (0, 1)`,
            # stands in parentheses too: its `⊂` would otherwise be read as
            # a claim about the whole union or difference
            listed = isinstance(operand, T.Points) and operand.superset is not None
            return PRODUCT + 1 if listed else PRODUCT

        return _Printed(
            _joined(
                (_document_at(operand, names, operand_level(operand)) for operand in operands),
                "∪" if union else "∖",
            ),
            PRODUCT - 1,
        )
    if isinstance(expression, T.Comprehension):
        # the bound names are a list, which may break after a comma
        bound_names = _listed(
            layout.text(printed_name(variable_identity(v), names))
            for v in subject_coordinates(expression.bound)
        )
        head = layout.concat("{", bound_names)
        if expression.base is not None:
            # the base may follow its `∈` on the next line where the head is
            # long, two columns in
            head = layout.concat(
                head,
                " ∈",
                layout.group(
                    layout.nest(2, layout.line(), _document_at(expression.base, names, SET_CHILD))
                ),
            )
        conditions = [
            condition
            for condition in expression.conds
            if not _same_carrier_restriction(condition, expression.bound, expression.base)
        ]
        if not conditions:
            return _Printed(layout.concat(head, "}"), ATOM)
        body = (
            _document_at(conditions[0], names)
            if len(conditions) == 1
            else _conjunction(_document_at(condition, names, AND) for condition in conditions)
        )
        return _Printed(layout.group(head, " |", layout.nest(2, layout.line(), body), "}"), ATOM)


def _predicates_document(expression, names):
    """The document of a predicate, and its level."""
    if isinstance(expression, P.Member):
        return _Printed(
            _binary(
                _document_at(expression.subject, names, ADD),
                "∈",
                _document_at(expression.set, names, SET_CHILD),
            ),
            RELATION,
        )
    if isinstance(expression, P.Compare):
        sign = {"<=": "≤", ">=": "≥"}.get(expression.relation, expression.relation)
        return _Printed(
            _binary(
                _document_at(expression.left, names, ADD),
                sign,
                _document_at(expression.right, names, ADD),
                kept=isinstance(expression.right, Apply),
            ),
            RELATION,
        )
    if isinstance(expression, P.Complementarity):
        # a relation and its bound at the point,
        # `𝑑𝑢(𝑐(m_d)) = 𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d)))
        # ⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0`, broken before ⟂ when long
        return _clause_document(expression, names)
    if isinstance(expression, P.Not):
        return _Printed(layout.concat("¬(", _document_at(expression.operand, names), ")"), ATOM)
    if isinstance(expression, P.And):
        return _Printed(
            _binary(
                _document_at(expression.left, names, AND),
                "∧",
                _document_at(expression.right, names, AND + 1),
            ),
            AND,
        )
    if isinstance(expression, P.Or):
        return _Printed(
            _binary(
                _document_at(expression.left, names, OR),
                "∨",
                _document_at(expression.right, names, OR + 1),
            ),
            OR,
        )
    if isinstance(expression, P.IsInteger):
        return _Printed(_binary(_document_at(expression.operand, names, ADD), "∈", "ℤ"), RELATION)


def _obligations_document(expression, names):
    """The document of an obligation record, and its level."""
    if isinstance(expression, Condition):
        entries = ", ".join(layout.flat(_document_at(item, names)) for item in expression.entries)
        evidence = "; evidence: " + "; ".join(expression.evidence) if expression.evidence else ""
        return _Printed(
            layout.text(f"{expression.status}[{expression.condition}]({entries}{evidence})"), ATOM
        )


def _bound_document(binding, names):
    """A variable bound in its set, `x ∈ X`: the set may follow its `∈` on the
    next line, two columns in, as the base of a comprehension may; several
    coordinates bound as one, `(m_d, ν)`, are a list that may break."""
    variable, domain = binding
    if isinstance(variable, T.Subject):
        bound_names = _enclosed(
            "(", _listed(layout.text(printed_name(c, names)) for c in variable.coordinates), ")"
        )
    else:
        bound_names = layout.text(printed_name(variable, names))
    return layout.concat(
        bound_names,
        " ∈",
        layout.group(layout.nest(2, layout.line(), _document_at(domain, names, SET_CHILD))),
    )


def _arguments_document(args, names):
    """The arguments of an application, a list that may break after a comma."""
    return _listed(_document_at(argument, names) for argument in _arguments(args))


# the dot that stands for an argument a map leaves open, `𝑔≻(·, 𝑐)` (RL14)
OPEN_ARGUMENT = "·"


def _opened_document(value, names):
    """The document of a map that reads a named function at the point it
    binds, as that function with the point left open: a dot for each bound
    coordinate, which stands as an argument once and in the order bound,
    and each named function read at bound coordinates by its name, which
    stands for its value at the point; `𝑔≻(·, 𝑐)` for `m_d ↦ 𝑔≻(m_d,
    𝑐(m_d))` and `𝑔≻(·, 𝜍, ·, ·)` for `(k_d, Ψ, θ) ↦ 𝑔≻(k_d, 𝜍(k_d), Ψ,
    θ)`, the law of motion at the policy written out (RL14). None for
    every other value, which prints as it is held."""
    if not isinstance(value, Lambda) or not isinstance(value.body, Apply):
        return None
    bound = tuple(variable_identity(variable) for variable, _ in value.bindings)

    def coordinate(term):
        # the bound coordinate a term refers to, None for any other term
        if isinstance(term, (T.Sym, T.Constant, ResolvedName)):
            identity = variable_identity(term)
            return identity if identity in bound else None
        return None

    def named(term):
        # a function referred to by name, no bound coordinate among them
        return coordinate(term) is None and (
            isinstance(term, (T.Sym, T.Constant, ResolvedName, Identity))
            or _context_name(term, names) is not None
        )

    if not named(value.body.function):
        return None
    opened, documents = [], []
    for argument in _arguments(value.body.args):
        held = coordinate(argument)
        if held is not None:
            opened.append(held)
            documents.append(layout.text(OPEN_ARGUMENT))
        elif (
            isinstance(argument, Apply)
            and named(argument.function)
            and all(coordinate(read) is not None for read in _arguments(argument.args))
        ):
            documents.append(_document_at(argument.function, names))
        else:
            return None
    if tuple(opened) != bound:
        return None
    return layout.concat(
        _document_at(value.body.function, names), _enclosed("(", _listed(documents), ")")
    )


def printed_name(value, names=()):
    contextual = _context_name(value, names)
    if contextual is not None:
        return contextual
    if isinstance(value, (T.Coordinate, T.Sym, T.Constant)):
        return printed_name(variable_identity(value), names)
    if isinstance(value, ResolvedName):
        return printed_name(value.identity, names)
    if isinstance(value, T.Subject):
        # several coordinates bound as one, `(m_d, ν)`
        return (
            "("
            + ", ".join(printed_name(coordinate, names) for coordinate in value.coordinates)
            + ")"
        )
    if isinstance(value, Identity):
        if value.kind in ("g", "G"):
            # the law of motion and the value aggregator are functions, and a
            # function prints in mathematical italic: 𝑔, 𝐺
            return italic(value.kind)
        if value.kind == "distribution":
            # a declared shock distribution as a measure, by its subjects,
            # `P_ν`, `P_{Ψ, θ}`
            return declared_distribution_symbol(value.subjects)
        if value.kind == "measure" and value.mark == "with-distribution":
            # a measure extended by a declared shock distribution: its
            # input's name, the measure it is the owner of, followed by the
            # distribution it extends by, `μ⊗P_ν`, `μ≺⊗P_ψ⊗P_ξ`; the
            # distribution by reference to its declaration, so that a card
            # names it as the file declares it, `P_{Ψ|ν}`
            base = (
                printed_name(value.owner, names)
                if isinstance(value.owner, Identity)
                else "μ" + PERCH_MARK.get(value.perch, "")
            )
            law = Identity("distribution", stage=value.stage, subjects=value.subjects)
            return base + "⊗" + printed_name(law, names)
        if value.kind in ("field", "function", "choice") and value.perch is not None:
            # a function wire composed with the law of motion is spelled by
            # its field alone; the composition is a held term, `Compose`,
            # and no suffix
            return value.stem + PERCH_MARK.get(value.perch, "")
        if value.kind == "measure" and value.perch is not None:
            # a measure on one branch by its label, `μ_keep≻`
            return (
                "\u03bc"
                + (f"_{value.field}" if value.field else "")
                + PERCH_MARK.get(value.perch, "")
            )
        if value.is_result:
            # an unnamed result wire, `<address>:<Kind>:<n>:result`, by its
            # spelling without the mark that tells the package the wire from
            # its box, `dcsn_to_arvl.value:Expectation:1`; the identity, the
            # ids of the graph JSON and the keys of every record keep the mark
            # (design pass 14 §4; S-D8, AAS, 21 October 2026)
            return value.stem.removesuffix(":result")
        return value.stem
    return str(value)


def _context_name(value, names):
    if not names:
        return None
    entries = names.items() if hasattr(names, "items") else names
    for candidate, name in entries:
        try:
            if candidate is value or candidate == value:
                return str(name)
        except (TypeError, ValueError):
            continue
    return None


def declared_distribution_symbol(subjects):
    """The symbol of a declared shock probability distribution, `P_ν` or
    `P_{Ψ, θ}`: roman `P` with the subjects as its subscript."""
    subjects = tuple(subjects)
    if len(subjects) == 1 and len(subjects[0]) == 1:
        return "P_" + subjects[0]
    return "P_{" + ", ".join(subjects) + "}"


def _enclosed(opening, document, closing):
    """`document` between `opening` and `closing`, `(…)`, `[…]`, `{…}`, its
    continuation lines aligned at the column after the opening bracket, so
    that a call broken over lines sets its later arguments under the first.
    No line breaks between a name and its opening bracket, whatever the
    column: the bracket and the name before it are one unit. On one line the
    alignment adds nothing: the text is the opening bracket, the document
    and the closing bracket."""
    return layout.concat(opening, layout.align(document), closing)


def _head_and_operand(head, operand):
    """`head`, then its bracketed `operand` after one space where the operand
    fits on the rest of the line, and otherwise on a line of its own two
    columns in from the head's first column: a maximand under
    `argmax_{c ∈ Γ_c(m_f), c_p ∈ Γ_p(w_d)}`, an integrand under
    `∫_{m_d ∈ ℝ₊₊}`. The head and the operand are aligned at the head's first
    column, so that a break inside the head's binders continues there too."""
    return layout.align(head, layout.group(layout.nest(2, layout.line(), operand)))


def _listed(documents):
    """`documents` separated by a comma and a space, one group: on one line
    where they fit, and otherwise one per line, each after a comma, under
    the first, so that the arguments of one call align and break together."""
    parts = []
    for place, document in enumerate(documents):
        if place:
            parts.extend((",", layout.line()))
        parts.append(document)
    return layout.group(*parts) if parts else layout.text("")


def _arguments(args):
    """The printed arguments of an application: a function applied to one
    tuple prints the tuple's components as its arguments, `g(m_d, c)` and
    not `g((m_d, c))`."""
    if len(args) == 1 and isinstance(args[0], T.Tuple):
        return args[0].items
    return args


def _callable(value, names=()):
    """Whether `value` may stand as the function of an application or the
    family of a selection without parentheses: a name, a variable, an
    application, a selection, an unresolved reference, or any child that a
    declared name of `names` replaces."""
    if _context_name(value, names) is not None:
        return True
    return isinstance(
        value,
        (
            Apply,
            T.Call,
            T.Select,
            T.Sym,
            T.Constant,
            T.Named,
            T.Coordinate,
            T.Variable,
            T.TimeValue,
            Identity,
            Unresolved,
            ResolvedName,
            str,
        ),
    )


def _binary(left, sign, right, spaced=True, *, kept=False):
    """`left`, a possible break, then `sign` and `right`: the group of one
    operator, which breaks before its sign with the continuation two columns
    in. A spaced sign has one space on each side; `/` has none. The
    right-hand side of a relation that does not fit on one line after its
    sign but fits at the sign's column stands on the next line at that
    column, on one line, the sign ending the line before it, `μ≻(B) =`
    (`layout.operand`); with `kept`, a right-hand side that is an
    application, which fits there neither but fits two columns to the left,
    stands there, under the relation's first character, so that the
    application a rule states is kept whole where the rule's column holds
    it (`card-redesign.md` §7 item 2; RL14)."""
    if spaced and sign in _RELATIONS:
        return layout.group(
            left, layout.nest(2, layout.operand(sign, right, dedent=2 if kept else 0))
        )
    if spaced:
        return layout.group(left, layout.nest(2, layout.line(), sign + " ", right))
    return layout.group(left, layout.nest(2, layout.line(""), sign, right))


def _joined(documents, sign):
    """`documents` joined by `sign`, a product's `×` or a map's `→`, each
    after a possible break, deciding for itself, with the continuation two
    columns in and the sign at its head, so that a set of maps or a product
    breaks before the sign and never leaves it at the end of a line."""
    parts = []
    for place, document in enumerate(documents):
        if place:
            parts.append(layout.group(layout.nest(2, layout.line(), sign + " ", document)))
        else:
            parts.append(document)
    return layout.concat(*parts) if parts else layout.text("")


def _unwrapped(term):
    """`term` without the `Sym` wrappers around it."""
    while isinstance(term, T.Sym):
        term = term.symbol
    return term


def _right_of(operand, level):
    """The level the right operand of a left-associative operator at `level`
    is printed at: one more than the operator's, and the level of an atom
    where the operand is a sign, so that `a − (−b)` and `a · (−b)` never print
    a sign directly after an operator sign."""
    if isinstance(operand, T.Sym):
        return _right_of(operand.symbol, level)
    if isinstance(operand, T.Neg):
        return ATOM
    if isinstance(operand, T.Number) and isinstance(operand.value, Numeric) and operand.value < 0:
        return ATOM
    return level + 1


_SUPERSCRIPT_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _superscript(exponent):
    """The superscript spelling of an integer exponent, `²`, `⁻²`, and None
    for any other exponent: a written number that is an integer, or the sign
    of one."""
    while isinstance(exponent, T.Sym):
        exponent = exponent.symbol
    negative = False
    if isinstance(exponent, T.Neg):
        exponent, negative = exponent.operand, True
        while isinstance(exponent, T.Sym):
            exponent = exponent.symbol
    if not isinstance(exponent, T.Number):
        return None
    value = exponent.value
    if isinstance(value, bool) or not isinstance(value, Numeric) or value != int(value):
        return None
    if value < 0:
        value, negative = -value, not negative
    return ("⁻" if negative else "") + str(int(value)).translate(_SUPERSCRIPT_DIGITS)


def _conjunction(documents):
    """`documents` joined by ∧, each after a possible break, inside one group
    with the continuation two columns in."""
    documents = list(documents)
    if not documents:
        return layout.text("")
    parts = [documents[0]]
    for document in documents[1:]:
        parts.append(layout.nest(2, layout.line(), "∧ ", document))
    return layout.group(*parts)


def _same_carrier_restriction(condition, bound, base):
    return (
        isinstance(condition, P.Member)
        and variable_identity(condition.subject) == variable_identity(bound)
        and condition.set == base
    )


# --- the text of an obligation's entries and of a predicate ---

# the one word a set the file does not declare prints, in a type and in a
# factor of a domain alike
UNDECLARED_SET_TEXT = "undeclared"


def obligation_entry(entry) -> str:
    """One entry of an obligation as it is shown.

    The entry is typed, and this is the one place that writes each of the
    five kinds: an identity by its spelling, save the parameter of a
    function, which is written by the parameter's name, so that an argument
    inclusion names the coordinate it concerns; a retained set, expression
    or statement by `to_source`; the head of an arithmetic operation by its
    head word; a predicate by its sentence; and the absence of a declared
    set by `UNDECLARED_SET_TEXT`. No entry holds its printed text, and no
    reader takes this text apart again."""
    if isinstance(entry, Identity):
        return entry.field if entry.kind == "function-parameter" else str(entry)
    if isinstance(entry, (T.expr, T.setexpr, T.stmt)):
        return _term_text(entry)
    if isinstance(entry, ArithmeticHead):
        return entry.head
    if isinstance(entry, Predicate):
        return predicate_text(entry)
    if isinstance(entry, UndeclaredSet):
        return UNDECLARED_SET_TEXT
    raise NotImplementedError(
        f"an obligation's entry is an identity, a retained term, the head of an "
        f"arithmetic operation, a predicate or the record of an undeclared set; a "
        f"{type(entry).__name__} is none of these"
    )


def predicate_text(p) -> str:
    """The predicate in the glyphs the semgraph documents use."""
    if isinstance(p, Member):
        return f"{_term_text(p.subject)} ∈ {_term_text(p.set)}"
    if isinstance(p, Compare):
        return f"{_term_text(p.left)} {p.relation} {_term_text(p.right)}"
    if isinstance(p, Not):
        return f"¬({predicate_text(p.operand)})"
    if isinstance(p, And):
        return f"{_group(p.left, And)} ∧ {_group(p.right, And)}"
    if isinstance(p, Or):
        return f"{_group(p.left, Or)} ∨ {_group(p.right, Or)}"
    if isinstance(p, IsInteger):
        return f"{_term_text(p.operand)} ∈ ℤ"
    raise TypeError(f"not a predicate: {type(p).__name__}")


def _term_text(term):
    """A retained term as an obligation writes it: a term of the source by
    `to_source`, and a term that holds a semantic constructor, the condition
    of an aggregation or a maximization with the constructed output
    substituted, by `format_expression`."""
    if _holds_semantic(term):
        return format_expression(term, width=None)
    return to_source(term)


def _holds_semantic(term):
    """Whether a term holds a constructor of the semantic expressions, an
    application, a composition, a Lambda, or a reference by identity, such
    as the residuals `(r₁, r₂)` of a solve's input, which the source printer
    has no rule for."""
    return any(isinstance(node, (_Expression, Identity)) for node in _nodes(term))


def _nodes(node):
    """Every node of a term, depth first: the term, then the nodes of each
    field of a dataclass or of each item of a tuple."""
    yield node
    if is_dataclass(node) and not isinstance(node, type):
        for field in fields(node):
            yield from _nodes(getattr(node, field.name))
    elif isinstance(node, tuple):
        for item in node:
            yield from _nodes(item)


def _group(p, outer) -> str:
    text = predicate_text(p)
    return text if isinstance(p, (Member, Compare, Not, IsInteger, outer)) else f"({text})"


# --- the answer record of a wire's carrier ---


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class WireType(Record):
    """A derived sort descriptor and the expression specifying its carrier.

    The descriptor contains representation, field classification, ordered
    coordinates, argument domain and result set. Neither field is stored on
    the stage. The expression denotes a set, not a numerical approximation.
    """

    sort: tuple
    carrier: T.setexpr
    declarations: tuple = dataclasses.field(default=(), compare=False)

    def __post_init__(self):
        require_tuple(self, "sort")
        if len(self.sort) != 5:
            raise ValueError("a semantic sort descriptor has five components")
        if not isinstance(self.carrier, T.setexpr):
            raise TypeError("a carrier is a structured set expression")
        object.__setattr__(self, "sort", freeze(self.sort))
        object.__setattr__(self, "carrier", freeze(self.carrier))
        object.__setattr__(self, "declarations", freeze(self.declarations))

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return alpha_key((self.sort, self.carrier)) == alpha_key((other.sort, other.carrier))

    def __hash__(self):
        return hash((type(self), alpha_key((self.sort, self.carrier))))

    def __str__(self):
        # the carrier as held: a declared set stands under its name where the
        # file writes the name; `declarations` is read
        # by the encoding, not by the printer
        return format_expression(self.carrier)

    __repr__ = __str__

    def _repr_markdown_(self):
        return "```text\n" + str(self) + "\n```"
