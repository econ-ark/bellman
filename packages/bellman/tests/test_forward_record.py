"""The acceptance file of the forward record of a period (CDC, 12 November
2026): one test for each item, named `test_item_<n>_<claim>`.

1. Of a period made of the buffer-stock stage alone, the record names for
   each forward builder the states it reads, the shocks it draws with the
   law the stage declares and the values of the parameters that law reads,
   the control with the state its policy is read at, the law of motion as a
   function, and the fields it gives; `needs()` lists what is to be given.
   An inter-period mapping that joins the period to itself closes the
   record; without a mapping it is open.
2. Of a period of three stages of the portfolio-choice trellis, the record
   holds the builders in the period's forward order, the joins within the
   period, the fields at which a measure enters and leaves, and the joins of
   the mapping to the period that follows; an arrival field no mapping
   reaches leaves the record open.
3. A stage that declares no arrival perch is entered at its decision perch
   and gives one builder.
4. A period that holds a record in place of a stage is refused under
   `record-shape`, and a stage whose forward builders are not constructed
   with the refusal that says why, both by the package's own checks; a
   period that follows given with no mapping, with a ValueError.
5. With `asva.forward`, the record of the buffer-stock stage gives the
   transition on a grid that the stage's two laws of motion give when they
   are written out, and its fixed point is unchanged one period ahead.
6. Death and birth are stated in a stage: a period of the buffer-stock
   stage and a stage in which a household survives with probability ℒ or is
   replaced by a newborn with assets k_0 has, as the fixed point of its own
   forward map, the stationary measure that the buffer-stock stage alone
   has with the survivors' share ℒ and entrants with assets k_0 given as
   arguments.
"""

import numpy as np
import pytest
from conftest import BUFFER_STOCK_METHODS, PORTFOLIO, ROOT

from bellman.period import ForwardRecord, forward_record
from bellman.refusals import FactoryError, NotConstructed
from bellman.stage import elaborate_stage, elaborate_text, load_stage
from bellman.trellis import elaborate_trellis, load_recipe

BUFFER_STOCK = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
CALIBRATION = {"β": 0.96, "ρ": 2.0, "R": 1.03, "Γ": 1.01, "σ_ψ": 0.1, "σ_ξ": 0.1, "p_zero": 0.005}
EZ_SAVINGS = "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl"
RETIREE_DEATH = "applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl"

# a stage that ends a period: the household survives and keeps its assets, or
# dies and is replaced by a newborn
MORTALITY = """@stage: mortality

Xa := ℝ₊₊
Life := {survive, die}   :: ["the household survives the period; it dies and a newborn takes its place"]

ℒ : (0,1]        :: ["probability of surviving into the next period"]
k_0 : ℝ₊₊        :: ["assets of a newborn"]

s : Life
s ~ Categorical((ℒ, 1 - ℒ))     :: ["surviving or dying, with probabilities in the order of the labels"]

[id=arvl_to_dcsn, (a_end : Xa, s) : !arvl -> (b : Xa) : !dcsn] {
    b = (a_end, k_0)[s]           :: [id=assets_kept_or_endowed]
}

[id=dcsn_to_cntn, (b) : !dcsn -> (k_next : Xa) : !cntn] {
    k_next = b                    :: [id=carried]
}
"""
SHOCKS = {
    "ψ": (np.array([0.9, 1.0, 1.1]), np.array([0.25, 0.5, 0.25])),
    "ξ": (np.array([0.0, 0.8, 1.2]), np.array([0.005, 0.4975, 0.4975])),
}


def _consumption(m):
    return 0.25 * m + 0.05 * m / (1.0 + m)


def _buffer_stock(calibrated=True):
    stage = elaborate_stage(load_stage(str(ROOT / BUFFER_STOCK), [str(ROOT / BUFFER_STOCK_METHODS)]))
    if calibrated:
        stage.calibrate({"calibration": CALIBRATION})
    return {"stages": {"bs": stage}, "connectors": []}


@pytest.fixture(scope="module")
def portfolio():
    return elaborate_trellis(load_recipe(PORTFOLIO, "spec.yml"))


def test_item_1_the_record_names_what_each_forward_builder_needs_and_gives():
    record = forward_record(_buffer_stock())
    assert isinstance(record, ForwardRecord)
    arrival, decision = record.steps
    assert (arrival.stage, arrival.builder, arrival.source, arrival.target) == (
        "bs", "arvl_to_dcsn", "arvl", "dcsn")
    assert arrival.states == ("k",) and arrival.controls == () and arrival.writes == ("m",)
    assert arrival.arguments == ("k", "ψ", "ξ") and arrival.roles == ("state", "shock", "shock")
    assert (arrival.parameters, arrival.parameter_values) == (("R", "Γ"), (1.03, 1.01))
    assert arrival.function(2.0, 1.0, 0.5, *arrival.parameter_values) == 1.03 * 2.0 / 1.01 + 0.5

    permanent, transitory = arrival.shocks
    assert (permanent.name, permanent.set, permanent.family) == ("ψ", "ℝ₊₊", "LogNormal")
    assert permanent.law == "LogNormal(-σ_ψ^2/2, σ_ψ)" and permanent.jointly == ("ψ",)
    assert permanent.argument_values == pytest.approx((-0.005, 0.1))
    assert (permanent.parameters, permanent.parameter_values) == (("σ_ψ",), (0.1,))
    # the law of ξ reads the derived parameter μ_ξ, whose value the record holds
    assert transitory.family == "Mixture" and transitory.parameters == ("p_zero", "μ_ξ", "σ_ξ")
    assert transitory.parameter_values == pytest.approx((0.005, -np.log(1 - 0.005) - 0.1**2 / 2, 0.1))

    assert decision.states == ("m",) and decision.shocks == () and decision.writes == ("a",)
    assert decision.arguments == ("m", "c") and decision.roles == ("state", "control")
    (control,) = decision.controls
    assert (control.name, control.set, control.read_at) == ("c", "ℝ₊₊", ("m",))
    assert decision.function(3.0, 1.0) == 2.0 and decision.outputs == ("a≻",)

    assert record.needs() == {
        "shocks": {("bs", "arvl_to_dcsn"): ("ψ", "ξ")}, "policies": {("bs", "c"): ("m",)}, "parameters": []}
    symbolic = forward_record(_buffer_stock(calibrated=False))
    assert symbolic.steps[0].parameter_values is None and symbolic.steps[0].shocks[0].parameter_values is None
    assert symbolic.needs()["parameters"] == [("bs", "arvl_to_dcsn", "R"), ("bs", "arvl_to_dcsn", "Γ")]
    assert "policy    c(m), to be given" in str(record) and "draws     ψ ~ LogNormal" in str(record)
    assert record.period == "the period of bs" and str(record).startswith("forward record of the period of bs")


    # joined to itself by the inter-period mapping, the record is closed
    period = _buffer_stock()
    record = forward_record(period, {"a": "k"})
    assert record.arrival == (("bs", "k", "Xa"),) and record.leaving == (("bs", "a", "Xa"),)
    assert record.connector == ((("bs", "a"), ("bs", "k")),) and record.joined_to == "itself"
    assert record.closed()
    alone = forward_record(period)
    assert alone.connector == () and alone.joined_to is None and not alone.closed()


def test_item_2_a_period_of_several_stages_is_recorded_in_its_forward_order(portfolio):
    later, earlier = portfolio["periods"][1], portfolio["periods"][0]
    record = forward_record(later, portfolio["inter_connectors"][0], to=earlier, address="periods[1]")
    assert [(step.stage, step.builder) for step in record.steps] == [
        ("port", "arvl_to_dcsn"), ("port", "dcsn_to_cntn"), ("cons", "arvl_to_dcsn"),
        ("cons", "dcsn_to_cntn"), ("disc", "arvl_to_dcsn"), ("disc", "dcsn_to_cntn")]
    assert set(record.joins) == {(("port", "m_next"), ("cons", "m")), (("cons", "a"), ("disc", "a"))}
    assert [field[:2] for field in record.arrival] == [("port", "k"), ("cons", "l")]
    assert record.leaving == (("disc", "a", "Xa"),)
    assert record.connector == ((("disc", "a"), ("port", "k")),)
    assert (record.period, record.joined_to) == ("periods[1]", "the period of port, cons, disc")
    # one declaration draws the two returns together
    risky, labour = record.steps[1].shocks
    assert risky.jointly == labour.jointly == ("Ψ", "θ") and risky.law == labour.law
    assert record.needs()["policies"] == {("port", "ς"): ("k_d",), ("cons", "c"): ("m_d",)}
    # joined to itself, the mapping reaches port.k and not cons.l
    assert not forward_record(later, portfolio["inter_connectors"][0]).closed()


def test_item_3_a_stage_with_no_arrival_perch_is_entered_at_its_decision_perch():
    stage = elaborate_stage(load_stage(str(ROOT / EZ_SAVINGS)))
    record = forward_record({"stages": {"ez": stage}, "connectors": []})
    (step,) = record.steps
    assert (step.source, step.target) == ("dcsn", "cntn")
    assert {field[1] for field in record.arrival} == set(step.states)


def test_item_4_what_the_record_cannot_hold_is_refused(portfolio):
    with pytest.raises(FactoryError, match="record-shape"):
        forward_record({"stages": {"bs": load_stage(str(ROOT / BUFFER_STOCK))}, "connectors": []})
    death = elaborate_stage(load_stage(str(ROOT / RETIREE_DEATH)))
    with pytest.raises(NotConstructed, match="the forward measures are not constructed"):
        forward_record({"stages": {"rd": death}, "connectors": []})
    with pytest.raises(ValueError, match="no inter-period mapping"):
        forward_record(portfolio["periods"][1], to=portfolio["periods"][0])


def test_item_5_asva_computes_the_transition_and_its_fixed_point_from_the_record():
    forward = pytest.importorskip("asva.forward")
    record = forward_record(_buffer_stock(), {"a": "k"})
    table = forward.product_table(SHOCKS)
    shocks, policies = {("bs", "arvl_to_dcsn"): table}, {("bs", "c"): _consumption}
    nodes = np.concatenate([[0.0], np.geomspace(1e-6, 30.0, 200)])
    transition = forward.transition(record, {("bs", "a"): nodes}, shocks, policies)

    # the two laws of the stage file written out: m = R*k/(Γ*ψ) + ξ, a = m - c
    count = nodes.size
    written = np.zeros((count, count))
    for weight, psi, xi in zip(table["weights"], table["nodes"]["ψ"], table["nodes"]["ξ"]):
        m = 1.03 * nodes / (1.01 * psi) + xi
        j, low, high = forward.lottery(nodes, m - _consumption(m))
        np.add.at(written, (j, np.arange(count)), weight * low)
        np.add.at(written, (j + 1, np.arange(count)), weight * high)
    assert np.abs(transition.toarray() - written).max() < 1e-15

    found = forward.stationary(transition)
    assert found.converged and found.change < 1e-13 and found.mass.sum() == pytest.approx(1.0)
    ahead = forward.one_period_ahead(
        record, forward.Atoms({("bs", "a"): nodes}, found.mass), shocks, policies, at="leaving")
    assert np.abs(forward.measure_on_grid({("bs", "a"): nodes}, ahead) - found.mass).max() < 1e-13


def test_item_6_death_and_birth_stated_in_a_stage_give_the_stationary_measure_of_a_survivors_share_and_entrants():
    forward = pytest.importorskip("asva.forward")
    buffer_stock = _buffer_stock()["stages"]["bs"]
    mortality = elaborate_text(MORTALITY, "mortality.bl")
    mortality.calibrate({"calibration": {"ℒ": 0.99, "k_0": 0.5}})
    period = {"stages": {"bs": buffer_stock, "mort": mortality}, "connectors": [{"a": "a_end"}]}
    record = forward_record(period, {"k_next": "k"})
    assert record.closed() and record.joins == ((("bs", "a"), ("mort", "a_end")),)
    assert record.needs()["shocks"][("mort", "arvl_to_dcsn")] == ("s",)
    event = record.steps[2].shocks[0]
    assert (event.family, event.set, event.parameter_values) == ("Categorical", "Life", (0.99,))

    table = forward.product_table(SHOCKS)
    life = {"nodes": {"s": np.array(["survive", "die"])}, "weights": np.array([0.99, 0.01])}
    policies = {("bs", "c"): _consumption}
    nodes = np.concatenate([[0.0], np.geomspace(1e-6, 30.0, 200)])
    whole = forward.transition(
        record, {("mort", "k_next"): nodes}, {("bs", "arvl_to_dcsn"): table, ("mort", "arvl_to_dcsn"): life},
        policies)
    in_a_stage = forward.stationary(whole)
    assert in_a_stage.method == "power-iteration" and in_a_stage.converged

    alone = forward_record({"stages": {"bs": buffer_stock}, "connectors": []}, {"a": "k"})
    grid = {("bs", "a"): nodes}
    survivors = forward.transition(alone, grid, {("bs", "arvl_to_dcsn"): table}, policies)
    newborns = (forward.Atoms({("bs", "a"): np.array([0.5])}, np.array([1.0])), "leaving")
    as_arguments = forward.stationary(
        survivors, forward.entrants_on_grid(alone, grid, newborns), survival=0.99)
    assert as_arguments.method.startswith("linear-solve")
    assert np.abs(in_a_stage.mass - as_arguments.mass).max() < 1e-12
