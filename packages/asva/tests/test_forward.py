"""The tests of `asva.forward`: a measure carried through a period
from its forward record, one period ahead, the transition on a grid and its
fixed point, each against values computed by hand or against the same
arithmetic written out.

No test reads a stage: asva imports nothing of `bellman`. A forward record
is plain data read by its attributes, and each record here is written by
hand with `SimpleNamespace`, which also states what `asva.forward` reads of
one: of a step, `stage`, `builder`, `shocks` (each with `name`), `controls`
(each with `name` and `read_at`), `function`, `arguments`, `roles`,
`writes`, `parameters` and `parameter_values`; of the record, `steps`,
`joins`, `connector`, `arrival`, `joined_to` and `closed()`.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from asva.forward import (Atoms, carry, connect, entrants_on_grid, lottery, measure_on_grid, one_period_ahead,
                          product_table, stationary, tabulated, transition)


def _step(stage, builder, function, arguments, roles, writes, shocks=(), controls=(), parameters=(), values=()):
    return SimpleNamespace(
        stage=stage, builder=builder, function=function, arguments=arguments, roles=roles, writes=writes,
        shocks=tuple(SimpleNamespace(name=name) for name in shocks),
        controls=tuple(SimpleNamespace(name=name, read_at=read_at) for name, read_at in controls),
        parameters=parameters, parameter_values=values)


def _record(steps, joins=(), connector=(), arrival=(), joined_to=None):
    record = SimpleNamespace(steps=tuple(steps), joins=tuple(joins), connector=tuple(connector),
                             arrival=tuple(arrival), joined_to=joined_to)
    record.closed = lambda: joined_to == "itself" and {target for _, target in connector} == {
        (stage, field) for stage, field, _ in arrival}
    return record


def _two_stages():
    """The stage `earn`, with resources m = R k + 1 and savings b = m - c, joined
    to the stage `keep`, which is entered at its decision perch and keeps
    nine tenths of its assets; what leaves `keep` is the next period's k."""
    return _record(
        [_step("earn", "arvl_to_dcsn", lambda k, R: R * k + 1.0, ("k",), ("state",), ("m",),
               parameters=("R",), values=(2.0,)),
         _step("earn", "dcsn_to_cntn", lambda m, c: m - c, ("m", "c"), ("state", "control"), ("b",),
               controls=(("c", ("m",)),)),
         _step("keep", "dcsn_to_cntn", lambda a: 0.9 * a, ("a",), ("state",), ("a_next",))],
        joins=[(("earn", "b"), ("keep", "a"))],
        connector=[(("keep", "a_next"), ("earn", "k"))],
        arrival=[("earn", "k", "ℝ₊")], joined_to="itself")


def _buffer_stock():
    """One stage with the buffer-stock laws m = R k/(Γ ψ) + ξ and a = m - c."""
    return _record(
        [_step("bs", "arvl_to_dcsn", lambda k, psi, xi, R, G: R * k / (G * psi) + xi, ("k", "ψ", "ξ"),
               ("state", "shock", "shock"), ("m",), shocks=("ψ", "ξ"), parameters=("R", "Γ"), values=(1.03, 1.01)),
         _step("bs", "dcsn_to_cntn", lambda m, c: m - c, ("m", "c"), ("state", "control"), ("a",),
               controls=(("c", ("m",)),))],
        connector=[(("bs", "a"), ("bs", "k"))], arrival=[("bs", "k", "ℝ₊")], joined_to="itself")


def _consumption(m):
    return 0.25 * m + 0.05 * m / (1.0 + m)


def test_forward_carries_a_measure_through_two_stages_a_join_and_the_inter_period_mapping_by_hand():
    """Assets 1 and 3 with masses 1/4 and 3/4, R = 2, c = m/2: m = 3 and 7,
    b = 1.5 and 3.5, which `keep` takes as a and leaves as 1.35 and 3.15, the
    next period's k. The masses do not change."""
    record = _two_stages()
    policies = {("earn", "c"): lambda m: 0.5 * m}
    start = Atoms({("earn", "k"): np.array([1.0, 3.0])}, np.array([0.25, 0.75]))

    leaving = carry(record, start, policies=policies)
    assert list(leaving.points) == [("keep", "a_next")]
    assert np.allclose(leaving.points[("keep", "a_next")], [1.35, 3.15])
    assert np.array_equal(leaving.masses, [0.25, 0.75])
    ahead = one_period_ahead(record, start, policies=policies)
    assert np.allclose(ahead.points[("earn", "k")], [1.35, 3.15]) and list(ahead.points) == [("earn", "k")]
    assert np.allclose(connect(record, leaving).points[("earn", "k")], [1.35, 3.15])

    # between two places inside the period: the join is made after `earn`
    inside = carry(record, start, policies=policies, stop=("keep", "dcsn_to_cntn"))
    assert np.allclose(inside.points[("keep", "a")], [1.5, 3.5]) and list(inside.points) == [("keep", "a")]
    late = carry(record, Atoms({("earn", "m"): np.array([3.0])}, np.array([1.0])), policies=policies,
                 start=("earn", "dcsn_to_cntn"))
    assert np.allclose(late.points[("keep", "a_next")], [1.35])
    # where a measure leaves the period, it is carried along the mapping first
    again = one_period_ahead(record, leaving, policies=policies, at="leaving")
    assert np.allclose(again.points[("keep", "a_next")], [0.9 * (2 * 1.35 + 1) / 2, 0.9 * (2 * 3.15 + 1) / 2])

    with pytest.raises(KeyError, match="give its policy, a function of m"):
        carry(record, start)
    with pytest.raises(ValueError, match="carried forward"):
        carry(record, start, policies=policies, start="leaving", stop="arrival")
    with pytest.raises(ValueError, match="have no values; calibrate the stage"):
        carry(_record([_step("s", "b", lambda k, R: k, ("k",), ("state",), ("m",), parameters=("R",),
                             values=None)]), Atoms({("s", "k"): np.ones(1)}, np.ones(1)))


def test_forward_extends_a_measure_by_the_table_of_a_builder_s_shocks():
    """One atom at k = 1: with income 0 or 2 at weights 1/4 and 3/4 and the
    event `work` or `rest` at 0.9 and 0.1, m = k + y for `work` and k for
    `rest`: four atoms whose masses are the products of the weights."""
    table = product_table({"y": (np.array([0.0, 2.0]), np.array([0.25, 0.75])),
                           "j": (np.array(["work", "rest"]), np.array([0.9, 0.1]))})
    assert list(table["nodes"]["y"]) == [0.0, 0.0, 2.0, 2.0] and list(table["nodes"]["j"]) == ["work", "rest"] * 2
    assert np.allclose(table["weights"], [0.225, 0.025, 0.675, 0.075])
    record = _record([_step("s", "arvl_to_dcsn", lambda k, y, j: k + np.where(j == "work", y, 0.0), ("k", "y", "j"),
                            ("state", "shock", "shock"), ("m",), shocks=("y", "j"))])
    given = carry(record, Atoms({("s", "k"): np.array([1.0])}, np.array([1.0])), {("s", "arvl_to_dcsn"): table})
    assert np.allclose(given.points[("s", "m")], [1.0, 1.0, 3.0, 1.0]) and np.allclose(given.masses, table["weights"])
    with pytest.raises(KeyError, match="draws y, j; give their joint table"):
        carry(record, Atoms({("s", "k"): np.array([1.0])}, np.array([1.0])))


def test_forward_places_a_measure_on_a_product_grid_by_linear_lottery():
    """On the nodes 0, 1 the value 0.25 puts 3/4 on node 0; a value beyond
    the grid stands at its end. On the product grid with nodes 0, 2 in the
    second field, the point (0.25, 0.5) puts 9/16, 3/16, 3/16 and 1/16 on
    the four nodes."""
    j, low, high = lottery(np.array([0.0, 1.0, 3.0]), np.array([0.25, 2.0, -1.0, 5.0]))
    assert list(j) == [0, 1, 0, 1] and np.allclose(low, [0.75, 0.5, 1.0, 0.0]) and np.allclose(high, 1.0 - low)
    grid = {("s", "x"): np.array([0.0, 1.0]), ("s", "y"): np.array([0.0, 2.0])}
    mass = measure_on_grid(grid, Atoms({("s", "x"): np.array([0.25]), ("s", "y"): np.array([0.5])}, np.array([1.0])))
    assert np.allclose(mass, [[0.5625, 0.1875], [0.1875, 0.0625]])
    with pytest.raises(ValueError, match="placed on a grid of its own fields"):
        measure_on_grid(grid, Atoms({("s", "x"): np.array([0.25])}, np.array([1.0])))


def test_forward_transition_on_a_grid_is_the_two_laws_written_out_and_one_period_ahead_agrees():
    """The transition of the buffer-stock laws on a grid of assets equals
    the matrix built from m = R a/(Γ ψ) + ξ and a = m - c written out, node
    by node, on the fields where a measure leaves the period and on those
    where it enters; the measure of the entrants equals theirs written out;
    and one period ahead on atoms equals s T mu + (1 - s) nu."""
    record = _buffer_stock()
    table = product_table({"ψ": (np.array([0.9, 1.0, 1.1]), np.array([0.25, 0.5, 0.25])),
                           "ξ": (np.array([0.0, 0.8, 1.2]), np.array([0.005, 0.4975, 0.4975]))})
    shocks, policies = {("bs", "arvl_to_dcsn"): table}, {("bs", "c"): _consumption}
    nodes = np.concatenate([[0.0], np.geomspace(1e-6, 30.0, 150)])
    count = nodes.size
    written = np.zeros((count, count))
    for weight, psi, xi in zip(table["weights"], table["nodes"]["ψ"], table["nodes"]["ξ"]):
        m = 1.03 * nodes / (1.01 * psi) + xi
        j, low, high = lottery(nodes, m - _consumption(m))
        np.add.at(written, (j, np.arange(count)), weight * low)
        np.add.at(written, (j + 1, np.arange(count)), weight * high)

    leaving = transition(record, {("bs", "a"): nodes}, shocks, policies)
    assert (leaving.size, leaving.shape, leaving.fields, leaving.at) == (count, (count,), (("bs", "a"),), "leaving")
    assert np.abs(leaving.toarray() - written).max() < 1e-15
    assert not leaving.below.any() and not leaving.above.any()  # no node sends mass beyond this grid
    arriving = transition(record, {("bs", "k"): nodes}, shocks, policies, at="arrival")
    assert np.abs(arriving.toarray() - written).max() < 1e-15
    assert np.allclose(written.sum(axis=0), 1.0)

    born_m, born_p = np.array([0.8, 1.0, 1.2]), np.array([0.3, 0.4, 0.3])
    entrants = (Atoms({("bs", "m"): born_m}, born_p), ("bs", "dcsn_to_cntn"))
    entered = entrants_on_grid(record, {("bs", "a"): nodes}, entrants, shocks, policies)
    j, low, high = lottery(nodes, born_m - _consumption(born_m))
    by_hand = np.zeros(count)
    np.add.at(by_hand, j, born_p * low)
    np.add.at(by_hand, j + 1, born_p * high)
    assert np.array_equal(entered, by_hand)

    mass = np.full(count, 1.0 / count)
    ahead = one_period_ahead(record, Atoms({("bs", "a"): nodes}, mass), shocks, policies, at="leaving",
                             survival=0.99, entrants=entrants)
    assert len(ahead.masses) == count * 9 + 3
    on_grid = measure_on_grid({("bs", "a"): nodes}, ahead)
    assert np.abs(on_grid - (0.99 * written @ mass + 0.01 * by_hand)).max() < 1e-15
    assert np.abs(leaving.apply(mass) - written @ mass).max() < 1e-15
    with pytest.raises(ValueError, match="the rest of the mass enters"):
        one_period_ahead(record, Atoms({("bs", "a"): nodes}, mass), shocks, policies, at="leaving", survival=0.99)
    with pytest.raises(ValueError, match="does not join the period to itself"):
        transition(_record(record.steps, arrival=record.arrival), {("bs", "a"): nodes}, shocks, policies)


def test_forward_stationary_finds_the_fixed_point_by_each_method():
    """With every survivor the fixed point is the eigenvector, by power
    iteration from the uniform measure. With a survivors' share of 0.99 it
    solves (I - s T) mu = (1 - s) nu: by the linear solve it equals the
    dense solution, and the iteration agrees with it. Each is unchanged one
    period ahead. An iteration that reaches its cap before its tolerance
    says that it did not converge: on three nodes, a map that halves the
    mass of the third node at each step reaches the tolerance within fifty
    steps, and one whose mass on the first two nodes turns between them
    while it shrinks does not."""
    record = _buffer_stock()
    table = product_table({"ψ": (np.array([0.9, 1.0, 1.1]), np.array([0.25, 0.5, 0.25])),
                           "ξ": (np.array([0.0, 0.8, 1.2]), np.array([0.005, 0.4975, 0.4975]))})
    shocks, policies = {("bs", "arvl_to_dcsn"): table}, {("bs", "c"): _consumption}
    grid = {("bs", "a"): np.concatenate([[0.0], np.geomspace(1e-6, 30.0, 150)])}
    held = transition(record, grid, shocks, policies)
    dense = held.toarray()

    all_survive = stationary(held)
    assert all_survive.method == "power-iteration" and all_survive.converged and all_survive.iterations > 1
    assert all_survive.mass.sum() == pytest.approx(1.0) and all_survive.change < 1e-13
    assert (all_survive.below, all_survive.above) == (0.0, 0.0) and not all_survive.held_at_an_end()
    assert np.abs(dense @ all_survive.mass - all_survive.mass).max() < 1e-13

    entrants = (Atoms({("bs", "m"): np.array([0.8, 1.0, 1.2])}, np.array([0.3, 0.4, 0.3])), ("bs", "dcsn_to_cntn"))
    entered = entrants_on_grid(record, grid, entrants, shocks, policies)
    solution = np.linalg.solve(np.eye(held.size) - 0.99 * dense, 0.01 * entered)
    solved = stationary(held, entered, survival=0.99)
    assert solved.method.startswith("linear-solve") and solved.iterations == 0 and solved.converged
    assert np.abs(solved.mass - solution / solution.sum()).max() < 1e-12 and solved.change < 1e-14
    iterated = stationary(held, entered, survival=0.99, method="iteration")
    assert iterated.converged and np.abs(iterated.mass - solved.mass).max() < 1e-11

    with pytest.raises(ValueError, match="give the entrants' measure on the grid"):
        stationary(held, survival=0.99)
    with pytest.raises(ValueError, match='the method is "power-iteration"'):
        stationary(held, method="linear-solve")
    halving = held._replace(rows=np.array([1, 0, 2]), columns=np.array([0, 1, 2]),
                            values=np.array([1.0, 1.0, 0.5]), size=3, shape=(3,), below=np.zeros(3),
                            above=np.zeros(3))
    reached = stationary(halving, max_iterations=50)
    assert reached.converged and np.allclose(reached.mass, [0.5, 0.5, 0.0])
    turning = halving._replace(values=np.array([1.0, 0.5, 1.0]))
    stopped = stationary(turning, max_iterations=50)
    assert not stopped.converged and stopped.iterations == 50 and stopped.change > 1e-14


def test_forward_reads_a_policy_from_a_table_and_refuses_a_point_the_table_does_not_hold():
    read = tabulated(np.array([3.0, 1.0, 2.0]), np.array([30.0, 10.0, 20.0]))
    assert list(read(np.array([2.0, 1.0 + 1e-13, 3.0]))) == [20.0, 10.0, 30.0]
    assert read(np.array([[1.0], [3.0]])).shape == (2, 1)
    with pytest.raises(ValueError, match="asked at 1 of 2 points farther than 1e-12"):
        read(np.array([1.0, 1.5]))
    with pytest.raises(ValueError, match="one value for each point"):
        tabulated(np.array([1.0, 2.0]), np.array([1.0]))


def test_forward_reports_the_mass_a_map_carries_beyond_the_grid_and_the_lottery_returns_to_its_ends():
    """A map that moves every household up, k' = 1.5 k, has no stationary
    measure. On the nodes 1, 2, ..., 10 the nodes from 7 up send all their
    mass above the last node; the iteration converges, to all the mass at
    the top node, and the result says that the whole of it is mass the
    lottery returned from above the grid. A map that moves every household
    down toward 0, k' = 0.5 k, is reported at the other end. A map that
    keeps every household where it is sends nothing beyond the grid: a
    point that passes an end node by rounding alone is not counted."""
    def one_stage(function):
        return _record([_step("s", "dcsn_to_cntn", function, ("k",), ("state",), ("k_next",))],
                       connector=[(("s", "k_next"), ("s", "k"))], arrival=[("s", "k", "ℝ₊₊")], joined_to="itself")

    grid = {("s", "k"): np.arange(1.0, 11.0)}
    rising = transition(one_stage(lambda k: 1.5 * k), grid, at="arrival")
    assert list(rising.above) == [0.0] * 6 + [1.0] * 4 and not rising.below.any()
    piled = stationary(rising)
    assert piled.converged and piled.mass[-1] == pytest.approx(1.0)
    assert piled.above == pytest.approx(1.0) and piled.below == 0.0 and piled.held_at_an_end()

    falling = stationary(transition(one_stage(lambda k: 0.5 * k), grid, at="arrival"))
    assert falling.mass[0] == pytest.approx(1.0) and falling.below == pytest.approx(1.0) and falling.above == 0.0

    staying = transition(one_stage(lambda k: k * (1.0 + 1e-15)), grid, at="arrival")
    assert not staying.above.any() and not stationary(staying).held_at_an_end()
