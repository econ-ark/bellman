"""One period's forward map on measures, computed from a forward record.

A forward record is the plain record ``bellman.period.forward_record``
answers: for each forward builder of a period, the states it reads, the
shocks it draws, the controls it reads and its law of motion as a function,
then the joins within the period and the inter-period mapping.  This module
reads the record by its attributes and imports nothing of ``bellman``.

The record states what a numerical step needs; the caller supplies it:

``shocks``
    a mapping from ``(stage key, builder)`` to the joint table of the shocks
    that builder draws, ``{"nodes": {name: array}, "weights": array}``, every
    array of one length.  The weights are probabilities, or any nonnegative
    weights where the caller computes under a weighted measure.
    :func:`product_table` builds the table of independent shocks.
``policies``
    a mapping from ``(stage key, control)`` to a function of the states the
    control's policy is read at, in the record's order, on arrays.
    :func:`tabulated` makes such a function from a table of one state.

A measure is held as weighted atoms, :class:`Atoms`: a mapping from
``(stage key, field)`` to an array of points, and an array of masses.

Two questions are asked of one period:

- one period ahead, :func:`one_period_ahead`: a measure carried through the
  period's builders and along the inter-period mapping;
- stationary, :func:`transition` and :func:`stationary`: the same map on a
  grid by linear lottery, and its fixed point
  ``mu = s T mu + (1 - s) nu``, with ``s`` the survivors' share of mass and
  ``nu`` the measure of those who enter.  A grid is finite, and the lottery
  places at an end node the mass the map carries beyond it; the transition
  and the fixed point report how much, since a measure that keeps its place
  only because of that is no stationary measure of the map.

:func:`carry` walks a measure between any two places of the period, which
gives the cross-section at a perch inside it.
"""

from __future__ import annotations

from collections import namedtuple

import numpy as np

try:  # SciPy is optional: where it is installed the linear solve is sparse
    from scipy.sparse import csr_matrix, identity
    from scipy.sparse.linalg import spsolve
except ImportError:
    csr_matrix = identity = spsolve = None

# ── Measures ───────────────────────────────────────────────


class Atoms(namedtuple("Atoms", "points masses origin", defaults=(None,))):
    """A finite measure as weighted atoms.

    ``points`` maps ``(stage key, field)`` to an array of N values, one per
    atom, and ``masses`` holds the N masses.  ``origin`` is None, or an array
    of N integers that names for each atom the atom it descends from, which
    :func:`transition` reads.
    """

    __slots__ = ()


def product_table(marginals):
    """The joint table of independent shocks.

    ``marginals`` maps each shock's name to ``(nodes, weights)``.  The table
    holds every combination, the first shock varying slowest, and for each
    the product of the weights.
    """
    names = list(marginals)
    nodes = [np.asarray(marginals[name][0]) for name in names]
    weights = [np.asarray(marginals[name][1], dtype=float) for name in names]
    index = np.meshgrid(*[np.arange(len(n)) for n in nodes], indexing="ij")
    joint = np.ones(index[0].size if index else 1)
    for held, w in zip(index, weights):
        joint = joint * w[held.ravel()]
    return {
        "nodes": {name: n[held.ravel()] for name, n, held in zip(names, nodes, index)},
        "weights": joint,
    }


def tabulated(points, values, tolerance=1e-12):
    """A function of one state read from a table.

    The function answers, for each point it is asked at, the value the table
    holds at the nearest of ``points``.  A point farther than ``tolerance``
    from every tabulated point is refused with a ValueError that counts such
    points and gives the largest distance: the table does not hold the
    function there.
    """
    points = np.asarray(points, dtype=float).ravel()
    values = np.asarray(values, dtype=float).ravel()
    if points.shape != values.shape:
        raise ValueError(
            f"a table holds one value for each point; got {points.size} points and "
            f"{values.size} values"
        )
    order = np.argsort(points, kind="stable")
    held, answers = points[order], values[order]

    def read(asked):
        asked = np.asarray(asked, dtype=float)
        flat = asked.ravel()
        right = np.clip(np.searchsorted(held, flat), 0, held.size - 1)
        left = np.clip(right - 1, 0, held.size - 1)
        nearest = np.where(np.abs(flat - held[left]) <= np.abs(held[right] - flat), left, right)
        distance = np.abs(flat - held[nearest])
        outside = distance > tolerance
        if outside.any():
            raise ValueError(
                f"the table is asked at {int(outside.sum())} of {flat.size} points farther "
                f"than {tolerance} from every point it holds; the largest distance is "
                f"{float(distance.max())}"
            )
        return answers[nearest].reshape(asked.shape)

    return read


# ── The walk through a period ──────────────────────────────


def carry(record, atoms, shocks=None, policies=None, *, start="arrival", stop="leaving"):
    """The measure ``atoms`` carried from one place of the period to another.

    A place is ``"arrival"``, where a measure enters the period;
    ``"leaving"``, where it leaves; or ``(stage key, builder)``, just before
    that builder.  The measure is carried through every builder from
    ``start`` up to ``stop``, and the joins within the period are made after
    the last builder of each stage.  At each builder the measure is extended
    by the table of the builder's shocks, each control is read from its
    policy, and the law of motion is applied; the result is a measure on the
    fields the builder gives, with the masses multiplied by the shocks'
    weights.
    """
    first, last = _place(record, start), _place(record, stop)
    if first > last:
        raise ValueError(
            f"the place {stop!r} stands before the place {start!r} in the period; a measure is "
            "carried forward"
        )
    points = {key: np.asarray(value) for key, value in atoms.points.items()}
    masses = np.asarray(atoms.masses, dtype=float)
    origin = atoms.origin
    for index in range(first, last):
        step = record.steps[index]
        points, masses, origin = _applied(step, points, masses, origin, shocks, policies)
        ends = index + 1 == len(record.steps) or record.steps[index + 1].stage != step.stage
        if ends:
            points = _renamed(points, [pair for pair in record.joins if pair[0][0] == step.stage])
    return Atoms(points, masses, origin)


def connect(record, atoms):
    """The measure ``atoms``, on the fields at which a measure leaves the
    period, as a measure on the arrival fields the inter-period mapping
    joins them to."""
    if not record.connector:
        raise ValueError(
            "the record holds no inter-period mapping; give one to forward_record, as an entry "
            'of a trellis\'s inter_connectors writes it, {"a": "k"}'
        )
    return Atoms(_renamed(dict(atoms.points), record.connector), atoms.masses, atoms.origin)


def one_period_ahead(
    record, atoms, shocks=None, policies=None, *, at="arrival", survival=1.0, entrants=None
):
    """The measure ``atoms`` one period ahead.

    With ``at="arrival"`` the measure stands where a measure enters the
    period: it is carried through the period and then along the inter-period
    mapping, to the arrival fields of the period that mapping joins.  With
    ``at="leaving"`` it stands where a measure leaves: it is carried along
    the mapping first, which then must join the period to itself, and
    through the period after.

    ``survival`` is the share of mass that survives the period, and
    ``entrants`` the measure of those who enter in place of the rest, as
    ``(atoms, place)``: atoms of total mass one that enter the period at
    ``place``, a place as :func:`carry` reads it.  The result is the
    survivors with their masses multiplied by ``survival``, and the entrants
    carried from their place with theirs multiplied by ``1 - survival``.
    """
    if at == "arrival":
        ahead = connect(record, carry(record, atoms, shocks, policies))
    elif at == "leaving":
        _must_be_closed(record)
        ahead = carry(record, connect(record, atoms), shocks, policies)
    else:
        raise ValueError(f'a measure stands at "arrival" or at "leaving"; got {at!r}')
    if entrants is None:
        if survival != 1.0:
            raise ValueError(
                f"with a survivors' share of {survival}, the rest of the mass enters; give the "
                "entrants' measure and the place at which they enter"
            )
        return ahead
    entered = _entered(record, entrants, shocks, policies, at)
    if set(entered.points) != set(ahead.points):
        raise ValueError(
            "the entrants arrive on the fields "
            f"{sorted(entered.points)} and the survivors on {sorted(ahead.points)}"
        )
    return Atoms(
        {key: np.concatenate([ahead.points[key], entered.points[key]]) for key in ahead.points},
        np.concatenate([survival * ahead.masses, (1.0 - survival) * entered.masses]),
    )


def _entered(record, entrants, shocks, policies, at):
    """The entrants carried from their place to where the measure stands."""
    atoms, place = entrants
    carried = carry(record, atoms, shocks, policies, start=place)
    return connect(record, carried) if at == "arrival" else carried


def _must_be_closed(record):
    if not record.closed():
        raise ValueError(
            "the inter-period mapping does not join the period to itself at every field at "
            f"which a measure enters it: it joins {list(record.connector)} to "
            f"{record.joined_to}, and a measure enters at {list(record.arrival)}"
        )


def _place(record, place):
    """The number of builders that stand before a place of the period."""
    if place == "arrival":
        return 0
    if place == "leaving":
        return len(record.steps)
    for index, step in enumerate(record.steps):
        if (step.stage, step.builder) == tuple(place):
            return index
    raise ValueError(
        f'the place {place!r} is none of "arrival", "leaving" and the builders of the record, '
        f"{[(step.stage, step.builder) for step in record.steps]}"
    )


def _renamed(points, pairs):
    """``points`` with the values at each origin of ``pairs`` standing at its
    target; an origin joined to several targets stands at each."""
    if not pairs:
        return points
    moved = {}
    for origin, target in pairs:
        if origin not in points:
            raise KeyError(
                f"the measure holds no field {origin}, which is joined to {target}; it holds "
                f"{sorted(points)}"
            )
        moved[target] = points[origin]
    origins = {origin for origin, _ in pairs}
    kept = {key: value for key, value in points.items() if key not in origins}
    kept.update(moved)
    return kept


def _applied(step, points, masses, origin, shocks, policies):
    """One builder applied to a measure: the points, masses and origins of
    the measure it gives."""
    where = f"{step.stage}.{step.builder}"
    if step.parameter_values is None:
        raise ValueError(
            f"the law of motion of {where} reads the parameters {', '.join(step.parameters)}, "
            "which have no values; calibrate the stage before its forward record is read"
        )
    count = masses.shape[0]
    drawn = {}
    if step.shocks:
        table = (shocks or {}).get((step.stage, step.builder))
        names = [shock.name for shock in step.shocks]
        if table is None:
            raise KeyError(
                f"{where} draws {', '.join(names)}; give their joint table under the key "
                f"{(step.stage, step.builder)!r} of shocks"
            )
        missing = [name for name in names if name not in table["nodes"]]
        if missing:
            raise KeyError(f"the table of {where} holds no nodes for {', '.join(missing)}")
        weights = np.asarray(table["weights"], dtype=float)
        size = weights.shape[0]
        points = {key: np.repeat(value, size, axis=0) for key, value in points.items()}
        drawn = {name: np.tile(np.asarray(table["nodes"][name]), count) for name in names}
        masses = np.repeat(masses, size) * np.tile(weights, count)
        origin = None if origin is None else np.repeat(origin, size)
    controls = {}
    for control in step.controls:
        policy = (policies or {}).get((step.stage, control.name))
        if policy is None:
            raise KeyError(
                f"{where} reads the control {control.name}; give its policy, a function of "
                f"{', '.join(control.read_at)}, under the key {(step.stage, control.name)!r} of "
                "policies"
            )
        controls[control.name] = np.asarray(
            policy(*(_held(points, step.stage, field, where) for field in control.read_at))
        )
    values = []
    for argument, role in zip(step.arguments, step.roles):
        if role == "shock":
            values.append(drawn[argument])
        elif role == "control":
            values.append(controls[argument])
        else:
            values.append(_held(points, step.stage, argument, where))
    result = step.function(*values, *step.parameter_values)
    results = result if isinstance(result, tuple) else (result,)
    given = {key: value for key, value in points.items() if key[0] != step.stage}
    for field, value in zip(step.writes, results):
        given[(step.stage, field)] = np.broadcast_to(np.asarray(value), masses.shape)
    return given, masses, origin


def _held(points, stage, field, where):
    try:
        return points[(stage, field)]
    except KeyError:
        raise KeyError(
            f"{where} reads the state {field} of stage {stage!r}, and the measure holds no "
            f"field {(stage, field)!r}; it holds {sorted(points)}"
        ) from None


# ── The measure on a grid ──────────────────────────────────


def lottery(nodes, values):
    """The linear lottery of ``values`` onto the increasing ``nodes``:
    ``(j, low, high)``, where each value puts the share ``low`` of its mass
    on node ``j`` and ``high`` on node ``j + 1``.  A value below the first
    node or above the last is placed at that node, so that mass beyond the
    grid stands at its ends.
    """
    nodes = np.asarray(nodes, dtype=float)
    if nodes.ndim != 1 or nodes.size < 2:
        raise ValueError("a grid of one field is at least two increasing nodes")
    count = nodes.size
    x = np.clip(values, nodes[0], nodes[-1])
    j = np.clip(np.searchsorted(nodes, x, side="right") - 1, 0, count - 2)
    high = (x - nodes[j]) / (nodes[j + 1] - nodes[j])
    return j, 1.0 - high, high


# a point counts as beyond an end of a grid where it passes the end node by
# more than this share of the grid's length, so that rounding at an end node
# is not read as mass that leaves the grid
BEYOND_TOLERANCE = 1e-12


def _corners(grid, points):
    """For a product grid, the nodes each point puts mass on and the share
    on each: pairs ``(index, share)``, one per corner of the cell, the index
    that of the node in the grid's arrays read in C order; then, for each
    point, whether it lies below the first node of some field and whether
    it lies above the last node of some field (``BEYOND_TOLERANCE``)."""
    fields = list(grid)
    missing = [field for field in fields if field not in points]
    if missing or len(points) != len(fields):
        raise ValueError(
            f"the grid is on the fields {fields} and the measure on {sorted(points)}; a measure "
            "is placed on a grid of its own fields"
        )
    shape = tuple(np.asarray(grid[field]).size for field in fields)
    lotteries = [lottery(grid[field], points[field]) for field in fields]
    corners = [(np.zeros_like(lotteries[0][0]), 1.0)]
    for size, (j, low, high) in zip(shape, lotteries):
        corners = [
            (index * size + j + step, share * part)
            for index, share in corners
            for step, part in ((0, low), (1, high))
        ]
    below = np.zeros(np.shape(lotteries[0][0]), dtype=bool)
    above = np.zeros(np.shape(lotteries[0][0]), dtype=bool)
    for field in fields:
        nodes, values = np.asarray(grid[field], dtype=float), np.asarray(points[field])
        slack = BEYOND_TOLERANCE * (nodes[-1] - nodes[0])
        below |= values < nodes[0] - slack
        above |= values > nodes[-1] + slack
    return shape, corners, below, above


def measure_on_grid(grid, atoms):
    """The masses the atoms put on the nodes of a product grid by linear
    lottery, as one array in the grid's shape.  ``grid`` maps each field of
    the measure, ``(stage key, field)``, to its increasing nodes."""
    shape, corners, _, _ = _corners(grid, atoms.points)
    size = int(np.prod(shape))
    masses = np.asarray(atoms.masses, dtype=float)
    total = np.zeros(size)
    for index, share in corners:
        total += np.bincount(index, weights=masses * share, minlength=size)
    return total.reshape(shape)


class Transition(
    namedtuple("Transition", "rows columns values size shape fields at below above")
):
    """One period's forward map on the nodes of a grid, as the triplets of a
    square matrix: the mass ``values[i]`` moves from node ``columns[i]`` to
    node ``rows[i]``.  A pair of nodes may stand in several triplets, whose
    values add.  ``shape`` is the grid's shape, ``fields`` its fields and
    ``at`` the place of the period the grid stands at.

    ``below`` and ``above`` hold, for each node, the mass that the map
    carries from it beyond the grid, below the first node of some field or
    above the last node of some field, and that the lottery placed at that
    end.  Where they are not zero, the matrix is the map of the period on
    the grid's inside alone.
    """

    __slots__ = ()

    def apply(self, mass):
        """The measure ``mass`` on the grid one period ahead, survivors
        alone."""
        flat = np.asarray(mass, dtype=float).ravel()
        moved = np.bincount(
            self.rows, weights=self.values * flat[self.columns], minlength=self.size
        )
        return moved.reshape(np.shape(mass))

    def toarray(self):
        """The matrix, dense."""
        dense = np.zeros((self.size, self.size))
        np.add.at(dense, (self.rows, self.columns), self.values)
        return dense


def transition(record, grid, shocks=None, policies=None, *, at="leaving"):
    """One period's forward map on a product grid, by linear lottery.

    ``grid`` maps each field at the place ``at``, ``(stage key, field)``, to
    its increasing nodes: the fields at which a measure leaves the period,
    or, with ``at="arrival"``, those at which it enters.  The unit mass at
    each node is carried one period ahead (:func:`one_period_ahead`) and
    placed on the grid (:func:`lottery`).  The inter-period mapping of the
    record must join the period to itself.  The mass each node sends beyond
    the grid is held in the result's ``below`` and ``above``.
    """
    _must_be_closed(record)
    fields = list(grid)
    held = [np.asarray(grid[field], dtype=float) for field in fields]
    size = int(np.prod([nodes.size for nodes in held]))
    mesh = np.meshgrid(*held, indexing="ij")
    start = Atoms(
        {field: values.ravel() for field, values in zip(fields, mesh)},
        np.ones(size),
        np.arange(size),
    )
    ahead = one_period_ahead(record, start, shocks, policies, at=at)
    shape, corners, below, above = _corners(grid, ahead.points)
    return Transition(
        rows=np.concatenate([index for index, _ in corners]),
        columns=np.concatenate([ahead.origin for _ in corners]),
        values=np.concatenate([ahead.masses * share for _, share in corners]),
        size=size,
        shape=shape,
        fields=tuple(fields),
        at=at,
        below=np.bincount(ahead.origin, weights=ahead.masses * below, minlength=size),
        above=np.bincount(ahead.origin, weights=ahead.masses * above, minlength=size),
    )


def entrants_on_grid(record, grid, entrants, shocks=None, policies=None, *, at="leaving"):
    """The measure of those who enter, on the grid at the place ``at``:
    ``entrants`` is ``(atoms, place)`` as :func:`one_period_ahead` reads it,
    and the atoms are carried from their place and placed on the grid."""
    return measure_on_grid(grid, _entered(record, entrants, shocks, policies, at))


# ── The fixed point ────────────────────────────────────────


class Stationary(
    namedtuple("Stationary", "mass method iterations change converged below above")
):
    """What :func:`stationary` answers: ``mass``, the measure on the grid,
    of total mass one, in the grid's shape; ``method``, the method that
    computed it; ``iterations``, the number of applications of the map, zero
    for a linear solve; ``change``, the largest change of a node's mass over
    one more period, ``max |s T mu + (1 - s) nu - mu|``, the measure
    normalized after the step where the survivors' share is one;
    ``converged``, whether an iteration stopped below its tolerance, True
    for a linear solve; and ``below`` and ``above``, the shares of the mass
    the survivors carry one more period ahead that the map carries beyond
    the grid, below its first node or above its last, and that the lottery
    returned to that end.

    A measure may keep its place only because of that return: where the map
    moves every household up without end, an iteration converges to all the
    mass at the top node, with ``above`` near one.  Such a measure is no
    stationary measure of the map.  A small ``below`` or ``above`` says that
    the grid's end holds little of the measure; ``held_at_an_end`` compares
    their sum with a tolerance."""

    __slots__ = ()

    def held_at_an_end(self, tolerance=1e-6):
        """Whether more than ``tolerance`` of the mass one more period ahead
        is mass the lottery returned from beyond the grid."""
        return self.below + self.above > tolerance

    __slots__ = ()


def stationary(
    transition,
    entrants=None,
    *,
    survival=1.0,
    method=None,
    tolerance=1e-14,
    max_iterations=200_000,
):
    """The fixed point of one period's forward map on a grid,
    ``mu = s T mu + (1 - s) nu``.

    ``transition`` is the :class:`Transition` ``T``; ``survival`` is ``s``,
    the survivors' share of mass; ``entrants`` is ``nu``, the measure on the
    grid of those who enter (:func:`entrants_on_grid`), which a share below
    one requires.

    With ``s < 1`` the method is ``"linear-solve"``, the solution of
    ``(I - s T) mu = (1 - s) nu``, sparse where SciPy is installed and dense
    otherwise, or ``"iteration"`` of the map from ``nu``.  With ``s = 1``
    it is ``"power-iteration"`` from the uniform measure, the measure
    normalized to total mass one at each step.  An iteration stops when no
    node's mass changes by ``tolerance`` or more, or after
    ``max_iterations`` steps.  The result is cut off at zero and normalized
    to total mass one.  ``below`` and ``above`` of the result say how much
    of it the grid's ends hold (:class:`Stationary`).
    """
    size = transition.size
    share = float(survival)
    if not 0.0 < share <= 1.0:
        raise ValueError(f"the survivors' share of mass is in (0, 1]; got {survival}")
    iterations, converged = 0, True
    if share < 1.0:
        if entrants is None:
            raise ValueError(
                f"with a survivors' share of {survival}, the rest of the mass enters; give the "
                "entrants' measure on the grid"
            )
        entered = np.asarray(entrants, dtype=float).ravel()
        method = "linear-solve" if method is None else method
        if method == "linear-solve":
            mass, method = _solved(transition, share, (1.0 - share) * entered)
        elif method == "iteration":
            mass, converged = entered / entered.sum(), False
            for iterations in range(1, max_iterations + 1):
                new = share * transition.apply(mass) + (1.0 - share) * entered
                moved = np.abs(new - mass).max()
                mass = new
                if moved < tolerance:
                    converged = True
                    break
        else:
            raise ValueError(
                'with a survivors\' share below one the method is "linear-solve" or '
                f'"iteration"; got {method!r}'
            )
    else:
        entered = np.zeros(size)
        method = "power-iteration" if method is None else method
        if method != "power-iteration":
            raise ValueError(
                f'with a survivors\' share of one the method is "power-iteration"; got {method!r}'
            )
        mass, converged = np.full(size, 1.0 / size), False
        for iterations in range(1, max_iterations + 1):
            new = transition.apply(mass)
            new = new / new.sum()
            moved = np.abs(new - mass).max()
            mass = new
            if moved < tolerance:
                converged = True
                break
    mass = np.clip(np.asarray(mass, dtype=float).ravel(), 0.0, None)
    mass = mass / mass.sum()
    carried = transition.apply(mass)
    ahead = share * carried + (1.0 - share) * entered
    if share == 1.0:
        ahead = ahead / ahead.sum()
    return Stationary(
        mass=mass.reshape(transition.shape),
        method=method,
        iterations=iterations,
        change=float(np.abs(ahead - mass).max()),
        converged=converged,
        below=float(transition.below @ mass) / float(carried.sum()),
        above=float(transition.above @ mass) / float(carried.sum()),
    )


def _solved(transition, share, right):
    """The solution of ``(I - share T) x = right`` and the name of the
    method: sparse with SciPy where it is installed, dense with NumPy
    otherwise."""
    size = transition.size
    if spsolve is None:
        dense = np.eye(size) - share * transition.toarray()
        return np.linalg.solve(dense, right), "linear-solve (dense, NumPy)"
    matrix = csr_matrix(
        (transition.values, (transition.rows, transition.columns)), shape=(size, size)
    )
    solved = spsolve(identity(size, format="csc") - share * matrix.tocsc(), right)
    return np.asarray(solved).ravel(), "linear-solve (sparse, SciPy)"
