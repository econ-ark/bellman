"""The read-only copy of an annotation value, at every depth, and the test of
one.

A stage's annotations, its metadata, its provenance, its calibration and
settings and the diagnostics a record carries, hold plain Python values, and
a version holds only values that cannot change after it is built. `freeze`
makes such a copy, `is_frozen` decides whether a value is one, and
`check_frozen_mapping` refuses an attribute of the stage that is not one.
A `discopy.frobenius.Hypergraph` is refused in every position, so that no
graph is held in an annotation.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from discopy.frobenius import Hypergraph

from bellman.native.hypergraphs import is_frozen_native, is_frozen_record

# The values an annotation may hold as they are: immutable scalars.
_SCALARS = (str, bytes, int, float, bool, type(None))


def freeze(value):
    """A read-only copy of an annotation value, at every depth.

    A mapping becomes a `MappingProxyType` over a new dict of frozen values;
    a list or a tuple becomes a tuple of frozen values; a set or a frozenset
    becomes a frozenset of frozen values; a str, bytes, int, float, bool or
    None is itself; an instance of a frozen dataclass is itself once each of
    its fields is found frozen. Any other value, such as a generated term (a
    dataclass that is not frozen), a Lark tree, a YAML node or an arbitrary
    object, is refused with `TypeError`. The copy shares no mapping, sequence
    or set with its source. A mapping key is kept as it is: it is refused
    only where it is a graph or holds one in a mapping, a sequence, a set or
    a frozen record, and a key of another type is not inspected.

    A `discopy.frobenius.Hypergraph` is refused in every position: as the
    value, as a mapping value, as an item of a sequence and as a field of a
    frozen dataclass. A block's record holds no graph, since a builder's
    interior is its `NodeData` records (`records.BlockData.nodes`). Such a
    record is held only in `Box.data`, which no step of the construction
    passes through `freeze`, and an annotation holds no DisCoPy object.
    """
    if isinstance(value, _SCALARS):
        return value
    if isinstance(value, Mapping):
        if any(_key_contains_graph(key) for key in value):
            raise TypeError("a Hypergraph cannot be an annotation mapping key or part of one")
        return MappingProxyType({key: freeze(v) for key, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(v) for v in value)
    if is_frozen_record(value):
        for f in dataclasses.fields(value):
            field_value = getattr(value, f.name)
            if not is_frozen(field_value):
                raise TypeError(
                    f"{type(value).__name__}.{f.name} holds a "
                    f"{type(field_value).__name__}, which is not read-only; a "
                    f"frozen dataclass in an annotation must hold frozen values"
                )
        return value
    raise TypeError(
        f"a {type(value).__name__} cannot be an annotation value; admitted are "
        f"mappings, lists, tuples, sets, str, bytes, int, float, bool, None, and "
        f"frozen dataclasses whose fields are frozen"
    )


def is_frozen(value) -> bool:
    """Whether `value` is in the read-only form `freeze` makes: a scalar; a
    `MappingProxyType`, a tuple or a frozenset of frozen values; a frozen
    dataclass whose fields are frozen; or a DisCoPy object that
    `hypergraphs.freeze_native` froze, such as the `Sort` of a wire of a
    stored graph. A `discopy.frobenius.Hypergraph` is frozen in no position,
    a field of a frozen dataclass included."""
    if isinstance(value, _SCALARS):
        return True
    if not isinstance(value, Hypergraph) and is_frozen_native(value):
        return True
    if isinstance(value, MappingProxyType):
        return all(not _key_contains_graph(key) and is_frozen(v) for key, v in value.items())
    if isinstance(value, (tuple, frozenset)):
        return all(is_frozen(v) for v in value)
    if is_frozen_record(value):
        return all(is_frozen(getattr(value, f.name)) for f in dataclasses.fields(value))
    return False


def check_frozen_mapping(attribute: str, value) -> None:
    """Refuses, with `TypeError`, a value of the attribute `attribute` of
    `ElaboratedStage` that is not a `MappingProxyType` of frozen values."""
    if not isinstance(value, MappingProxyType):
        raise TypeError(
            f"ElaboratedStage.{attribute} must be a read-only mapping produced by "
            f"freeze (types.MappingProxyType); got {type(value).__name__}"
        )
    if not is_frozen(value):
        raise TypeError(
            f"ElaboratedStage.{attribute} holds a value that is not read-only; pass "
            f"the mapping through freeze"
        )


def _key_contains_graph(value, seen=None):
    """Whether a mapping key is a graph or holds one in a mapping, a sequence,
    a set or a frozen record; an object of another type is not inspected."""
    if isinstance(value, Hypergraph):
        return True
    seen = set() if seen is None else seen
    if id(value) in seen:
        return False
    seen.add(id(value))
    if isinstance(value, Mapping):
        return any(
            _key_contains_graph(k, seen) or _key_contains_graph(v, seen) for k, v in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_key_contains_graph(item, seen) for item in value)
    if is_frozen_record(value):
        return any(
            _key_contains_graph(getattr(value, field.name), seen)
            for field in dataclasses.fields(value)
        )
    return False
