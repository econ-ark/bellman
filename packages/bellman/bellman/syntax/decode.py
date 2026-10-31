"""The strict inverse of `to_json`: the JSON encoding of a parsed AST read back
into its term.

`from_json` reads an already-parsed JSON value — the encoding that
`bellman.syntax.lower.to_json` writes: a dataclass node is a mapping whose
"__class__" names the constructor and whose other keys are the constructor's
ASDL fields in ASDL order, an absent slot an explicit null; a sequence slot is
a JSON array element-wise; a primitive is itself — and returns the
`terms.FILE` it encodes. The constructors it admits are exactly the dataclasses
defined in `terms.py` (a registry built once at import); a
sort base such as `item`, a name imported into that module, or any other name
is rejected. A mapping's key set must equal the constructor's field set; a
sequence slot (annotated `tuple`) decodes only from a JSON array, and decodes
to a tuple, the children a term holds; a single or optional slot (annotated
`object`) decodes from a mapping, a primitive (str, int, float, bool) or null,
never from an array. Sorts are not checked: the
decoder inverts the encoding, it does not type the term. Every defect raises
`TermDecodeError`, a ValueError whose message gives the JSON path of the
offending value ("items[3].declaration.subject"; "the root" for the value
itself) and the defect. Nothing here evaluates a name from the data.
"""

from dataclasses import fields, is_dataclass
from typing import NamedTuple

from bellman.syntax import terms


class TermDecodeError(ValueError):
    """A JSON value that is not the `to_json` encoding of a generated term.
    The message names the JSON path of the offending value and the defect."""


_ROOT = "the root"


def from_json(data):
    """The `terms.FILE` that `data`, an already-parsed JSON value, encodes
    under `to_json`; `TermDecodeError` for anything else."""
    if not isinstance(data, dict):
        _fail(
            _ROOT,
            f"{_kind(data)} cannot encode a term; the encoding of a "
            f'term is a mapping whose "__class__" is "FILE"',
        )
    term = _decoded_term(data, _ROOT)
    if not isinstance(term, terms.FILE):
        _fail(
            _ROOT,
            f"the root encodes {type(term).__name__}; from_json "
            f"returns a FILE, so the root must encode FILE",
        )
    return term


def _decoded_term(mapping, path):
    """A mapping tagged "__class__": the constructor named must be in the
    registry, the other keys must be exactly its fields, and each field
    decodes by its slot category."""
    if "__class__" not in mapping:
        _fail(
            path,
            'the mapping has no "__class__" key; every encoded node '
            "names its generated constructor",
        )
    name = mapping["__class__"]
    if not isinstance(name, str):
        _fail(
            path, f'"__class__" must be a string naming a generated constructor, not {_kind(name)}'
        )
    entry = _REGISTRY.get(name)
    if entry is None:
        if name in _SORTS:
            _fail(path, f"{name!r} is a sort of bellman.syntax.terms, not a generated constructor")
        _fail(path, f"{name!r} is not a constructor generated in bellman.syntax.terms")
    cls, slots = entry.cls, entry.slots
    expected = [slot.name for slot in slots]
    missing = [field_name for field_name in expected if field_name not in mapping]
    unknown = [key for key in mapping if key != "__class__" and key not in expected]
    if missing or unknown:
        parts = []
        if missing:
            parts.append("missing: " + ", ".join(map(repr, missing)))
        if unknown:
            parts.append("unknown: " + ", ".join(map(repr, unknown)))
        _fail(path, f"the fields of {name} are {', '.join(expected)}; " + "; ".join(parts))
    args = {}
    for held in slots:
        field_name = held.name
        value = mapping[field_name]
        child = _child(path, field_name)
        slot = f"{name}.{field_name}"
        if held.is_sequence:
            if not isinstance(value, list):
                _fail(
                    child,
                    f"the sequence slot {slot} must decode from a JSON array, not {_kind(value)}",
                )
            args[field_name] = tuple(
                _value(item, f"{child}[{i}]", f"an element of {slot}")
                for i, item in enumerate(value)
            )
        else:
            args[field_name] = _value(value, child, f"the single slot {slot}")
    return cls(**args)


_PRIMITIVES = (str, int, float, bool)


def _value(value, path, slot):
    """One JSON value in a single slot or as an element of a sequence slot:
    a mapping is a node, a primitive or null is itself, an array is a
    defect (only a sequence slot decodes from an array)."""
    if isinstance(value, dict):
        return _decoded_term(value, path)
    if isinstance(value, list):
        _fail(
            path,
            f"{slot} cannot decode from a JSON array; only a sequence slot decodes from an array",
        )
    if value is None or isinstance(value, _PRIMITIVES):
        return value
    _fail(
        path, f"{_kind(value)} is not a JSON value; {slot} holds a mapping, a primitive, or null"
    )


def _fail(path, defect):
    raise TermDecodeError(f"at {path}: {defect}")


def _kind(value):
    """A JSON value described for an error message."""
    if isinstance(value, dict):
        return "a mapping"
    if isinstance(value, list):
        return "a JSON array"
    if value is None:
        return "null"
    return f"the {type(value).__name__} {value!r}"


def _child(path, name):
    return name if path == _ROOT else f"{path}.{name}"


def _generated(module):
    """The classes the generated module defines, split into the constructors
    — the dataclasses, each mapped to (class, slots) — and the sorts, the
    plain base classes. A class imported into the module belongs to
    neither, and a name that is not a class is ignored."""
    constructors, sorts = {}, set()
    for name, obj in vars(module).items():
        if not (isinstance(obj, type) and obj.__module__ == module.__name__):
            continue
        if name.startswith("_"):
            continue  # the sorts' metaclass, not a sort
        if is_dataclass(obj):
            constructors[name] = _Constructor(cls=obj, slots=_slots(obj))
        else:
            sorts.add(name)
    return constructors, sorts


def _slots(cls):
    """The (ASDL field name, is a sequence slot) pairs of a generated
    constructor, in ASDL order. gen_types.py annotates a sequence slot
    `tuple` and every other slot `object`; any other annotation is a change
    to the generator this decoder does not know how to read."""
    out = []
    for f in fields(cls):
        if f.type is tuple:
            out.append(_Slot(name=f.name, is_sequence=True))
        elif f.type is object:
            out.append(_Slot(name=f.name, is_sequence=False))
        else:
            raise TypeError(
                f"{cls.__name__}.{f.name} is annotated {f.type!r}; the "
                f"generated module annotates a sequence slot tuple and every "
                f"other slot object"
            )
    return tuple(out)


class _Slot(NamedTuple):
    """One ASDL field of a generated constructor and whether it is a
    sequence slot."""

    name: str
    is_sequence: bool


class _Constructor(NamedTuple):
    """A generated constructor: its class and its slots in ASDL order."""

    cls: type
    slots: tuple


_REGISTRY, _SORTS = _generated(terms)
