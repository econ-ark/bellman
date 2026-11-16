"""A period: the joins of its stages, the forward and backward orders, and the
forward record."""

import numpy as np
import pytest
from application_files import BUFFER_STOCK_FILE, BUFFER_STOCK_METHODS, PORTFOLIO, ROOT
from skips import require_package
from stage_texts import corpus_text

from bellman.period import (
    ForwardRecord,
    backward_order,
    computable_together,
    forward_order,
    forward_record,
    period_joins,
)
from bellman.refusals import FactoryError, NotConstructed
from bellman.stage import elaborate_stage, elaborate_text, load_stage
from bellman.trellis import connection_report, elaborate_trellis, load_recipe

# a calibration of the buffer-stock stage that differs from
# `BUFFER_STOCK_BASELINE_CALIBRATION` of application_files.py in the growth
# factor alone, Γ = 1.01 in place of 1.03
BUFFER_STOCK_CALIBRATION_AT_GROWTH_1_01 = {
    "β": 0.96,
    "ρ": 2.0,
    "R": 1.03,
    "Γ": 1.01,
    "σ_ψ": 0.1,
    "σ_ξ": 0.1,
    "p_zero": 0.005,
}


# a stage that ends a period: the household survives and keeps its assets, or
# dies and is replaced by a newborn
MORTALITY = """@stage: mortality

Xa := ℝ₊₊
Life := {survive, die}  :: ["the household survives the period, or dies and a newborn replaces it"]

ℒ : (0,1]        :: ["probability of surviving into the next period"]
k_0 : ℝ₊₊        :: ["assets of a newborn"]

s : Life
s ~ Categorical((ℒ, 1 - ℒ))     :: ["surviving or dying, with probabilities in label order"]

[id=arvl_to_dcsn, (a_end : Xa, s) : !arvl -> (b : Xa) : !dcsn] {
    b = (a_end, k_0)[s]           :: [id=assets_kept_or_endowed]
}

[id=dcsn_to_cntn, (b) : !dcsn -> (k_next : Xa) : !cntn] {
    k_next = b                    :: [id=carried]
}
"""


# the two shocks of the buffer-stock stage on three points each: the nodes and
# their weights
DISCRETE_SHOCKS = {
    "ψ": (np.array([0.9, 1.0, 1.1]), np.array([0.25, 0.5, 0.25])),
    "ξ": (np.array([0.0, 0.8, 1.2]), np.array([0.005, 0.4975, 0.4975])),
}


# the grid of saving: zero and 200 points spaced geometrically on [1e-6, 30]
SAVING_NODES = np.concatenate([[0.0], np.geomspace(1e-6, 30.0, 200)])


# the phrases of the refusal of the cycle that two connectors close between
# port and cons
CYCLE_PHRASES = ("port continues to 'm_next'", "cons arrives at 'm'", "'a'", "'k'")


def consumption(m):
    """A consumption rule given by hand, which the forward record leaves to
    the user."""
    return 0.25 * m + 0.05 * m / (1.0 + m)


def buffer_stock_period(calibrated=True):
    """A period of the buffer-stock stage alone, with its methods file, under
    the key `bs`; its stage is calibrated unless `calibrated` is False."""
    stage = elaborate_stage(
        load_stage(str(ROOT / BUFFER_STOCK_FILE), [str(ROOT / BUFFER_STOCK_METHODS)])
    )
    if calibrated:
        stage.calibrate({"calibration": BUFFER_STOCK_CALIBRATION_AT_GROWTH_1_01})
    return {"stages": {"bs": stage}, "connectors": []}


@pytest.fixture(scope="module")
def portfolio():
    """The trellis of the portfolio application,
    `applications/portfolio-choice`, elaborated from its recipe."""
    return elaborate_trellis(load_recipe(PORTFOLIO, "spec.yml"))


@pytest.fixture(scope="module")
def connected_period(cons, port):
    """A period of port and cons whose connector joins the continuation field
    m_next of port to the arrival field m of cons."""
    return {"stages": {"cons": cons, "port": port}, "connectors": [{"m_next": "m"}]}


@pytest.fixture(scope="module")
def calibrated_period():
    """The period of the buffer-stock stage, calibrated."""
    return buffer_stock_period()


@pytest.fixture(scope="module")
def buffer_stock_record(calibrated_period):
    """The forward record of the calibrated buffer-stock period, with no
    inter-period mapping."""
    return forward_record(calibrated_period)


@pytest.fixture(scope="module")
def closed_record(calibrated_period):
    """The forward record of the calibrated buffer-stock period joined to
    itself by the inter-period mapping from its saving a to its arrival
    field k."""
    return forward_record(calibrated_period, {"a": "k"})


@pytest.fixture(scope="module")
def record_joined_to_the_following_period(portfolio):
    """The forward record of `periods[1]` of the trellis of the portfolio
    application, joined by the inter-period mapping of the trellis to
    `periods[0]`, the period that follows it in time."""
    period, following_period = portfolio["periods"][1], portfolio["periods"][0]
    return forward_record(
        period, portfolio["inter_connectors"][0], to=following_period, address="periods[1]"
    )


@pytest.fixture(scope="module")
def mortality_period(calibrated_period):
    """A period of the calibrated buffer-stock stage followed by the
    calibrated mortality stage, the saving a of the one joined to the arrival
    field a_end of the other."""
    mortality = elaborate_text(MORTALITY, "mortality.bl")
    mortality.calibrate({"calibration": {"ℒ": 0.99, "k_0": 0.5}})
    return {
        "stages": {"bs": calibrated_period["stages"]["bs"], "mort": mortality},
        "connectors": [{"a": "a_end"}],
    }


@pytest.fixture(scope="module")
def mortality_record(mortality_period):
    """The forward record of the period with the mortality stage, joined to
    itself by the inter-period mapping from k_next to k."""
    return forward_record(mortality_period, {"k_next": "k"})


@pytest.fixture(scope="module")
def asva_forward():
    """The module `asva.forward`, which computes transitions from a forward
    record; a test that reads it is skipped where asva is not installed."""
    return require_package("asva.forward")


@pytest.fixture(scope="module")
def buffer_stock_transition(asva_forward, closed_record):
    """The transition that asva computes from the closed record of the
    buffer-stock period on the grid of saving, with the discrete shocks and
    the consumption rule."""
    return asva_forward.transition(
        closed_record,
        {("bs", "a"): SAVING_NODES},
        {("bs", "arvl_to_dcsn"): asva_forward.product_table(DISCRETE_SHOCKS)},
        {("bs", "c"): consumption},
    )


def test_a_period_without_connectors_joins_no_fields_whose_names_differ(cons, port):
    """Port continues to m_next and cons arrives at m, so without a connector
    no field is joined and both continuation fields leave the period."""
    assert period_joins({"stages": {"cons": cons, "port": port}, "connectors": []}) == {
        "joins": [],
        "outputs": [("cons", "a"), ("port", "m_next")],
    }


def test_a_connector_joins_the_continuation_field_to_the_arrival_field_it_names(
    connected_period,
):
    """The connector {m_next: m} joins m_next of port to m of cons, and only
    the saving a of cons leaves the period."""
    assert period_joins(connected_period)["joins"] == [
        {"from": ("port", "m_next"), "to": ("cons", "m")}
    ]
    assert period_joins(connected_period)["outputs"] == [("cons", "a")]


@pytest.mark.parametrize(
    "listed",
    [
        pytest.param(("cons", "port"), id="cons listed first"),
        pytest.param(("port", "cons"), id="port listed first"),
    ],
)
def test_the_forward_order_of_a_period_follows_its_joins_in_either_listing(listed, cons, port):
    """The forward order puts port before cons, whose arrival field the
    connector joins to port, whichever stage the period lists first."""
    stages = {"cons": cons, "port": port}
    period = {"stages": {key: stages[key] for key in listed}, "connectors": [{"m_next": "m"}]}
    assert forward_order(period) == ["port", "cons"]


def test_the_backward_order_of_a_period_reverses_the_order_of_its_joins(connected_period):
    """The backward order puts cons, the stage that the connector joins to
    port, before port."""
    assert backward_order(connected_period) == ["cons", "port"]


def test_the_joins_of_a_period_do_not_depend_on_the_order_of_its_stages(
    connected_period, cons, port
):
    """A period that lists port before cons has the joins and the outputs of
    the period that lists cons first."""
    listed_the_other_way = {
        "stages": {"port": port, "cons": cons},
        "connectors": [{"m_next": "m"}],
    }
    assert period_joins(listed_the_other_way) == {
        "joins": [{"from": ("port", "m_next"), "to": ("cons", "m")}],
        "outputs": [("cons", "a")],
    }
    assert period_joins(listed_the_other_way) == period_joins(connected_period)


def test_computable_together_gives_the_layers_of_stages_that_the_joins_order(connected_period):
    """Port and cons stand in two layers, port first, since the connector joins
    port to cons."""
    assert computable_together(connected_period) == [["port"], ["cons"]]


def test_a_keyed_connector_restating_an_equal_name_pair_gives_the_one_join_of_equal_names(cons):
    """A connector written as {from, to, fields} that restates the pair that
    equal names would join gives that one join, the joins of the period
    without the connector."""
    # a copy of port that continues to m, so that equal names join it to cons
    port_to_m = elaborate_text(corpus_text("port").replace("m_next", "m"), "port.bl")
    written = {
        "stages": {"cons": cons, "port": port_to_m},
        "connectors": [{"from": "port", "to": "cons", "fields": {"m": "m"}}],
    }
    assert period_joins(written, "periods[0]")["joins"] == [
        {"from": ("port", "m"), "to": ("cons", "m")}
    ]
    assert period_joins({**written, "connectors": []}, "periods[0]") == period_joins(
        written, "periods[0]"
    )


def test_a_connector_naming_no_declared_field_is_no_refusal_but_an_unresolved_endpoint(cons):
    """A connector that names a field that no stage declares makes no join and
    no refusal, and the connection report of the trellis names its endpoint as
    unresolved."""
    named = {"stages": {"cons": cons}, "connectors": [{"a": "q"}]}
    assert period_joins(named, "periods[0]") == {"joins": [], "outputs": [("cons", "a")]}
    trellis = elaborate_trellis({"periods": [named], "inter_connectors": []})
    (diagnostic,) = connection_report(trellis).diagnostics
    assert (diagnostic.rule, diagnostic.address) == (
        "endpoint-unresolved",
        "periods[0].connectors[0]",
    )
    assert [phrase for phrase in ("'q'", "m") if phrase not in diagnostic.message] == []


def test_a_cycle_closed_by_two_connectors_is_refused_by_forward_order(cons, port):
    """Two connectors that join the saving a of cons to k of port and m_next
    of port to m of cons close a cycle, which forward_order refuses, naming
    both joins and what the author can do."""
    connectors = [{"a": "k"}, {"m_next": "m"}]
    with pytest.raises(FactoryError) as refused:
        forward_order(
            {"stages": {"cons": cons, "port": port}, "connectors": connectors}, "periods[0]"
        )
    assert (
        refused.value.rule == "period-join-cycle"
        and "remove or redirect an authored connector" in refused.value.write
    )
    assert [phrase for phrase in CYCLE_PHRASES if phrase not in refused.value.message] == []


def test_period_joins_refuses_a_period_of_stage_records_that_are_not_elaborated():
    """A period as a recipe holds it, a record of each stage's text, has no
    fields, so period_joins refuses it and names elaborate_trellis."""
    record = {"stage": {"text": "", "origin": "cons.bl"}}
    with pytest.raises(FactoryError, match="elaborate_trellis") as refused:
        period_joins({"stages": {"cons": record}, "connectors": []}, "periods[0]")
    assert (refused.value.rule, refused.value.address) == (
        "record-shape",
        "periods[0].stages['cons']",
    )


def test_a_connector_that_joins_a_stage_to_itself_is_refused_by_forward_order_alone(cons):
    """A connector from the saving a of cons to its own arrival field m makes
    no join of period_joins, and forward_order refuses it as a cycle."""
    self_pair = {"stages": {"cons": cons}, "connectors": [{"a": "m"}]}
    assert period_joins(self_pair, "periods[0]")["joins"] == []
    with pytest.raises(FactoryError) as refused:
        forward_order(self_pair, "periods[0]")
    assert (
        refused.value.rule == "period-join-cycle"
        and "cons" in refused.value.message
        and "'a'" in refused.value.message
    )


def test_two_connectors_mapping_one_continuation_field_are_refused_by_forward_order_alone(
    cons, port
):
    """Two connectors that map the saving a of cons to k of port give one join
    of period_joins, and forward_order refuses the second connector."""
    duplicate = {"stages": {"cons": cons, "port": port}, "connectors": [{"a": "k"}, {"a": "k"}]}
    assert period_joins(duplicate, "periods[0]")["joins"] == [
        {"from": ("cons", "a"), "to": ("port", "k")}
    ]
    with pytest.raises(FactoryError) as refused:
        forward_order(duplicate, "periods[0]")
    assert (
        "periods[0].connectors[0] and periods[0].connectors[1] both map the continuation field "
        "'a' of cons" in refused.value.message
    )
    assert (refused.value.rule, refused.value.address) == (
        "connector-names-no-field",
        "periods[0].connectors[1]",
    )


def test_a_keyed_connector_with_a_key_beside_from_to_and_fields_is_refused(cons, port):
    """A connector written as {from, to, fields} with a fourth key, label, is
    refused, naming the key."""
    connector = {"from": "cons", "to": "port", "fields": {"a": "k"}, "label": "x"}
    with pytest.raises(FactoryError) as refused:
        period_joins(
            {"stages": {"cons": cons, "port": port}, "connectors": [connector]}, "periods[0]"
        )
    assert "'label'" in refused.value.message and refused.value.rule == "connector-names-no-field"


def test_forward_record_answers_a_forward_record_named_for_the_period_of_its_stages(
    buffer_stock_record,
):
    """The record of a period with no address is a ForwardRecord named for the
    keys of its stages."""
    assert isinstance(buffer_stock_record, ForwardRecord)
    assert buffer_stock_record.period == "the period of bs"


def test_the_printed_record_names_its_period_the_policy_to_be_given_and_the_draws(
    buffer_stock_record,
):
    """The printed record opens with its period and states the policy that the
    user gives and the law of each draw."""
    printed = str(buffer_stock_record)
    assert printed.startswith("forward record of the period of bs")
    phrases = ("policy    c(m), to be given", "draws     ψ ~ LogNormal")
    assert [phrase for phrase in phrases if phrase not in printed] == []


def test_the_arrival_step_names_its_builder_and_the_perches_it_joins(buffer_stock_record):
    """The first step of the record is the forward builder arvl_to_dcsn of bs,
    from the arrival perch to the decision perch."""
    arrival, _ = buffer_stock_record.steps
    assert (arrival.stage, arrival.builder, arrival.source, arrival.target) == (
        "bs",
        "arvl_to_dcsn",
        "arvl",
        "dcsn",
    )


def test_the_arrival_step_reads_the_state_and_the_shocks_and_writes_the_decision_state(
    buffer_stock_record,
):
    """The arrival step reads the state k and the shocks ψ and ξ, chooses
    nothing, and writes the decision state m."""
    arrival, _ = buffer_stock_record.steps
    assert arrival.states == ("k",) and arrival.controls == () and arrival.writes == ("m",)
    assert arrival.arguments == ("k", "ψ", "ξ") and arrival.roles == ("state", "shock", "shock")


def test_the_arrival_step_holds_its_parameters_with_their_calibrated_values(buffer_stock_record):
    """The arrival step reads the parameters R and Γ and holds the values of
    the calibration."""
    arrival, _ = buffer_stock_record.steps
    assert (arrival.parameters, arrival.parameter_values) == (("R", "Γ"), (1.03, 1.01))


def test_the_function_of_the_arrival_step_computes_the_law_of_motion_of_the_stage(
    buffer_stock_record,
):
    """The function of the arrival step computes m = R·k/(Γ·ψ) + ξ at the
    values of R and Γ that the step holds."""
    arrival, _ = buffer_stock_record.steps
    # the arguments k, ψ and ξ, then the values of R and Γ:
    # m = 1.03 · 2 / (1.01 · 1) + 0.5
    assert arrival.function(2.0, 1.0, 0.5, *arrival.parameter_values) == 1.03 * 2.0 / 1.01 + 0.5


def test_the_permanent_shock_of_the_record_holds_its_law_and_its_calibrated_arguments(
    buffer_stock_record,
):
    """The permanent shock ψ of the arrival step is drawn alone from its
    lognormal law, whose arguments and parameter the record holds at the
    calibration."""
    arrival, _ = buffer_stock_record.steps
    permanent, _ = arrival.shocks
    assert (permanent.name, permanent.set, permanent.family) == ("ψ", "ℝ₊₊", "LogNormal")
    assert permanent.law == "LogNormal(-σ_ψ^2/2, σ_ψ)" and permanent.jointly == ("ψ",)
    assert permanent.argument_values == pytest.approx((-0.005, 0.1))
    assert (permanent.parameters, permanent.parameter_values) == (("σ_ψ",), (0.1,))


def test_the_transitory_shock_reads_a_derived_parameter_whose_value_the_record_holds(
    buffer_stock_record,
):
    """The law of the transitory shock ξ, a mixture, reads the derived
    parameter μ_ξ, and the record holds its value beside those of p_zero and
    σ_ξ."""
    arrival, _ = buffer_stock_record.steps
    _, transitory = arrival.shocks
    assert transitory.family == "Mixture" and transitory.parameters == ("p_zero", "μ_ξ", "σ_ξ")
    # μ_ξ = −log(1 − p_zero) − σ_ξ²/2
    assert transitory.parameter_values == pytest.approx(
        (0.005, -np.log(1 - 0.005) - 0.1**2 / 2, 0.1)
    )


def test_the_decision_step_reads_the_state_and_the_control_and_writes_the_saving(
    buffer_stock_record,
):
    """The decision step reads the state m and the control c, draws nothing,
    and writes the saving a, the output a≻ of its function."""
    _, decision = buffer_stock_record.steps
    assert decision.states == ("m",) and decision.shocks == () and decision.writes == ("a",)
    assert decision.arguments == ("m", "c") and decision.roles == ("state", "control")
    assert decision.outputs == ("a≻",)


def test_the_control_of_the_decision_step_is_read_at_the_decision_state(buffer_stock_record):
    """The one control c of the decision step lies in ℝ₊₊ and is read at the
    decision state m."""
    _, decision = buffer_stock_record.steps
    (control,) = decision.controls
    assert (control.name, control.set, control.read_at) == ("c", "ℝ₊₊", ("m",))


def test_the_function_of_the_decision_step_computes_the_saving(buffer_stock_record):
    """The function of the decision step computes the saving a = m − c."""
    # the arguments m and c: a = 3 − 1
    _, decision = buffer_stock_record.steps
    assert decision.function(3.0, 1.0) == 2.0


def test_needs_lists_the_shocks_and_the_policies_that_a_calibrated_record_needs(
    buffer_stock_record,
):
    """The record of a calibrated period needs the draws of ψ and ξ and the
    policy c(m), and no parameter."""
    assert buffer_stock_record.needs() == {
        "shocks": {("bs", "arvl_to_dcsn"): ("ψ", "ξ")},
        "policies": {("bs", "c"): ("m",)},
        "parameters": [],
    }


def test_a_record_of_an_uncalibrated_period_needs_its_parameters():
    """The record of a period that is not calibrated holds no parameter
    values, and needs lists the parameters R and Γ of the arrival step."""
    symbolic = forward_record(buffer_stock_period(calibrated=False))
    assert (
        symbolic.steps[0].parameter_values is None
        and symbolic.steps[0].shocks[0].parameter_values is None
    )
    assert symbolic.needs()["parameters"] == [
        ("bs", "arvl_to_dcsn", "R"),
        ("bs", "arvl_to_dcsn", "Γ"),
    ]


def test_the_record_names_the_arrival_and_leaving_fields_of_the_period_with_their_sets(
    closed_record,
):
    """The record names k, the field at which the period is entered, and a,
    the field at which it is left, each with its stage and its set."""
    assert closed_record.arrival == (("bs", "k", "Xa"),) and closed_record.leaving == (
        ("bs", "a", "Xa"),
    )


def test_a_record_is_closed_when_an_inter_period_mapping_joins_the_period_to_itself(
    calibrated_period, closed_record
):
    """The mapping {a: k} joins the period to itself and closes the record,
    and the record of the same period without a mapping is open."""
    assert (
        closed_record.connector == ((("bs", "a"), ("bs", "k")),)
        and closed_record.joined_to == "itself"
    )
    assert closed_record.closed()
    alone = forward_record(calibrated_period)
    assert alone.connector == () and alone.joined_to is None and not alone.closed()


def test_a_period_of_several_stages_is_recorded_in_its_forward_order(
    record_joined_to_the_following_period,
):
    """The steps of a period of port, cons and disc follow the forward order,
    each stage's two forward builders in turn."""
    assert [
        (step.stage, step.builder) for step in record_joined_to_the_following_period.steps
    ] == [
        ("port", "arvl_to_dcsn"),
        ("port", "dcsn_to_cntn"),
        ("cons", "arvl_to_dcsn"),
        ("cons", "dcsn_to_cntn"),
        ("disc", "arvl_to_dcsn"),
        ("disc", "dcsn_to_cntn"),
    ]


def test_the_record_of_a_period_of_several_stages_holds_its_joins(
    record_joined_to_the_following_period,
):
    """The record holds the two joins of the period, from port to cons and
    from cons to disc."""
    assert set(record_joined_to_the_following_period.joins) == {
        (("port", "m_next"), ("cons", "m")),
        (("cons", "a"), ("disc", "a")),
    }


def test_the_record_of_a_period_of_several_stages_names_its_arrival_and_leaving_fields(
    record_joined_to_the_following_period,
):
    """The period is entered at k of port and l of cons and left at a of
    disc."""
    assert [field[:2] for field in record_joined_to_the_following_period.arrival] == [
        ("port", "k"),
        ("cons", "l"),
    ]
    assert record_joined_to_the_following_period.leaving == (("disc", "a", "Xa"),)


def test_the_record_of_a_period_names_the_connector_to_the_period_that_follows_it(
    record_joined_to_the_following_period,
):
    """The record of `periods[1]` names its address, the inter-period mapping
    from a of `disc` to k of `port`, and `periods[0]`, the period that follows
    it in time and that it joins, by the keys of its stages."""
    assert record_joined_to_the_following_period.connector == ((("disc", "a"), ("port", "k")),)
    assert (
        record_joined_to_the_following_period.period,
        record_joined_to_the_following_period.joined_to,
    ) == (
        "periods[1]",
        "the period of port, cons, disc",
    )


def test_one_declaration_draws_the_two_shocks_of_port_together(
    record_joined_to_the_following_period,
):
    """The risky return Ψ and the labour income θ of port are drawn together by
    one law."""
    risky, labour = record_joined_to_the_following_period.steps[1].shocks
    assert risky.jointly == labour.jointly == ("Ψ", "θ") and risky.law == labour.law


def test_the_record_of_the_portfolio_period_needs_a_policy_for_each_control(
    record_joined_to_the_following_period,
):
    """The record needs the share ς of port at k_d and the consumption c of
    cons at m_d."""
    assert record_joined_to_the_following_period.needs()["policies"] == {
        ("port", "ς"): ("k_d",),
        ("cons", "c"): ("m_d",),
    }


def test_a_mapping_that_reaches_one_arrival_field_of_two_leaves_the_record_open(portfolio):
    """Joined to itself, the mapping of the portfolio trellis reaches k of port
    and not l of cons, so the record is not closed."""
    record = forward_record(portfolio["periods"][1], portfolio["inter_connectors"][0])
    assert record.joined_to == "itself"
    assert [field[:2] for field in record.arrival] == [("port", "k"), ("cons", "l")]
    assert not record.closed()


def test_a_stage_with_no_arrival_perch_is_entered_at_its_decision_perch(ez_savings):
    """The one step of a period of ez_savings, which declares no arrival
    perch, goes from the decision perch to the continuation perch, and the
    period is entered at its decision states."""
    record = forward_record({"stages": {"ez": ez_savings}, "connectors": []})
    (step,) = record.steps
    assert (step.source, step.target) == ("dcsn", "cntn")
    assert {field[1] for field in record.arrival} == set(step.states)


def test_forward_record_refuses_a_period_of_a_stage_that_is_not_elaborated():
    """A period whose stage is the record that load_stage reads, not an
    elaborated stage, is refused under the rule record-shape."""
    with pytest.raises(FactoryError, match="record-shape"):
        forward_record(
            {"stages": {"bs": load_stage(str(ROOT / BUFFER_STOCK_FILE))}, "connectors": []}
        )


def test_forward_record_refuses_a_stage_whose_forward_measures_are_not_constructed(
    retiree_death,
):
    """A period of retiree_death, whose forward builders the package does not
    construct, is refused."""
    with pytest.raises(NotConstructed, match="the forward measures are not constructed"):
        forward_record({"stages": {"rd": retiree_death}, "connectors": []})


def test_forward_record_refuses_a_following_period_given_without_an_inter_period_mapping(
    portfolio,
):
    """A period given as `to`, the period that follows in time, without an
    inter-period mapping is refused."""
    with pytest.raises(ValueError, match="no inter-period mapping"):
        forward_record(portfolio["periods"][1], to=portfolio["periods"][0])


def test_the_transition_from_the_record_is_the_matrix_of_the_laws_of_the_stage_file(
    asva_forward, buffer_stock_transition
):
    """The transition that asva computes from the closed record equals the
    matrix of the two laws of the stage file written out, the mass at each
    saving split between its two neighbouring nodes of the grid."""
    table = asva_forward.product_table(DISCRETE_SHOCKS)
    # the two laws of the stage file written out: m = R*k/(Γ*ψ) + ξ, a = m - c
    count = SAVING_NODES.size
    written = np.zeros((count, count))
    for weight, psi, xi in zip(table["weights"], table["nodes"]["ψ"], table["nodes"]["ξ"]):
        m = 1.03 * SAVING_NODES / (1.01 * psi) + xi
        j, low, high = asva_forward.lottery(SAVING_NODES, m - consumption(m))
        np.add.at(written, (j, np.arange(count)), weight * low)
        np.add.at(written, (j + 1, np.arange(count)), weight * high)
    assert np.abs(buffer_stock_transition.toarray() - written).max() < 1e-15


def test_the_stationary_measure_of_the_transition_converges_to_a_probability_measure(
    asva_forward, buffer_stock_transition
):
    """The stationary measure of the transition converges, and its masses sum
    to one."""
    found = asva_forward.stationary(buffer_stock_transition)
    assert found.converged and found.change < 1e-13 and found.mass.sum() == pytest.approx(1.0)


def test_the_stationary_measure_is_its_own_measure_one_period_ahead(
    asva_forward, closed_record, buffer_stock_transition
):
    """The measure one period ahead of the stationary measure, on the grid of
    saving, is the stationary measure."""
    found = asva_forward.stationary(buffer_stock_transition)
    assert found.converged and found.mass.sum() == pytest.approx(1.0)
    shocks = {("bs", "arvl_to_dcsn"): asva_forward.product_table(DISCRETE_SHOCKS)}
    ahead = asva_forward.one_period_ahead(
        closed_record,
        asva_forward.Atoms({("bs", "a"): SAVING_NODES}, found.mass),
        shocks,
        {("bs", "c"): consumption},
        at="leaving",
    )
    on_grid = asva_forward.measure_on_grid({("bs", "a"): SAVING_NODES}, ahead)
    assert np.abs(on_grid - found.mass).max() < 1e-13


def test_a_connector_joins_the_saving_of_buffer_stock_to_the_mortality_stage(mortality_record):
    """The connector {a: a_end} joins the saving a of bs to the arrival field
    a_end of the mortality stage."""
    assert mortality_record.joins == ((("bs", "a"), ("mort", "a_end")),)


def test_the_inter_period_mapping_closes_the_record_of_the_period_with_mortality(
    mortality_record,
):
    """The mapping {k_next: k} joins the continuation field of the mortality
    stage to the arrival field of bs and closes the record."""
    assert mortality_record.closed()


def test_the_record_needs_a_draw_of_the_label_shock_of_the_mortality_stage(mortality_record):
    """The record needs the draw of s at the arrival builder of the mortality
    stage."""
    assert mortality_record.needs()["shocks"][("mort", "arvl_to_dcsn")] == ("s",)


def test_the_label_shock_of_the_mortality_stage_is_categorical_on_life_with_its_weight(
    mortality_record,
):
    """The shock s of the mortality stage is drawn from a categorical law on
    Life whose weight is the calibrated probability of surviving."""
    event = mortality_record.steps[2].shocks[0]
    assert (event.family, event.set, event.parameter_values) == ("Categorical", "Life", (0.99,))


def test_death_in_a_stage_gives_the_stationary_measure_of_a_survival_share_and_entrants(
    asva_forward, closed_record, mortality_record
):
    """The stationary measure of the period with the mortality stage, found by
    power iteration, equals the measure that a survival share of 0.99 and
    newborns at assets 0.5 give by a linear solve."""
    table = asva_forward.product_table(DISCRETE_SHOCKS)
    life = {"nodes": {"s": np.array(["survive", "die"])}, "weights": np.array([0.99, 0.01])}
    policies = {("bs", "c"): consumption}
    whole = asva_forward.transition(
        mortality_record,
        {("mort", "k_next"): SAVING_NODES},
        {("bs", "arvl_to_dcsn"): table, ("mort", "arvl_to_dcsn"): life},
        policies,
    )
    in_a_stage = asva_forward.stationary(whole)
    assert in_a_stage.method == "power-iteration" and in_a_stage.converged

    # the buffer-stock period alone, joined to itself, and the newborns as
    # entrants at its leaving field
    grid = {("bs", "a"): SAVING_NODES}
    survivors = asva_forward.transition(
        closed_record, grid, {("bs", "arvl_to_dcsn"): table}, policies
    )
    # the newborns: a mass of one at the saving 0.5, entering at the leaving
    # field
    newborns = (asva_forward.Atoms({("bs", "a"): np.array([0.5])}, np.array([1.0])), "leaving")
    as_arguments = asva_forward.stationary(
        survivors, asva_forward.entrants_on_grid(closed_record, grid, newborns), survival=0.99
    )
    assert as_arguments.method.startswith("linear-solve")
    assert np.abs(in_a_stage.mass - as_arguments.mass).max() < 1e-12
