"""The walk over a term or a record: the values directly inside a value, and
every value inside it, depth first.

A term of the parsed AST, a typed expression and a stored record are frozen
dataclasses whose fields hold other terms, tuples of them or frozensets of
them. A function that visits every part of such a value reads the parts here,
so that the traversal is written once.
"""

from __future__ import annotations

import dataclasses


def children(value):
    """The values directly inside `value`, in order: the fields of a dataclass
    instance in the order its class declares them, the items of a tuple or a
    list, or the members of a frozenset in its iteration order. Any other
    value, a string among them, has none."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return tuple(getattr(value, field.name) for field in dataclasses.fields(value))
    if isinstance(value, (tuple, list, frozenset)):
        return tuple(value)
    return ()


def nodes(value):
    """`value` and every value inside it, depth first: `value`, then the nodes
    of each of its children in order."""
    yield value
    for child in children(value):
        yield from nodes(child)
