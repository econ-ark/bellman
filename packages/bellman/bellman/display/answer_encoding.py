"""A detached mathematical answer written as JSON data, with no display text
(`encode_answer`).

Each node of the data carries the kind of the schema `stage-encoding/2.6`
under which it is written, `records.Wire`, `terms.Sym`, read from `KINDS`,
the one table from the classes the encoder writes to those kinds. A kind is
spelled `<namespace>.<Kind>` in one of the schema's five namespaces, `terms`,
`semantic`, `records`, `predicates` and `methods`; a namespace is a name of
the schema and names no module of the package, so that a class may be moved
or renamed while the documents already written stay as written.
"""

from __future__ import annotations

import json
import math
from collections import namedtuple
from collections.abc import Mapping
from dataclasses import fields, is_dataclass

from bellman.display import cards as C
from bellman.native import predicates as P
from bellman.native import records as R
from bellman.native.identity import Identity
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import PRIMITIVE_SETS
from bellman.typing import typed_expressions as S
from bellman.typing.line_unknowns import OPERATOR_VOCABULARY
from bellman.typing.primitive_definitions import primitive_definition

# --- the encoding of one answer ---


def encode_answer(answer):
    """One detached answer as JSON data: `value`, the answer with each bound
    variable written by the depth of its scope and its position there, not by
    its name; and `identities`, the fields of every document identity the
    value refers to, in the order of the identities' text. A free name no
    retained definition answers is written as unresolved, with its reason.
    Nothing is stored on the answer or on a stage."""
    tables = _EncodingTables(aliases=_aliases_by_field(answer), identities={})
    value = _encode(answer, (), tables)
    return {
        "identities": [
            {"id": key, "fields": tables.identities[key]} for key in sorted(tables.identities)
        ],
        "value": value,
    }


# The two tables one encoding reads and writes: the identities each field
# name of the answer stands for, and the fields of each document identity the
# encoding refers to, by the identity's text, written when it is first met.
_EncodingTables = namedtuple("_EncodingTables", "aliases identities")


def _aliases_by_field(answer):
    """The identities each field name stands for, read from every denoted
    object reached from the answer through its wires, pieces, records,
    mappings and sequences."""
    aliases = {}
    pending = [answer]
    seen = set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if isinstance(item, C.Denoted) and isinstance(item.identity, Identity):
            if item.identity.field is not None:
                aliases.setdefault(item.identity.field, set()).add(item.identity)
        if isinstance(item, C.Wire):
            pending.extend(
                (
                    item.mathematical_type,
                    item.expression,
                    item.definition,
                    item.rules,
                    item.residuals,
                )
            )
        elif isinstance(item, C.Piece):
            pending.append(item.record)
        elif is_dataclass(item) and not isinstance(item, (type, Identity)):
            pending.extend(getattr(item, f.name) for f in fields(item))
        elif isinstance(item, Mapping):
            pending.extend(item.values())
        elif isinstance(item, (tuple, list, frozenset)):
            pending.extend(item)
    return aliases


def _encode(value, frames, tables):
    """One value as JSON data: an identity by its reference, a record, a term
    or a typed expression as a node of its kind, a scoped term with its bound
    variables by depth and position, and a mapping, a sequence, a set or a
    number in the forms the schema gives them. `frames` holds the variables
    of each enclosing scope, the innermost last."""
    if isinstance(value, Identity):
        return _reference(value, frames, tables)
    if isinstance(value, C.Wire):
        return _node(
            value,
            {
                "identity": _reference(value.identity, frames, tables),
                "mathematical_type": _encode(value.mathematical_type, frames, tables),
                "note": value.note,
                "expression": _encode(value.expression, frames, tables),
                "definition": _encode(value.definition, frames, tables),
                "controls": _encode(value.controls, frames, tables),
                "rules": _encode(value.rules, frames, tables),
                "residuals": _encode(value.residuals, frames, tables),
            },
        )
    if isinstance(value, C.Piece):
        return _node(
            value,
            {
                "key": _encode(value.key, frames, tables),
                "name": value.name,
                "record": _encode(value.record, frames, tables),
            },
        )
    if isinstance(value, C.Textual):
        return {"textual": value.text}
    if isinstance(value, S.Unresolved):
        return {
            "ref": "unresolved",
            "target": _encode(value.identity, frames, tables),
            "reason": value.missing,
        }
    if isinstance(value, T.Operator) and not _binds_its_subscripts(value):
        return _encode_unscoped_operator(value, frames, tables)
    scope = (
        (value.params, (value.name,), (value.body,))
        if isinstance(value, (T.FuncDef, T.CorrDef))
        else S.binder_parts(value)
    )
    if scope is not None:
        return _encode_scope(value, scope, frames, tables)
    if isinstance(
        value,
        (
            R.ResolvedName,
            T.Constant,
            T.Named,
            T.Variable,
            T.Var,
            T.In,
            T.TimeValue,
            T.Call,
            T.Coordinate,
            R.ExpressionType,
        ),
    ):
        key = (
            "identity"
            if isinstance(value, R.ResolvedName)
            else "fun"
            if isinstance(value, T.Call)
            else "var"
            if isinstance(value, T.In)
            else "stem"
            if isinstance(value, T.Coordinate)
            else "domain"
            if isinstance(value, R.ExpressionType)
            else "name"
        )
        return _node(
            value,
            {
                f.name: (
                    _reference(getattr(value, f.name), frames, tables)
                    if f.name == key
                    and getattr(value, f.name) is not None
                    and isinstance(getattr(value, f.name), (str, Identity))
                    else _encode(getattr(value, f.name), frames, tables)
                )
                for f in fields(value)
            },
        )
    if isinstance(value, S.WireType):
        return _node(
            value,
            {
                "sort": _encode(value.sort, frames, tables),
                "carrier": _encode(value.carrier, frames, tables),
                "declarations": [
                    [_reference(name, frames, tables), _encode(carrier, frames, tables)]
                    for name, carrier in value.declarations
                ],
            },
        )
    if isinstance(value, R.Condition):
        entries = {f.name: _encode(getattr(value, f.name), frames, tables) for f in fields(value)}
        entries.update(
            named_identities=_encode(value.named_identities, frames, tables),
            predicate=(
                _encode(value.predicate, frames, tables)
                if value.predicate is not None
                else {"textual": value.explanation or value.condition}
            ),
            purpose=value.purpose,
            family=value.family,
            evidence=[{"textual": text} for text in value.evidence],
        )
        return _node(value, entries)
    if isinstance(value, C.OperatorCard):
        return _node(
            value,
            {
                f.name: (
                    {"textual": value.affine}
                    if f.name == "affine"
                    else _encode(getattr(value, f.name), frames, tables)
                )
                for f in fields(value)
            },
        )
    if is_dataclass(value) and not isinstance(value, type):
        return _node(
            value, {f.name: _encode(getattr(value, f.name), frames, tables) for f in fields(value)}
        )
    if isinstance(value, Mapping):
        return {
            "mapping": [
                [_encode(k, frames, tables), _encode(v, frames, tables)] for k, v in value.items()
            ]
        }
    if isinstance(value, (tuple, list)):
        return [_encode(v, frames, tables) for v in value]
    if isinstance(value, frozenset):
        return {
            "set": sorted(
                (_encode(v, frames, tables) for v in value),
                key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False),
            )
        }
    if isinstance(value, float) and not math.isfinite(value):
        return {"float": str(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"no mathematical encoding for a {type(value).__name__}")


def _node(value, entries):
    """A node of the kind of `value`, with its fields."""
    return {"node": schema_kind(value), "fields": entries}


def _binds_its_subscripts(operator):
    """Whether an operator's subscripts are variables it binds, which the
    encoding writes as a scope: `forall` and `exists`, and an `argmax` or a
    `solve` over explicit domains, whose every subscript is `x ∈ X`."""
    explicit_choice = operator.head in ("argmax", "solve") and all(
        isinstance(sub, T.In) for sub in operator.subs
    )
    return operator.head in ("forall", "exists") or explicit_choice


def _encode_unscoped_operator(value, frames, tables):
    """An operator whose subscripts select declared names: its head, each
    subscript with the name it selects as a reference read outside every
    scope, and its arguments."""
    subscripts = []
    for sub in value.subs:
        key = "name" if isinstance(sub, T.Var) else "var"
        subscripts.append(
            _node(
                sub,
                {
                    f.name: (
                        _reference(getattr(sub, f.name), (), tables)
                        if f.name == key and isinstance(getattr(sub, f.name), (str, Identity))
                        else _encode(getattr(sub, f.name), (), tables)
                        if f.name == key
                        else _encode(getattr(sub, f.name), frames, tables)
                    )
                    for f in fields(sub)
                },
            )
        )
    return _node(
        value,
        {
            "head": _reference(value.head, frames, tables),
            "subs": subscripts,
            "args": _encode(value.args, frames, tables),
        },
    )


def _encode_scope(value, scope, frames, tables):
    """A term that binds variables, from its `scope`, the variables, the
    terms outside the scope and the bodies inside it: the metadata of each
    variable, the outside terms (an operator's domains each in the scope of
    the variables bound before it), the bodies in the scope of all of them,
    and the shape the bound variables form."""
    variables, outside, bodies = scope
    inner = frames + (tuple(S.variable_identity(v) for v in variables),)
    outer = [_encode(v, frames, tables) for v in outside]
    metadata = [_encode(S.variable_metadata(v), frames, tables) for v in variables]
    if isinstance(value, (T.Operator, T.FuncDef, T.CorrDef)):
        outer[0] = _reference(outside[0], frames, tables)
    if isinstance(value, T.Operator):
        for index, variable in enumerate(variables):
            preceding = frames + (inner[-1][:index],)
            outer[index + 1] = _encode(outside[index + 1], preceding, tables)
            metadata[index] = _encode(S.variable_metadata(variable), preceding, tables)
    structure = (
        _bound_pattern(value.bound, inner, tables)
        if isinstance(value, T.Comprehension)
        else [schema_kind(s) for s in value.subs]
        if isinstance(value, T.Operator)
        else []
    )
    return {
        "node": schema_kind(value),
        "bindings": metadata,
        "outside": outer,
        "body": [_encode(v, inner, tables) for v in bodies],
        "shape": structure,
    }


# --- the references and the bound variables ---


# the names a reference writes as primitive: the primitive sets and their
# domains, the operators of a line, the extended reals and the booleans, and
# `product`, `forall`, `exists` and `inf`
_PRIMITIVE_NAMES = (
    set(PRIMITIVE_SETS)
    | set(OPERATOR_VOCABULARY)
    | {p.domain for p in PRIMITIVE_SETS.values() if p.domain is not None}
    | {"primitive:extended-real", "primitive:boolean", "product", "forall", "exists", "inf"}
)


def _reference(value, frames, tables):
    """A reference to what a name stands for: a variable bound by an enclosing
    scope by its depth and position, a document identity, a field name that
    stands for one identity, a primitive name, or an unresolved name with its
    reason."""
    name = S.variable_identity(value)
    for depth, frame in enumerate(reversed(frames)):
        for position, variable in enumerate(frame):
            if name == variable:
                return {"ref": "bound", "depth": depth, "position": position}
    if isinstance(name, Identity):
        return _identity_entry(name, tables)
    choices = tables.aliases.get(name, ()) if isinstance(name, str) else ()
    if len(choices) == 1:
        return _identity_entry(next(iter(choices)), tables)
    if isinstance(name, str) and (
        name in _PRIMITIVE_NAMES or primitive_definition(name) is not None
    ):
        return {"ref": "primitive", "name": name}
    return {
        "ref": "unresolved",
        "target": _encode(name, (), tables),
        "reason": "ambiguous declaration" if choices else "definition not retained",
    }


def _identity_entry(identity, tables):
    """The reference to a document identity; its fields are written into the
    table of identities when it is first met, the entry held empty while they
    are written, so that an identity whose fields refer to it is written
    once."""
    key = str(identity)
    if key not in tables.identities:
        tables.identities[key] = None
        tables.identities[key] = {
            f.name: _encode(getattr(identity, f.name), (), tables) for f in fields(identity)
        }
    return {"ref": "document", "id": key}


def _bound_pattern(value, frames, tables):
    """The pattern the variables a comprehension binds form, `(x, y)` or a
    group, each variable by its reference and each part written outside the
    pattern (a classifier, a coordinate's annotation) read from outside the
    innermost scope."""
    if isinstance(value, (T.Tuple, T.Subject)):
        key = "items" if isinstance(value, T.Tuple) else "coordinates"
        return _node(
            value, {key: [_bound_pattern(v, frames, tables) for v in getattr(value, key)]}
        )
    if isinstance(value, T.Group):
        return _node(
            value,
            {
                "inner": _bound_pattern(value.inner, frames, tables),
                "classifiers": _encode_outside(value.classifiers, frames, tables),
            },
        )
    if isinstance(value, (T.Coordinate, T.Sym, T.Constant)):
        key = (
            "stem"
            if isinstance(value, T.Coordinate)
            else "symbol"
            if isinstance(value, T.Sym)
            else "name"
        )
        return _node(
            value,
            {
                f.name: (
                    _bound_pattern(getattr(value, f.name), frames, tables)
                    if f.name == key
                    else _encode_outside(getattr(value, f.name), frames, tables)
                )
                for f in fields(value)
            },
        )
    if isinstance(value, R.ResolvedName):
        return _node(
            value,
            {
                f.name: (
                    _reference(value.identity, frames, tables)
                    if f.name == "identity"
                    else _encode_outside(getattr(value, f.name), frames, tables)
                )
                for f in fields(value)
            },
        )
    return _reference(value, frames, tables)


def _encode_outside(item, frames, tables):
    """A part of a bound pattern encoded outside the innermost scope, its
    references to bound variables then read from inside that scope."""
    return _shift_bound_depths(_encode(item, frames[:-1], tables))


def _shift_bound_depths(tree, local=0):
    """`tree` with each reference to a variable bound outside it, at a depth
    of `local` or more, one scope deeper; the scopes inside `tree` count in
    `local`, an operator's domains each in the scope of the variables bound
    before it."""
    if isinstance(tree, list):
        return [_shift_bound_depths(v, local) for v in tree]
    if isinstance(tree, dict):
        if tree.get("ref") == "bound":
            return dict(tree, depth=tree["depth"] + (tree["depth"] >= local))
        scoped = "bindings" in tree
        if scoped and tree.get("node") == "terms.Operator":
            return {
                k: (
                    [
                        _shift_bound_depths(item, local + (index > 0))
                        for index, item in enumerate(v)
                    ]
                    if k == "outside"
                    else _shift_bound_depths(v, local + (k in ("bindings", "body", "shape")))
                )
                for k, v in tree.items()
            }
        return {
            k: _shift_bound_depths(v, local + (scoped and k in ("body", "shape")))
            for k, v in tree.items()
        }
    return tree


# --- the kinds of the schema ---


# The kind of the schema under which each class is written as a node, by
# namespace: `terms`, the constructors of the base grammar
# (`syntax/grammars/*.asdl`); `semantic`, the typed expressions; `records`,
# the stored records of a stage version and the records a denotation answers;
# `predicates`, the seven forms of a condition; `methods`, a method's typed
# option. The schema's `x-constructors` lists the same kinds with their
# fields, and `x-namespaces` states what each namespace holds.
KINDS = {
    # terms
    T.Add: "terms.Add",
    T.Annotation: "terms.Annotation",
    T.Arrival: "terms.Arrival",
    T.Assignment: "terms.Assignment",
    T.At: "terms.At",
    T.Between: "terms.Between",
    T.Block: "terms.Block",
    T.Call: "terms.Call",
    T.Closed: "terms.Closed",
    T.Complementary: "terms.Complementary",
    T.Comprehension: "terms.Comprehension",
    T.Constant: "terms.Constant",
    T.Continuation: "terms.Continuation",
    T.Control: "terms.Control",
    T.Coordinate: "terms.Coordinate",
    T.CorrDef: "terms.CorrDef",
    T.Decision: "terms.Decision",
    T.Declaration: "terms.Declaration",
    T.Declare: "terms.Declare",
    T.Div: "terms.Div",
    T.Domain: "terms.Domain",
    T.Eq: "terms.Eq",
    T.Equation: "terms.Equation",
    T.FILE: "terms.FILE",
    T.FiniteSet: "terms.FiniteSet",
    T.FuncDef: "terms.FuncDef",
    T.Functions: "terms.Functions",
    T.Ge: "terms.Ge",
    T.Group: "terms.Group",
    T.Gt: "terms.Gt",
    T.In: "terms.In",
    T.Inequality: "terms.Inequality",
    T.Infoset: "terms.Infoset",
    T.IntegerRange: "terms.IntegerRange",
    T.Interval: "terms.Interval",
    T.Key: "terms.Key",
    T.KeyValue: "terms.KeyValue",
    T.Law: "terms.Law",
    T.Le: "terms.Le",
    T.Lt: "terms.Lt",
    T.Marked: "terms.Marked",
    T.Metadata: "terms.Metadata",
    T.Mul: "terms.Mul",
    T.Named: "terms.Named",
    T.Neg: "terms.Neg",
    T.Node: "terms.Node",
    T.Number: "terms.Number",
    T.Open: "terms.Open",
    T.Operator: "terms.Operator",
    T.Parameter: "terms.Parameter",
    T.PathAssignment: "terms.PathAssignment",
    T.Pos: "terms.Pos",
    T.Points: "terms.Points",
    T.Pow: "terms.Pow",
    T.Product: "terms.Product",
    T.Range: "terms.Range",
    T.Rel: "terms.Rel",
    T.Residual: "terms.Residual",
    T.Role: "terms.Role",
    T.Select: "terms.Select",
    T.Shock: "terms.Shock",
    T.Signature: "terms.Signature",
    T.Slack: "terms.Slack",
    T.Space: "terms.Space",
    T.State: "terms.State",
    T.Statement: "terms.Statement",
    T.SteadyState: "terms.SteadyState",
    T.Sub: "terms.Sub",
    T.Subject: "terms.Subject",
    T.Sym: "terms.Sym",
    T.T: "terms.T",
    T.Tag: "terms.Tag",
    T.TimeValue: "terms.TimeValue",
    T.Tuple: "terms.Tuple",
    T.Typer: "terms.Typer",
    T.Value: "terms.Value",
    T.Var: "terms.Var",
    T.Variable: "terms.Variable",
    # semantic
    S.Apply: "semantic.Apply",
    S.Compose: "semantic.Compose",
    S.FiniteMeasureSet: "semantic.FiniteMeasureSet",
    S.FunctionSet: "semantic.FunctionSet",
    S.Integral: "semantic.Integral",
    S.StochasticKernelSet: "semantic.StochasticKernelSet",
    S.Lambda: "semantic.Lambda",
    S.MeasurableMapSet: "semantic.MeasurableMapSet",
    S.Measure: "semantic.Measure",
    S.PowerSet: "semantic.PowerSet",
    S.ProbabilityMeasureSet: "semantic.ProbabilityMeasureSet",
    S.ProductMeasure: "semantic.ProductMeasure",
    S.Sup: "semantic.Sup",
    S.Unresolved: "semantic.Unresolved",
    # records
    R.ArithmeticHead: "records.ArithmeticHead",
    C.AuthoredCard: "records.AuthoredCard",
    R.Bindings: "records.Bindings",
    R.BlockData: "records.BlockData",
    R.BlockHeader: "records.BlockHeader",
    R.ValueRepresentation: "records.ValueRepresentation",
    R.Builders: "records.Builders",
    R.CategoryCodes: "records.CategoryCodes",
    C.Composite: "records.Composite",
    C.Declared: "records.Declared",
    R.Definition: "records.Definition",
    C.DefinitionCard: "records.DefinitionCard",
    C.Denoted: "records.Denoted",
    C.BlockDenoted: "records.BlockDenoted",
    C.Hypothesis: "records.Hypothesis",
    R.InitialDiagrams: "records.InitialDiagrams",
    C.KernelClause: "records.KernelClause",
    R.Line: "records.Line",
    R.Metadata: "records.Metadata",
    R.Method: "records.Method",
    C.MethodClause: "records.MethodClause",
    C.BlockMethodClause: "records.BlockMethodClause",
    C.ImageByName: "records.ImageByName",
    R.NodeData: "records.NodeData",
    C.OperatorCard: "records.OperatorCard",
    R.OperatorOccurrence: "records.OperatorOccurrence",
    C.Piece: "records.Piece",
    C.ImageAtPoint: "records.ImageAtPoint",
    R.Provenance: "records.Provenance",
    R.Refusal: "records.Refusal",
    R.ResolvedName: "records.ResolvedName",
    C.Rule: "records.Rule",
    R.Condition: "records.Condition",
    R.ExpressionType: "records.ExpressionType",
    S.WireType: "records.WireType",
    R.Semgraph: "records.Semgraph",
    C.ImageSet: "records.ImageSet",
    C.StageDenotation: "records.StageDenotation",
    C.Statement: "records.Statement",
    C.Textual: "records.Textual",
    C.TitleBlock: "records.TitleBlock",
    R.UndeclaredSet: "records.UndeclaredSet",
    C.Wire: "records.Wire",
    # predicates
    P.And: "predicates.And",
    P.Compare: "predicates.Compare",
    P.Complementarity: "predicates.Complementarity",
    P.IsInteger: "predicates.IsInteger",
    P.Member: "predicates.Member",
    P.Not: "predicates.Not",
    P.Or: "predicates.Or",
    # methods
    R.MethodOption: "methods.MethodOption",
}


def schema_kind(value):
    """The kind of the schema under which `value` is written as a node, from
    `KINDS`; a value of a class the schema lists no kind for is refused."""
    try:
        return KINDS[type(value)]
    except KeyError:
        raise TypeError(
            f"the stage encoding's schema lists no kind for a {type(value).__name__}"
        ) from None
