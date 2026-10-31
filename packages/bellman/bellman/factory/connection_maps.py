"""The pure transport along a certified route (AMD-COMP-001 §5): the
coordinate permutation a route's selected pairs give, applied to a point,
to the atoms of a finite measure, to the components of a derivative and to
both indices of a Hessian, and the pullback of a function.

A certified `Route` of `bellman.factory.connections` holds the ordered
continuation state tuple of its source branch, `source_fields`, the
ordered arrival state tuple of its destination, `destination_fields`, and
the `permutation` its pairs give: `permutation[i]` is the index in
`source_fields` of the source coordinate whose image is destination index
`i`, and `inverse[j]` the destination index that is the image of source
coordinate `j`.
For the crossed pair `{S.a: T.b, S.b: T.a}` the permutation is `(1, 0)`
and sends `(a, b)` to `(b, a)`.

Two directions are kept apart. A point and the atoms of a measure are
transported forward, from the source's order to the destination's: the
pushforward of a finite measure given by atoms is the atoms at their
images, each with its mass, the masses of atoms that land on one tuple
summed. A function on the destination's tuple is pulled back to the
source's by composition with the map, `(P*v)(x) = v(P x)`, and the
pullback of a composition of two routes is the composition of the
pullbacks in reverse order. The components of a derivative the
destination supplies, a gradient in the destination's order, and both
indices of an authored Hessian are transported to the source's order by the
inverse: `(P*v)` has the partial derivative in source coordinate `j` that
`v` has in destination coordinate `inverse[j]`, and the second derivative
in `(j, k)` that `v` has in `(inverse[j], inverse[k])`. For the swap the
authored Hessian `[[2, 1], [1, 4]]` becomes `[[4, 1], [1, 2]]`.

These operations create no choice, law of motion, derivative or solver:
they reorder what is given. A route that is not certified, a tuple of
another length than the route's and an atom without a number for its
mass are refused with a ValueError naming the obligation, so that a
partial tuple, an unspecified joint law or an uncertified route uses none
of them.
"""

from __future__ import annotations

import math
from numbers import Integral, Real

__all__ = [
    "pull_back",
    "transport_atoms",
    "transport_hessian",
    "transport_point",
    "transport_vector",
]


def transport_point(route, point):
    """The point `point`, a tuple in the order of the route's source
    coordinates, in the order of its destination coordinates."""
    _certified(route)
    point = _tuple(point, route.source_fields, "a point")
    return tuple(point[j] for j in route.permutation)


def transport_atoms(route, atoms):
    """The atoms of a finite measure on the route's source tuple, each
    `(point, mass)`, transported to the destination tuple: `((point,
    mass), …)` in order of first image, the masses of atoms with one image
    summed and every mass preserved. A nonfinite input or an accumulated
    mass that overflows its numerical representation is refused."""
    _certified(route)
    landed = {}
    for atom in atoms:
        try:
            point, mass = atom
        except (TypeError, ValueError):
            raise ValueError(f"an atom is a pair (point, mass); got {atom!r}") from None
        if (
            not isinstance(mass, Real)
            or isinstance(mass, bool)
            or not 0 <= mass < math.inf
        ):
            raise ValueError(f"the mass of an atom is a finite nonnegative number; got {mass!r}")
        if isinstance(mass, Integral):
            mass = int(mass)
        target = transport_point(route, point)
        try:
            total = landed.get(target, 0) + mass
        except OverflowError:
            raise ValueError(f"the accumulated mass at {target!r} is not representable as a finite number") from None
        if not 0 <= total < math.inf:
            raise ValueError(f"the accumulated mass at {target!r} is not a finite nonnegative number")
        landed[target] = total
    return tuple(landed.items())


def transport_vector(route, components):
    """The components of a derivative the destination supplies, in the
    order of the route's destination coordinates, in the order of its
    source coordinates: component `j` of the answer is the component the
    destination has in the coordinate that is the image of source
    coordinate `j`."""
    _certified(route)
    components = _tuple(components, route.destination_fields, "a vector of components")
    return tuple(components[i] for i in route.inverse)


def transport_hessian(route, matrix):
    """An authored Hessian in the destination's order, rows and columns
    alike, in the source's order: entry `(j, k)` of the answer is the
    destination's entry at the two coordinates `j` and `k` land at."""
    _certified(route)
    n = len(route.destination_fields)
    rows = _tuple(matrix, route.destination_fields, "a Hessian's rows")
    rows = tuple(_tuple(row, route.destination_fields, "a Hessian's row") for row in rows)
    return tuple(
        tuple(rows[route.inverse[j]][route.inverse[k]] for k in range(n)) for j in range(n)
    )


def pull_back(route, function):
    """The pullback of `function`, a function of the destination's
    coordinates in their order, to the source's coordinates: the function
    that answers `function` at the transported point."""
    _certified(route)

    def pulled(*point):
        return function(*transport_point(route, point))

    return pulled


def _certified(route):
    """Refuses a route that is not certified, naming its obligations."""
    if route.status != "certified":
        raise ValueError(
            f"the route {route.source} → {route.destination} is not certified, so nothing is "
            "transported along it: " + "; ".join(route.obligations)
        )


def _tuple(values, fields, what):
    """`values` as a tuple of the length of `fields`; a tuple of another
    length is a partial tuple and is refused."""
    try:
        values = tuple(values)
    except TypeError:
        raise ValueError(f"{what} is a tuple of {len(fields)} values; got {values!r}") from None
    if len(values) != len(fields):
        raise ValueError(
            f"{what} on ({', '.join(fields)}) has {len(fields)} entries; {len(values)} given"
        )
    return values
