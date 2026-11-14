"""A line's operators and unknowns, read from its retained term.

The operator occurrences a right side holds (`E`, `argmax`, `solve`, `D`,
`evaluate` and `upper_env`) with the kind of target each seeks; the selection
tuples indexed by a shock and the positions at which they read each name; the
names an expression reads that no operator in it binds, with their marks; the
fields a left side names and the type each is listed at; the candidate
statements of a policy block and the systems they form; the expressions of a
bound; and the small readers of a spelling, a coordinate, a classifier and a
source position.
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from bellman.native.identity import Identity
from bellman.native.records import OperatorOccurrence
from bellman.refusals import NotConstructed
from bellman.syntax import terms
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    CONTROL,
    DECISION,
    DOC,
    NODE,
    PERCH_OF_SIDE,
    PERCHES,
    SHCK,
    SHOCK,
    STATE,
    VALUE_ROLES,
    WRITTEN_MARK,
)
from bellman.syntax.walk import children
from bellman.typing import sets
from bellman.typing.typed_expressions import substitute

# --- the operators a line holds ---

# The operator vocabulary: the heads a methods file may name as targets. The
# grammar writes the first four as operator calls with a subscript
# (stage.lark, rule `operator_call`) and `evaluate` and `upper_env` as
# ordinary calls (rule `call`), so those two are occurrences by name.
OPERATOR_VOCABULARY = ("E", "argmax", "solve", "D", "evaluate", "upper_env")
OPERATOR_MEANINGS = {
    "E": "the expectation",
    "argmax": "the maximizer",
    "solve": "root finding",
    "D": "the derivative",
    "evaluate": "the interpolation",
    "upper_env": "the upper envelope",
}
CALL_OPERATORS = ("evaluate", "upper_env")
# The kinds of target a solve, argmax, or upper_env occurrence seeks: an
# interior root, a constrained optimum, or a selection among several optima.
INTERIOR_ROOT, CONSTRAINED_OPTIMUM, SELECTION = (
    "interior_root",
    "constrained_optimum",
    "selection",
)


def occurrence_paths(expr, path, *, slack=False, declarations=None, address=None) -> list:
    """The operator occurrences of an expression in source order, each with
    the path of term fields from `path` to it: every operator call (grammar
    rule `operator_call`: a head with a subscript) and every call to `evaluate`
    or `upper_env` (rule `call`). A `solve` records its binder as unknown, its
    printed argument as residual, and a constrained optimum when the binder is
    constrained or the statement carries a slack clause, else an interior root;
    an `argmax` a constrained optimum, a selection over several written
    alternatives, or an interior root; an `upper_env` a selection."""
    out = []

    def visit(e, path):
        if isinstance(e, terms.Operator):
            out.append(
                _operator_occurrence(
                    e, path, slack=slack, declarations=declarations, address=address
                )
            )
            for i, s in enumerate(e.subs):
                if isinstance(s, terms.In):
                    visit(s.set, path + ("subs", i, "set"))
            for i, a in enumerate(e.args):
                visit(a, path + ("args", i))
        elif isinstance(e, terms.Call):
            if e.fun in CALL_OPERATORS:
                out.append(
                    OperatorOccurrence(
                        head=e.fun,
                        subscripts=(),
                        position=path,
                        unknown=None,
                        target=SELECTION if e.fun == "upper_env" else None,
                    )
                )
            for i, a in enumerate(e.args):
                visit(a, path + ("args", i))
        elif isinstance(e, (terms.Add, terms.Sub, terms.Mul, terms.Div)):
            visit(e.left, path + ("left",))
            visit(e.right, path + ("right",))
        elif isinstance(e, terms.Neg):
            visit(e.operand, path + ("operand",))
        elif isinstance(e, terms.Pow):
            visit(e.base, path + ("base",))
            visit(e.exponent, path + ("exponent",))
        elif isinstance(e, terms.Tuple):
            for i, item in enumerate(e.items):
                visit(item, path + ("items", i))
        elif isinstance(e, terms.Select):
            visit(e.family, path + ("family",))
        elif isinstance(e, terms.Conditional):
            visit(e.test.left, path + ("test", "left"))
            visit(e.test.right, path + ("test", "right"))
            visit(e.then, path + ("then",))
            visit(e.otherwise, path + ("otherwise",))
        elif isinstance(e, terms.Interval) and isinstance(e.bounds, terms.Range):
            visit(e.bounds.lower, path + ("bounds", "lower"))
            visit(e.bounds.upper, path + ("bounds", "upper"))
        elif isinstance(
            e,
            (
                terms.Number,
                terms.Sym,
                terms.Space,
                terms.Named,
                terms.FiniteSet,
                terms.Product,
                terms.Comprehension,
            ),
        ):
            return
        else:
            raise unreadable_form_refusal(
                declarations,
                address,
                "no construction rule reads the operators of a term written on this line",
            )

    # `(*path,)` is a fresh tuple, so two builds share no position object.
    visit(expr, (*path,))
    return out


def _operator_occurrence(e, path, *, slack, declarations=None, address=None) -> OperatorOccurrence:
    subscripts = []
    constrained = False
    for s in e.subs:
        if isinstance(s, terms.Var):
            subscripts.append(s.name)
        elif isinstance(s, terms.In):
            subscripts.append(s.var)
            constrained = True
        else:
            raise unreadable_form_refusal(
                declarations,
                address,
                (
                    f"no construction rule reads a subscript of the operator {e.head!r} "
                    f"written on this line; a subscript is a name (`E_{{θ}}`) or a name in a "
                    f"set (`argmax_{{c : Γ(w)}}`)"
                ),
            )
    unknown = target = None
    if e.head == "solve":
        unknown = subscripts[0] if subscripts else None
        target = CONSTRAINED_OPTIMUM if (slack or constrained) else INTERIOR_ROOT
    elif e.head == "argmax":
        target = (
            CONSTRAINED_OPTIMUM if constrained else SELECTION if len(e.args) > 1 else INTERIOR_ROOT
        )
    return OperatorOccurrence(
        head=e.head, subscripts=tuple(subscripts), position=path, unknown=unknown, target=target
    )


def unreadable_form_refusal(declarations, address, message) -> NotConstructed:
    """The refusal of a form no construction rule of this module reads,
    positioned when the caller knows which item is being read."""
    if declarations is None or address is None:
        return NotConstructed(message, rule="not-constructed")
    return declarations.error("not-constructed", address, message, error_class=NotConstructed)


def check_selections_and_calls(
    expr, address, declarations, local_domains=None, *, local_values=None, language_calls=()
) -> None:
    """The check of every selection from a family and of every call in an
    expression, under the local typed names: a selection is checked by
    `_check_family_selection` and a call by `_check_call`. `language_calls`
    names the functions of the language that the expression calls, `log`,
    `exp`, `min` and `max` in a derived parameter's definition."""
    local_values = {} if local_values is None else local_values

    def visit(e, local):
        if isinstance(e, terms.Select):
            visit(e.family, local)
            _check_family_selection(
                e, local, address=address, declarations=declarations, local_values=local_values
            )
        elif isinstance(e, terms.Call):
            _check_call(e, local, address, declarations, language_calls)
            for arg in e.args:
                visit(arg, local)
        elif isinstance(e, terms.Operator):
            nested = dict(local)
            for sub in e.subs:
                if isinstance(sub, terms.In):
                    visit(sub.set, local)
                    nested[sub.var] = sub.set.set if isinstance(sub.set, terms.Space) else sub.set
                elif isinstance(sub, terms.Var):
                    nested.setdefault(sub.name, declarations.declared_set_of(sub.name))
            for arg in e.args:
                visit(arg, nested)
        elif isinstance(e, terms.Comprehension):
            visit(e.base, local)
            nested = dict(local)
            if isinstance(e.bound, terms.Subject):
                for coordinate in e.bound.coordinates:
                    if isinstance(coordinate, terms.Coordinate):
                        nested[coordinate.stem] = e.base
            for condition in e.conds:
                visit(condition, nested)
        elif dataclasses.is_dataclass(e):
            for field in dataclasses.fields(e):
                value = getattr(e, field.name)
                for child in value if isinstance(value, (tuple, list)) else (value,):
                    if dataclasses.is_dataclass(child):
                        visit(child, local)

    visit(expr, dict(local_domains or {}))


def _check_family_selection(select, local, *, address, declarations, local_values) -> None:
    """A selection by a position reads a coordinate the family has, and one
    by a key reads a finite set of as many members as the family has
    coordinates; any other selection is refused under `family-selection`.

    A Key names a selector variable; members of its finite domain are labels.
    Domain terms are retained from declarations, never recovered from text.
    """

    def refuse(reason, write=None):
        raise declarations.error(
            "family-selection",
            address,
            f"the selection {to_source(select)} {reason}",
            write=write,
        )

    def shape(e):
        return _selection_shape(
            e, local, address=address, declarations=declarations, local_values=local_values
        )

    family_shape = shape(select.family)
    indexed = _indexed_collection(family_shape, declarations)
    if indexed is not None:
        # a collection on an index set: selected by a name declared on the
        # set, never by a position, and the key's set lies in the index set
        first, _ = indexed
        index_set = sets.defined(first, declarations.space_terms)
        by_name = (
            f"Select by a name declared on the index set {to_source(index_set)}, such as "
            f"`{to_source(select.family)}[j]`"
        )
        if isinstance(select.sel, terms.Pos):
            refuse(
                f"selects the position {select.sel.at} of {to_source(select.family)}, a "
                f"collection on the index set {to_source(index_set)}; a collection on an index "
                f"set is selected by a name declared on the set, `{to_source(select.family)}[j]`",
                by_name,
            )
        if not isinstance(select.sel, terms.Key):
            refuse(
                f"selects by a selector no construction rule reads; a collection on an index set "
                f"is selected by a name declared on the set, `{to_source(select.family)}[j]`",
                by_name,
            )
        name = select.sel.at
        key_set = _local_domain(name, local, declarations)
        if key_set is None:
            missing = name not in local and declarations.declared_as(name) is None
            reason = (
                "which the stage does not declare" if missing else "which is declared with no set"
            )
            refuse(
                f"selects by {name!r}, {reason}; a key is a name declared on the index set "
                f"{to_source(index_set)}",
                f"Declare {name} on the index set {to_source(index_set)}",
            )
        decided = sets.index_within(key_set, first, declarations.space_terms)
        if decided is False:
            refuse(
                f"selects by {name!r}, declared in {to_source(key_set)}, which is not within "
                f"the index set {to_source(index_set)} of {to_source(select.family)}; declare "
                f"{name} on the index set, or select under a condition that establishes its "
                f"membership",
                f"Declare {name} on the index set {to_source(index_set)}, or select under a "
                f"condition that establishes its membership",
            )
        return
    members = _coordinate_sets(family_shape, declarations)
    family = to_source(select.family)
    if members is None:
        index = None
        if isinstance(select.sel, terms.Key):
            key = select.sel.at
            index = local[key] if key in local else declarations.declared_set_of(key)
        refuse(
            f"selects from {family}, which is written as no tuple and is declared on no product "
            f"set and no set of functions; a selection reads a coordinate of a tuple, such as "
            f"`(a, b)[1]`, a coordinate of a name declared on a product set, such as "
            f"`{family} : ℝ × ℝ`, or an entry of a collection declared on a set of functions, "
            f"such as `{family} : {'J' if index is None else to_source(index)} → ℝ`, at a name "
            f"declared on its index set",
            f"Select from a tuple, such as `(a, b)[1]`, declare {family} on a product set, such "
            f"as `{family} : ℝ × ℝ`, or declare it on a set of functions, such as "
            f"`{family} : {'J' if index is None else to_source(index)} → ℝ`, and select it "
            f"at a name declared on the index set",
        )
    n = len(members)
    if isinstance(select.sel, terms.Pos):
        if not 1 <= select.sel.at <= n:
            refuse(f"selects position {select.sel.at} from {n} coordinates")
    elif isinstance(select.sel, terms.Key):
        declared = shape(terms.Sym(terms.Constant(select.sel.at)))
        if isinstance(declared, terms.Space):
            declared = declared.set
        if not isinstance(declared, terms.FiniteSet):
            missing = (
                select.sel.at not in local and declarations.declared_as(select.sel.at) is None
            )
            reason = (
                "which the stage does not declare"
                if missing
                else "which is not declared with a suitable set"
            )
            refuse(
                f"selects by {select.sel.at!r}, {reason}; a selection from a tuple of {n} "
                f"coordinates reads a position, such as `{family}[1]`, or a name declared on a "
                f"finite set of {n} members",
                f"Select a position, such as `{family}[1]`, or select by a name declared on a "
                f"finite set of {n} members",
            )
        if len(declared.members) != n:
            refuse(
                f"uses {select.sel.at!r}, whose set has {len(declared.members)} members, "
                f"for {n} coordinates"
            )
    else:
        refuse(
            "selects by a selector no construction rule reads; a selection reads a position or "
            "a name"
        )


def _selection_shape(e, local, *, address, declarations, local_values, resolving=frozenset()):
    """The set of an expression's values, as a selection reads it. A tuple
    has the tuple of its items' sets. A name has the set of the value an
    earlier line of the block defines for it, and otherwise its own set. A
    selection has the set of the coordinate it reads. Any other expression
    has None. `resolving` holds the names whose values are being read, so
    that a name defined through itself is read by its own set."""

    def shape(e, resolving=resolving):
        return _selection_shape(
            e,
            local,
            address=address,
            declarations=declarations,
            local_values=local_values,
            resolving=resolving,
        )

    if isinstance(e, terms.Tuple):
        return tuple(shape(item) for item in e.items)
    if isinstance(e, terms.Sym) and isinstance(e.symbol, (terms.Constant, terms.Variable)):
        ref = field_spelling(e, address, declarations)
        if e.symbol.name not in local and ref in local_values and ref not in resolving:
            return shape(local_values[ref], resolving | {ref})
        return _local_domain(e.symbol.name, local, declarations)
    if isinstance(e, terms.Select):
        family = shape(e.family)
        indexed = _indexed_collection(family, declarations)
        if indexed is not None:
            # one key fixed: the entries' set, or the collection on the
            # remaining factors
            return indexed[1] if isinstance(e.sel, terms.Key) else None
        members = _coordinate_sets(family, declarations)
        if members is None:
            return None
        if isinstance(e.sel, terms.Pos) and 1 <= e.sel.at <= len(members):
            return members[e.sel.at - 1]
        if members and all(member == members[0] for member in members):
            return members[0]
    return None


def _local_domain(name, local, declarations):
    """The set of a name under the local typed names: the set an operator
    binds it over, or else its declared set, with a named set read through
    the stage's spaces, down to the set that gives its coordinates."""
    value = local[name] if name in local else declarations.declared_set_of(name)
    if isinstance(value, terms.Sym) and isinstance(value.symbol, terms.Constant):
        value = declarations.space_terms.get(value.symbol.name, value)
    return coordinate_set_term(value, declarations)


def _indexed_collection(value, declarations):
    """The first index set and the remainder of a collection declared on a
    set of functions, `(I, A)` for `I → A`, read through the stage's named
    sets; None for a tuple of sets and for every other set."""
    if value is None or isinstance(value, tuple):
        return None
    return sets.index_sets(coordinate_set_term(value, declarations), declarations.space_terms)


def _coordinate_sets(value, declarations):
    """The sets of the coordinates of a set, or of a tuple of sets: the
    factors of a product, the items of a tuple; None for any other set."""
    value = coordinate_set_term(value, declarations)
    if isinstance(value, terms.Product):
        return tuple(value.factors)
    return value if isinstance(value, tuple) else None


def _check_call(call, local, address, declarations, language_calls=()) -> None:
    """A call names a function, not a declared value or a name its operator
    binds, and gives a function defined with a body as many arguments as its
    definition declares; otherwise it is refused under `definition-order`.

    `language_calls` names the functions of the language that the expression
    calls, `log`, `exp`, `min` and `max` in a derived parameter's
    definition. A call of one of them is no call of the stage's function of
    that name, so its arguments are not counted against that function's:
    the check of the derived parameters refuses the call under
    `derived-parameter`, whatever number of arguments the stage's function
    takes (`declarations.derived_parameter_fault`)."""
    definition = declarations.callable_definition(call.fun)
    declared = declarations.declared_as(call.fun)
    if declared not in (None, "function") or call.fun in local:
        raise declarations.error(
            "definition-order",
            address,
            f"the call names {call.fun!r}, which is a declared value, not a function",
        )
    if (
        definition is not None
        and definition.slot == "body"
        and call.fun not in language_calls
        and len(call.args) != len(definition.params)
    ):
        raise declarations.error(
            "definition-order",
            address,
            f"the call to {call.fun!r} supplies {len(call.args)} arguments; "
            f"its definition requires {len(definition.params)}",
        )


def coordinate_set_term(term, declarations, active=frozenset()):
    """The set that gives the coordinates of a term's values: the term read
    through spaces, named sets, comprehensions and a called correspondence's
    product or comprehension body; a comprehension's conditions are not
    read here."""
    if isinstance(term, terms.Space):
        return coordinate_set_term(term.set, declarations, active)
    if isinstance(term, terms.Named) and term.name not in active:
        value = declarations.space_terms.get(term.name)
        if value is not None:
            return coordinate_set_term(value, declarations, active | {term.name})
    if isinstance(term, terms.Comprehension):
        return coordinate_set_term(term.base, declarations, active)
    if isinstance(term, terms.Call) and term.fun not in active:
        definition = declarations.callable_definition(term.fun)
        if definition is not None and isinstance(
            definition.body, (terms.Comprehension, terms.Product)
        ):
            body = substitute(
                definition.body,
                {name: argument for (name, _), argument in zip(definition.params, term.args)},
            )
            return coordinate_set_term(body, declarations, active | {term.fun})
    return term


class MarkedName(NamedTuple):
    """A name as a line writes it, with the perch its mark names: `stem` the
    name, `mark` `arvl` or `cntn` for `[<]` or `[>]`, None for a bare name. A
    named tuple, so that it equals the plain pair of the same two values."""

    stem: str
    mark: str | None


def field_spelling(expr, address, declarations) -> MarkedName:
    """The spelling (stem, mark) of a field named by an expression: a bare
    name (`c`, the decision perch or a bare header listing), or a name marked
    `[<]` or `[>]`. Any other left side has no construction rule here."""
    if isinstance(expr, terms.Sym):
        s = expr.symbol
        if isinstance(s, terms.Constant):
            return MarkedName(s.name, None)
        if isinstance(s, terms.Variable) and isinstance(s.when, terms.At) and s.shift == 0:
            return MarkedName(
                s.name, declarations.perch_token(s.when.side, address, f"the mark on {s.name!r}")
            )
    raise unreadable_form_refusal(
        declarations,
        address,
        (
            "the left side of this line names no field; a line defines one field by name "
            "(`c`, `V[<]`, `a[>]`), and the construction reads no other left side"
        ),
    )


def selection_tuples(term, key):
    """The tuples a term selects from by the name `key`, in the order
    written: the family of each `(e₁, …, eₙ)[key]`, and the arguments of an
    `argmax` over the one binder `key`, that tuple read at the binder."""
    found = []

    def visit(node):
        if (
            isinstance(node, terms.Select)
            and isinstance(node.family, terms.Tuple)
            and isinstance(node.sel, terms.Key)
            and node.sel.at == key
        ):
            found.append(tuple(node.family.items))
        elif (
            isinstance(node, terms.Operator)
            and node.head == "argmax"
            and len(node.args) > 1
            and len(node.subs) == 1
            and subscript_binder(node.subs[0]) == key
        ):
            found.append(tuple(node.args))
        if dataclasses.is_dataclass(node) and not isinstance(node, type):
            for field in dataclasses.fields(node):
                visit(getattr(node, field.name))
        elif isinstance(node, tuple):
            for item in node:
                visit(item)

    visit(term)
    return found


def subscript_binder(sub):
    """The name a subscript binds: `d` of `argmax_{d}` and of
    `argmax_{d : J}`."""
    return sub.var if isinstance(sub, terms.In) else sub.name


def expectations_over(term, key):
    """The expectation operators of a term that bind the one name `key`,
    `E_{s}(…)`, in the order written."""
    found = []

    def visit(node):
        if (
            isinstance(node, terms.Operator)
            and node.head == "E"
            and len(node.subs) == 1
            and subscript_binder(node.subs[0]) == key
        ):
            found.append(node)
        if dataclasses.is_dataclass(node) and not isinstance(node, type):
            for field in dataclasses.fields(node):
                visit(getattr(node, field.name))
        elif isinstance(node, tuple):
            for item in node:
                visit(item)

    visit(term)
    return found


def maximand(operator):
    """What an `argmax` maximizes: its one argument, or, over one binder and
    several arguments, the tuple of its arguments indexed by the binder, one
    tuple read one way in the value line and in the policy."""
    if len(operator.args) == 1:
        return operator.args[0]
    if len(operator.subs) == 1:
        return terms.Select(
            terms.Tuple(tuple(operator.args)), terms.Key(subscript_binder(operator.subs[0]))
        )
    return terms.Tuple(tuple(operator.args))


def selection_positions(entries, key, resolve):
    """The positions at which the selection tuples indexed by `key` read
    each name: `entries` holds (address, core) pairs in file order and
    `resolve(address, name, side)` the identity a name reads there, or None;
    each identity maps to its (position, address) pairs in the order met, a
    name inside an entry, `V_w[>] - δ`, at that entry's position."""
    found = {}
    for address, core in entries:
        for items in selection_tuples(core, key):
            for position, item in enumerate(items):
                for name, side in _written_names(item):
                    identity = resolve(address, name, side)
                    if identity is not None:
                        found.setdefault(identity, []).append((position, address))
    return found


def _written_names(term):
    """(name, side) of each name a term writes, in order: `side` the perch a
    mark names, None for a bare name."""
    if isinstance(term, terms.Sym):
        if isinstance(term.symbol, terms.Variable):
            yield (
                term.symbol.name,
                term.symbol.when.side if isinstance(term.symbol.when, terms.At) else None,
            )
        elif isinstance(term.symbol, terms.Constant):
            yield term.symbol.name, None
    elif dataclasses.is_dataclass(term) and not isinstance(term, type):
        for field in dataclasses.fields(term):
            yield from _written_names(getattr(term, field.name))
    elif isinstance(term, tuple):
        for item in term:
            yield from _written_names(item)


# --- the names and the fields a line reads ---

BOUND_OPERATORS = ("E", "argmax", "solve", "D")


def free_names(expr, address, declarations, bound=frozenset(), *, aliases=None):
    """The names an expression reads that no operator in it binds, each a
    `MarkedName`, in source order; the reading of scope and wire checks."""
    return list(
        dict.fromkeys(
            ref
            for ref, _ in _references(
                expr, address, declarations, bound, aliases=aliases, contexts=False
            )
        )
    )


def free_names_with_shocks(expr, address, declarations, bound=frozenset(), *, aliases=None):
    """The names an expression reads that no operator in it binds, each with
    the shocks integrated at its occurrence, in source order. The aliases of
    the block and the bodies of the functions it calls are read in place, so
    that a free name is never read as a variable an unrelated local operator
    binds."""
    return list(
        dict.fromkeys(
            _references(expr, address, declarations, bound, aliases=aliases, contexts=True)
        )
    )


def _references(expr, address, declarations, bound, *, aliases, contexts):
    """The names an expression reads that no operator in it binds, in source
    order, each with the shocks integrated at its occurrence; with
    `contexts`, the aliases and the called functions are read in place."""
    aliases = {} if aliases is None else aliases

    def reference(ref, bound, integrated, env, active, local_aliases):
        if ref.mark is None and ref.stem in bound:
            return []
        if contexts and ref in env:
            return [(r, shocks | integrated) for r, shocks in env[ref]]
        if contexts and ref in local_aliases and ref not in active:
            return visit(
                local_aliases[ref], frozenset(), integrated, {}, active | {ref}, local_aliases
            )
        if contexts and ref.mark is None and ref.stem in declarations.functions:
            definition = declarations.functions[ref.stem]
            return visit(
                definition.body,
                frozenset(p for p, _ in definition.params),
                integrated,
                {},
                active,
                {},
            )
        return [(ref, integrated)]

    def visit(e, bound, integrated, env, active, local_aliases):
        def child(term, names=bound, shocks=integrated, bindings=env):
            return visit(term, names, shocks, bindings, active, local_aliases)

        if isinstance(e, terms.Sym):
            return reference(
                field_spelling(e, address, declarations),
                bound,
                integrated,
                env,
                active,
                local_aliases,
            )
        if isinstance(e, (terms.Number, terms.Space, terms.Named, terms.FiniteSet)):
            return []
        if isinstance(e, (terms.Add, terms.Sub, terms.Mul, terms.Div)):
            return child(e.left) + child(e.right)
        if isinstance(e, terms.Neg):
            return child(e.operand)
        if isinstance(e, terms.Pow):
            return child(e.base) + child(e.exponent)
        if isinstance(e, terms.Call):
            args = [child(a) for a in e.args]
            if contexts and e.fun in declarations.functions:
                definition = declarations.callable_definition(e.fun)
                # Assignments such as du := D_c(u) define a callable rather
                # than a function with an explicit argument list.
                if definition.params:
                    bindings = {
                        MarkedName(p, None): a for (p, _), a in zip(definition.params, args)
                    }
                    return visit(definition.body, frozenset(), integrated, bindings, active, {})
                return sum(args, []) + visit(
                    definition.body, frozenset(), integrated, {}, active, {}
                )
            return sum(args, [])
        if isinstance(e, terms.Operator):
            if contexts and e.head not in BOUND_OPERATORS:
                raise declarations.error(
                    "not-constructed",
                    address,
                    f"the operator {e.head!r} has no supported output-context rule",
                    error_class=NotConstructed,
                )
            names, shocks, out = set(bound), set(integrated), []
            law_dependencies = {}
            for sub in e.subs:
                if isinstance(sub, terms.In):
                    # a binder is in scope in the sets of the binders written
                    # after it, `h_choice : Γ_h(m - c)` after `c : Γ_c(m)`
                    out += child(sub.set, frozenset(names))
                    name = sub.var
                elif isinstance(sub, terms.Var):
                    name = sub.name
                else:
                    raise unreadable_form_refusal(
                        declarations,
                        address,
                        f"no construction rule reads a subscript of the operator {e.head!r} "
                        f"written on this line",
                    )
                if contexts and e.head == "E":
                    if name not in declarations.law_of:
                        raise declarations.error(
                            "not-constructed",
                            address,
                            f"the expectation over {name!r} needs a declared distribution",
                            error_class=NotConstructed,
                        )
                    law_address = declarations.law_of[name]
                    law_key = ("law", law_address)
                    if law_key in active:
                        raise declarations.error(
                            "not-constructed",
                            address,
                            f"the distribution of {name!r} recursively requires "
                            "its own expectation",
                            error_class=NotConstructed,
                        )
                    law_body = next(
                        body for body, at in declarations.law_terms if at == law_address
                    )
                    law_dependencies[law_address] = visit(
                        law_body, frozenset(), integrated, {}, active | {law_key}, {}
                    )
                    shocks.add(name)
                else:
                    names.add(name)
            if law_dependencies:
                out += _joint_integration(
                    law_dependencies, shocks, integrated, declarations, address
                )
            for arg in e.args:
                out += child(arg, frozenset(names), frozenset(shocks))
            return out
        if isinstance(e, terms.Tuple):
            return sum((child(item) for item in e.items), [])
        if isinstance(e, terms.Conditional):
            return sum(
                (child(part) for part in (e.test.left, e.test.right, e.then, e.otherwise)), []
            )
        if isinstance(e, terms.Select):
            out = child(e.family)
            if isinstance(e.sel, terms.Key):
                out += reference(
                    MarkedName(e.sel.at, None), bound, integrated, env, active, local_aliases
                )
            return out
        if isinstance(e, terms.Interval) and isinstance(e.bounds, terms.Range):
            return child(e.bounds.lower) + child(e.bounds.upper)
        if isinstance(e, terms.IntegerRange):
            return child(e.lower) + child(e.upper)
        if isinstance(e, terms.Points):
            out = sum((child(member) for member in e.members), [])
            return out + (child(e.superset) if e.superset is not None else [])
        if isinstance(e, terms.Product):
            return sum((child(item) for item in e.factors), [])
        if isinstance(e, terms.Comprehension):
            # the binder of `{c : ℝ₊₊ | c < x}` is bound in its conditions
            binders = frozenset(bound) | {
                c.stem for c in e.bound.coordinates if isinstance(c, terms.Coordinate)
            }
            out = child(e.base) if e.base is not None else []
            for condition in e.conds:
                out += child(condition.left, binders) + child(condition.right, binders)
            return out
        raise unreadable_form_refusal(
            declarations,
            address,
            "no construction rule reads the fields of a term written on this line",
        )

    return visit(expr, bound, frozenset(), {}, frozenset(), aliases)


def _joint_integration(law_dependencies, shocks, integrated, declarations, address) -> list:
    """The names the distributions of an expectation's shocks read, each with
    the shocks it is integrated over: a conditioning shock the expectation
    names is integrated with the others, and every other name keeps the
    shocks of its own occurrence. The distributions must stand in an order in
    which each is read after those of the shocks it is conditioned on; a
    cycle among them is refused under `not-constructed`."""
    pending = {
        law: {
            declarations.law_of[ref.stem]
            for ref, covered in dependencies
            if ref.mark is None
            and ref.stem in shocks - set(integrated)
            and ref.stem not in covered
        }
        for law, dependencies in law_dependencies.items()
    }
    while pending:
        roots = {
            law for law, dependencies in pending.items() if not dependencies.intersection(pending)
        }
        if not roots:
            raise declarations.error(
                "not-constructed",
                address,
                "the conditional distributions form a cycle and do not supply "
                "a supported joint distribution",
                error_class=NotConstructed,
            )
        pending = {law: dependencies for law, dependencies in pending.items() if law not in roots}
    return [
        (ref, covered | frozenset(shocks) if ref.mark is None and ref.stem in shocks else covered)
        for dependencies in law_dependencies.values()
        for ref, covered in dependencies
    ]


def outputs_and_unknowns(expr, address, declarations, rhs, *, relation=False) -> tuple:
    """The ordered outputs of a scalar statement or an explicit joint
    choice, and the unknowns of a candidate statement: an equation whose
    left side is neither a name nor a tuple of names states a relation in
    the outputs of its block it mentions, and those are what it defines. An
    inequality of that form states a relation and no equation (`relation`),
    so it names no output and is retained with none."""
    if (
        isinstance(expr, terms.Tuple)
        and names_fields(expr)
        and not (isinstance(rhs, terms.Operator) and rhs.head in ("argmax", "solve"))
    ):
        raise unreadable_form_refusal(
            declarations,
            address,
            "a tuple left side is constructed for one explicit argmax or solve; "
            "ordinary tuple assignments are not constructed",
        )
    if not names_fields(expr):
        return () if relation else _candidate_names(expr, rhs, address, declarations)
    items = expr.items if isinstance(expr, terms.Tuple) else (expr,)
    fields = tuple(field_spelling(item, address, declarations) for item in items)
    if not fields or len(set(fields)) != len(fields):
        raise declarations.error(
            "declared-once", address, "a statement's left side must name distinct fields"
        )
    return fields


def derivative_left_side(expr) -> bool:
    """Whether a left side is one derivative term of one field, `D_{m_d}V`: the
    line is then a derivative line, a statement about the value the builder
    writes, which defines no field and names no unknown (AMD-MB-001 §4.3)."""
    return (
        isinstance(expr, terms.Operator)
        and expr.head == "D"
        and len(expr.subs) == 1
        and len(expr.args) == 1
        and isinstance(expr.subs[0], terms.Var)
        and isinstance(expr.args[0], terms.Sym)
        and isinstance(expr.args[0].symbol, (terms.Variable, terms.Constant))
    )


def names_fields(expr) -> bool:
    """Whether a left side is a name or a tuple of names."""
    if isinstance(expr, terms.Tuple):
        return bool(expr.items) and all(isinstance(item, terms.Sym) for item in expr.items)
    return isinstance(expr, terms.Sym)


INPUT, OUTPUT = "input", "output"


def _candidate_names(expr, rhs, address, declarations) -> tuple:
    """The candidate spellings of a candidate statement. A field's name
    occurs when it stands on either side of the equation after the
    substitution of the block's aliases: an argument of a call is an
    occurrence, the body of a called function is not read, no law of motion
    is followed, and the clause after the complementarity sign is not read,
    since only the equation is given here."""
    block_id = Identity("line", address=address).block
    out_listings = declarations.side_entries(block_id, OUTPUT)
    aliases, defined = {}, []
    for _, other, item in declarations.bodies.get(block_id, ()):
        marks, _ = annotation_entries(item.annot, other, declarations)
        if DOC in marks:
            continue
        core = item.core.core if isinstance(item.core, terms.Slack) else item.core
        if not isinstance(core, terms.Equation) or not names_fields(core.lhs):
            continue
        items = core.lhs.items if isinstance(core.lhs, terms.Tuple) else (core.lhs,)
        for item_expr in items:
            spelling = field_spelling(item_expr, other, declarations)
            defined.append(spelling)
            if listed_identity(spelling, out_listings, declarations) is None:
                aliases[spelling] = core.rhs
    mentions = []
    for side in (expr, rhs):
        mentioned, _ = mentions_after_aliases(side, aliases, address, declarations)
        for spelling in mentioned:
            if spelling not in mentions:
                mentions.append(spelling)

    def identity(spelling):
        """The field a spelling names, or None where it names an alias, a
        parameter or a function, which is the output of no block."""
        stem, mark = spelling
        perch = mark if mark is not None else perch_of_spelling(spelling, block_id, declarations)
        return (
            Identity("field", stage=declarations.stage, perch=perch, field=stem)
            if perch is not None
            else None
        )

    spelled = {}
    for spelling in reversed(mentions):
        found = identity(spelling)
        if found is not None:
            spelled[found] = spelling
    outputs = tuple(l.wire_type for l in out_listings)
    named = tuple(found for found in (identity(s) for s in defined) if found is not None)
    return tuple(spelled[i] for i in candidates_of_statement(tuple(spelled), outputs, named))


def annotation_entries(annotation, address, declarations):
    """The marks (`node`, `doc`) and the printed tags of a line's annotation,
    in the order written: `id=value`, `!doc`, `!node`, any other tag."""
    marks, tags = [], []
    if annotation is None:
        return (), ()
    for entry in annotation.entries:
        if isinstance(entry, terms.KeyValue):
            tags.append(f"{entry.key}={entry.value}")
        elif isinstance(entry, terms.Tag):
            tags.append(str(entry.tag))
            if entry.tag == "!doc":
                marks.append(DOC)
        elif (
            isinstance(entry, terms.Typer)
            and isinstance(entry.typing, terms.Marked)
            and isinstance(entry.typing.kind, terms.Node)
        ):
            tags.append("!node")
            marks.append(NODE)
        else:
            raise declarations.error(
                "readable-form",
                address,
                (
                    "no construction rule reads an annotation entry written on this line; a "
                    "line's annotation carries `id=…`, `!doc`, `!node`, or a bare tag"
                ),
            )
    return tuple(marks), tuple(tags)


def mentions_after_aliases(expr, aliases, address, declarations):
    """The spellings an expression mentions once the block's earlier aliases
    are substituted, and whether it or a substituted alias names an
    operator."""
    mentions, seen = [], set()
    has_operator = False

    def visit(e):
        nonlocal has_operator
        if occurrence_paths(e, (), declarations=declarations, address=address):
            has_operator = True
        for spelling in free_names(e, address, declarations):
            if spelling not in mentions:
                mentions.append(spelling)
            if spelling in aliases and spelling not in seen:
                seen.add(spelling)
                visit(aliases[spelling])

    visit(expr)
    return mentions, has_operator


def perch_of_spelling(spelling, block_id, declarations, elsewhere=False) -> str | None:
    """The perch of a field a statement mentions: its mark; the decision perch
    for a control; the perch of the listing the block names it by when it is
    listed bare; None for an alias name, a parameter, or a function.

    A shock is at no perch: `_is_implicit` reads that as "no perch" (None),
    and `Declarations.check_known_at_perch`, which must say that a shock is
    drawn on an edge, reads it as the token `shck` (`elsewhere=True`).
    `elsewhere` also places a field the block does not list, at the perch the
    rest of the stage lists it, so that a refusal can say at which perch the
    field is; a stem listed at two perches is not placed this way."""
    stem, mark = spelling
    if mark is not None:
        return mark
    if declarations.field_roles.get(stem) == CONTROL:
        return DECISION
    if declarations.declared_as(stem) == "shock":
        # a shock a block lists and one it does not are both shocks
        return SHCK if elsewhere else None
    for listing in declarations.side_entries(block_id, INPUT) + declarations.side_entries(
        block_id, OUTPUT
    ):
        if listing.stem == stem and listing.mark is None and listing.wire_type:
            return listing.wire_type.perch
    if elsewhere:
        perches = {
            l.wire_type.perch for l in declarations.listings if l.stem == stem and l.wire_type
        }
        if len(perches) == 1:
            return next(iter(perches))
    return None


def listed_identity(spelling, listings, declarations) -> Identity | None:
    """The wire type a body reference names among the listings of one side
    of its block, or None when that side lists no such field. A field's
    identity is its wire type `<stage>:<perch>:<field>`, not a spelling: a
    marked name (`a[>]`, `V[<]`) is the field of its stem at the marked
    perch; a bare name is the control of its stem, at the decision perch
    wherever it is listed, the shock of its stem at no perch, or else the
    field the side lists under the bare name, whose perch is the side's
    perch word. So `a[>]` on a left side and `a` on the `: !cntn` output
    side of the header are one field, and `dV[>]` on a right side reads the
    input a `: !cntn` side lists as `dV`. (The decision mark `x[~]` lowers
    to the bare name, so a spelling carries the arrival or the continuation
    mark or none.)"""
    stem, mark = spelling
    role = declarations.field_roles.get(stem)
    if mark is not None:
        wanted = Identity("field", stage=declarations.stage, perch=mark, field=stem)
    elif role == CONTROL:
        wanted = Identity("field", stage=declarations.stage, perch=DECISION, field=stem)
    elif role == SHOCK:
        wanted = Identity("field", stage=declarations.stage, perch=SHCK, field=stem)
    else:
        wanted = next((l.wire_type for l in listings if l.stem == stem and l.mark is None), None)
    return next((l.wire_type for l in listings if l.wire_type == wanted), None)


def candidates_of_statement(mentioned, outputs, defined) -> tuple:
    """The candidates of a candidate statement: the fields it mentions that
    are outputs of its block, bare or under a perch mark, and that no
    operative statement of the block with a name on its left side defines.
    The order is the block's header, a marked field directly after the
    output it marks. The three arguments are identities: the fields the
    statement mentions, the block's declared outputs in header order, and
    the fields the block's name-sided statements define. The fold of the
    policy builder reads the same rule from its own context."""
    out = []
    for output in dict.fromkeys(outputs):
        marked = [i for i in mentioned if i.field == output.field and i != output]
        for identity in [output] + marked:
            if identity in mentioned and identity not in defined and identity not in out:
                out.append(identity)
    return tuple(out)


def forward_blocks_between(perch_from: str, perch_to: str, declarations) -> list | None:
    """The forward blocks from one perch to a later one — `arvl_to_dcsn` for
    arrival to decision, `dcsn_to_cntn` for decision to continuation, both
    in turn for arrival to continuation — in order. None when the second
    perch is not later than the first, or a block of the chain is absent
    from the stage."""
    start, end = PERCHES.index(perch_from), PERCHES.index(perch_to)
    if end <= start:
        return None
    chain = []
    for i in range(start, end):
        block = declarations.block_between(PERCHES[i], PERCHES[i + 1])
        if block is None:
            return None
        chain.append(block)
    return chain


def group_coordinates(subject, declarations, address):
    """The coordinates of a subject in order, each typed group over an
    explicit product read as its members, each member with its factor of the
    product and the classifiers the group shares."""
    for coordinate in subject.coordinates:
        if not isinstance(coordinate, terms.Group):
            yield coordinate
            continue
        members = tuple(group_coordinates(coordinate.inner, declarations, address))
        domains = [c for c in coordinate.classifiers if isinstance(c, terms.Domain)]
        shared = [c for c in coordinate.classifiers if not isinstance(c, terms.Domain)]
        product = domains[0].space if len(domains) == 1 else None
        if isinstance(product, terms.Named):
            product = declarations.space_terms.get(product.name, product)
        if domains and (
            not isinstance(product, terms.Product) or len(product.factors) != len(members)
        ):
            raise declarations.error(
                "readable-form",
                address,
                "a grouped declaration requires one explicit product factor per name; "
                "retain coupled feasible constraints on the choice binder",
                write=(
                    "Write one explicit product factor for each name, and retain coupled "
                    "feasible constraints on the choice binder"
                ),
            )
        for i, member in enumerate(members):
            classifiers = tuple(member.classifiers) + tuple(shared)
            if domains:
                classifiers += (terms.Domain(product.factors[i]),)
            yield dataclasses.replace(member, classifiers=classifiers)


def statement_id(annotation) -> str | None:
    """The id a line carries, `[id=cons_choice]`, or None when it carries
    none."""
    if annotation is None:
        return None
    for entry in annotation.entries:
        if isinstance(entry, terms.KeyValue) and entry.key == "id":
            return entry.value
    return None


def systems_by_shared_candidate(members) -> dict:
    """The systems of candidate statements of a block: `members` is the
    pairs (address, candidates) in file order; the statements that share a
    candidate, transitively, form one system, keyed by the address of its
    first statement and holding its addresses in file order and its
    candidates in the order first met. It is the one grouping that the
    construction's records (`construction._statement_records`), the occurrences
    of a constructed stage (`stage_names.occurrences_of`) and the fold
    (`fold.policy.candidate_systems`) read."""
    members = tuple(members)
    order = [address for address, _ in members]
    candidates_of = dict(members)
    systems = []
    for address, candidates in members:
        # sharing a candidate is transitive, so a statement that meets several
        # systems joins them into one
        met = [
            system
            for system in systems
            if set(candidates) & {c for member in system for c in candidates_of[member]}
        ]
        for system in met:
            systems.remove(system)
        systems.append(
            sorted([address, *(member for system in met for member in system)], key=order.index)
        )
    return {
        system[0]: (
            tuple(system),
            tuple(dict.fromkeys(c for member in system for c in candidates_of[member])),
        )
        for system in sorted(systems, key=lambda system: order.index(system[0]))
    }


def system_occurrence(names, clause) -> OperatorOccurrence:
    """The one `solve` occurrence of a system of candidate statements, which
    its first statement records: its unknowns the field names in the order
    of the block's header, spelled `c` or `(c, c_p)`; it seeks a constrained
    optimum where a statement of the system carries a clause and an interior
    root otherwise."""
    names = tuple(names)
    spelled = names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"
    return OperatorOccurrence(
        head="solve",
        subscripts=names,
        position=(),
        unknown=spelled,
        target=CONSTRAINED_OPTIMUM if clause else INTERIOR_ROOT,
    )


# --- the expressions of a bound ---


def bound_expressions(bound) -> tuple:
    """The expressions a bound relates: the two sides of a `Rel`, `a >= 0`,
    or the three terms of a `Between`, `0 <= c_p <= w_d`."""
    if isinstance(bound, terms.Between):
        return (bound.lower, bound.middle, bound.upper)
    return (bound.left, bound.right)


def is_number_alone(expression) -> bool:
    """Whether a side of a bound is a number or `inf` alone, with or without
    a minus sign."""
    if isinstance(expression, terms.Neg):
        expression = expression.operand
    return isinstance(expression, terms.Number) or expression == terms.Sym(terms.Constant("inf"))


# the relation sign of a bound read from its other side
_CONVERSE_SIGN = {terms.Le: terms.Ge, terms.Lt: terms.Gt, terms.Ge: terms.Le, terms.Gt: terms.Lt}


def converse_bound(bound):
    """A one-bound relation with its two sides exchanged and its sign
    turned, `0 <= a` as `a >= 0`, the spelling the refusal of a reversed
    bound names."""
    return terms.Rel(bound.right, _CONVERSE_SIGN[type(bound.op)](), bound.left)


def classifier_set(classifiers):
    for cl in classifiers:
        if isinstance(cl, terms.Domain):
            return cl.space
    return None


def named_sets(term) -> list:
    """The names of the sets a set term reads, each once, in the order
    written: a bare name, `Foo`; the factors of a product, `Xm × Foo`; the
    base of a comprehension, `{i : Foo | i >= 0}`; the superset of listed
    points, `{0, θ} ⊂ Foo`; the domain and the codomain of a set of
    functions; the members of a union, `Foo \\/ (0, 1)`; and the two sides of
    a difference. The endpoints of an interval and the members of a finite
    set are no sets, and a term that is no set term reads none."""
    found = []

    def visit(t):
        if isinstance(t, terms.Space):
            visit(t.set)
        elif isinstance(t, terms.Named):
            if t.name not in found:
                found.append(t.name)
        elif isinstance(t, terms.Product):
            for factor in t.factors:
                visit(factor)
        elif isinstance(t, terms.Comprehension):
            visit(t.base)
        elif isinstance(t, terms.Points):
            visit(t.superset)
        elif isinstance(t, terms.Functions):
            visit(t.domain)
            visit(t.codomain)
        elif isinstance(t, terms.SetUnion):
            for member in t.members:
                visit(member)
        elif isinstance(t, terms.SetDifference):
            visit(t.left)
            visit(t.right)

    visit(term)
    return found


def names_read_in_set(term, bound=(), heads=None) -> list:
    """The bare names a set term reads as numbers, each once, in the order
    written: a name in an endpoint of an interval, `(0, R)`, in a bound of a
    range, in a member of a listed set or in a condition of a comprehension.
    A name that the binder of a comprehension or a subscript of an operator
    binds is no read, and `inf` is a number word. `bound` holds the names
    bound where the term stands. The names of the sets the term reads are
    those of `named_sets`.

    `heads` holds the heads of the operators whose subscripts bind a name,
    and every operator's subscripts bind where it is None. With `("E",)` the
    subscript of an expectation alone binds, so the name a derivative is
    taken in, `D_{y}(y^2)`, is read."""
    found = []

    def visit(node, bound):
        if isinstance(node, terms.Sym):
            symbol = node.symbol
            if (
                isinstance(symbol, terms.Constant)
                and symbol.name != "inf"
                and symbol.name not in bound
                and symbol.name not in found
            ):
                found.append(symbol.name)
        elif isinstance(node, terms.Comprehension):
            visit(node.base, bound)
            binders = bound | {
                c.stem
                for c in getattr(node.bound, "coordinates", ())
                if isinstance(c, terms.Coordinate)
            }
            for condition in node.conds:
                visit(condition, binders)
        elif isinstance(node, terms.Operator):
            binds = heads is None or node.head in heads
            names = set(bound)
            for sub in node.subs:
                if isinstance(sub, terms.In):
                    # a binder is in scope in the sets of the binders after it
                    visit(sub.set, frozenset(names))
                    if binds:
                        names.add(sub.var)
                elif isinstance(sub, terms.Var) and binds:
                    names.add(sub.name)
            for argument in node.args:
                visit(argument, frozenset(names))
        else:
            for child in children(node):
                visit(child, bound)

    visit(term, frozenset(bound))
    return found


# --- small readers: spellings, coordinates, classifiers and positions ---


def spelling_text(spelling) -> str:
    stem, mark = spelling
    return stem + WRITTEN_MARK.get(mark, "")


def role_word(kind) -> str | None:
    """The role a role constructor names: "state", "control", "value" or
    "shock"; None for a constructor no word of the lowering's vocabulary
    produces, `Parameter` or a `Value` of an order above zero."""
    if isinstance(kind, terms.Control):
        return CONTROL
    if isinstance(kind, terms.Value):
        return VALUE_ROLES[kind.order] if kind.order in range(len(VALUE_ROLES)) else None
    if isinstance(kind, terms.Shock):
        return SHOCK
    if isinstance(kind, terms.State):
        return STATE
    return None


def coordinate_text(c) -> str:
    """A coordinate as written, `V[>]`, `c`, for messages. It never raises:
    a term whose mark is a form no construction rule reads is written bare
    here, and the refusal that names it says what is wrong with it."""
    if not isinstance(c, terms.Coordinate):
        try:
            return to_source(c)
        except NotImplementedError:
            return "a listing"
    mark = PERCH_OF_SIDE.get(type(c.at.side)) if isinstance(c.at, terms.At) else None
    return c.stem + WRITTEN_MARK.get(mark, "")


def classifier_text(cl) -> str:
    """A classifier written on a side as a message names it: a set by its
    spelling, a role word or a second perch word by its kind."""
    if isinstance(cl, terms.Domain):
        return f"the set {to_source(cl.space)}"
    if isinstance(cl, terms.Role):
        return "a role word"
    if isinstance(cl, terms.Infoset):
        return "a second perch word"
    return "a classifier no construction rule reads"


def span_of(address: str, spans):
    """The source span of one item, or None when the term was decoded from a
    saved AST and carries no positions. A table without an entry for the
    address does not describe this term, which is the caller's mistake and
    not a fault of the stage file."""
    if spans is None:
        return None
    try:
        return spans[address]
    except KeyError:
        raise ValueError(
            f"the span table has no entry for term address {address!r}; it "
            f"does not describe this term"
        ) from None


def position_text(address: str, spans) -> str:
    """`file:line:column (term address 'a')` when the span table is given,
    `term address 'a'` when it is None."""
    span = span_of(address, spans)
    if span is None:
        return f"term address {address!r}"
    return f"{span.file}:{span.line}:{span.column} (term address {address!r})"


def item_kind(item) -> str:
    """The constructor name of an item, with a statement's core: `Declare`,
    `Block`, `Statement(Assignment)`."""
    if isinstance(item, terms.Statement):
        return f"Statement({type(item.core).__name__})"
    return type(item).__name__
