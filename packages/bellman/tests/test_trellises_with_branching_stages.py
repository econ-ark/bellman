"""Trellises with branching stages: the registries of four applications and of
the childbearing model elaborated as whole trellises with their joins, a
period of the model of Cagetti and De Nardi (2006), which this file calls the
Cagetti–De Nardi model afterwards, with its entrepreneur stages stood in, and
periods of one branching stage placed by hand."""

import copy
import hashlib
import importlib.util
from collections import Counter

import pytest
from application_files import (
    BRANCHING_EXAMPLES_FOLDER,
    COPIED_FILES_FOLDER,
    DURABLES,
    HOUSING,
    PENSION,
    RETIREMENT,
    ROOT,
)
from printed_text import (
    card_section_lines,
    card_shown_on_the_page,
    differing_card_sections,
    flat,
    operations_entries,
)

from bellman.factory.trellis import positions
from bellman.period import computable_together, period_joins
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.stage_answers import fields
from bellman.trellis import (
    accrete,
    assemble_trellis,
    calibrate_trellis,
    configure_trellis,
    elaborate_trellis,
    inter_period_joins,
    load_recipe,
    methodize_trellis,
)

CHILDBEARING_EXAMPLE = BRANCHING_EXAMPLES_FOLDER / "examples/de-la-croix-pommeret-2021/expected.md"


# the registry of the Cagetti–De Nardi model; the package refuses its two
# entrepreneur stages, which the tests stand in by stages of their own
CAGETTI_DE_NARDI_REGISTRY = BRANCHING_EXAMPLES_FOLDER / "examples/cagetti-denardi-2006/registry"


# the registry of the childbearing model of de la Croix and Pommeret (2021)
CHILDBEARING = ROOT / COPIED_FILES_FOLDER / "de-la-croix-pommeret-2021"


def arrow(join):
    """A join written `stage:field → stage:field`."""
    return f"{join['from'][0]}:{join['from'][1]} → {join['to'][0]}:{join['to'][1]}"


def wage_schedule_writer():
    """The function of the durables application that writes the wage schedule
    of each period into a recipe, read from the code folder of the
    application."""
    spec = importlib.util.spec_from_file_location(
        "durables_wage_schedule", DURABLES.parent / "code/wage_schedule.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.write_wage_schedule


# the joins within each period other than the terminal period, in each
# registry: the branches of tenure and of house_choice join the decision
# states of the stages they enter, which declare no arrival perch
DURABLES_WITHIN = [
    "tenure:h_kp → keeper_cons:h_d",
    "tenure:w_adj → adjuster_cons:m",
    "tenure:w_kp → keeper_cons:w_d",
    "tenure:z_adj → adjuster_cons:z_d",
    "tenure:z_kp → keeper_cons:z_d",
]


RETIREMENT_WITHIN = ["ret_choice:a_r → retiree_cons:a_ret", "ret_choice:a_w → worker_cons:a_w"]


PENSION_WITHIN = ["worker_saving:y_f → retire_choice:y_f", "worker_saving:y_p → retire_choice:y_p"]


HOUSING_WITHIN = [
    "house_choice:h_kp → keeper_saving:h_d",
    "house_choice:w_adj → adjuster_saving:m",
    "house_choice:w_kp → keeper_saving:m_d",
]


# for each registry: the number of periods and of stage occurrences; the joins
# and the layers of the terminal period; the joins, the outputs and the layers
# of each period other than the terminal period; and the inter-period joins of
# each pair of periods
REGISTRIES = [
    pytest.param(
        "durables_trellis_with_wage_schedule",
        dict(
            n=51,
            occurrences=154,
            terminal=sorted(
                [
                    f"{s}:{f}_nxt_{t} → bequest:{f}_bq"
                    for s, t in (("adjuster_cons", "adj"), ("keeper_cons", "kp"))
                    for f in "ahz"
                ]
            )
            + DURABLES_WITHIN,
            layers=[["tenure"], ["adjuster_cons", "keeper_cons"], ["bequest"]],
            within=DURABLES_WITHIN,
            outputs=[
                "adjuster_cons:a_nxt_adj",
                "adjuster_cons:h_nxt_adj",
                "adjuster_cons:z_nxt_adj",
                "keeper_cons:a_nxt_kp",
                "keeper_cons:h_nxt_kp",
                "keeper_cons:z_nxt_kp",
            ],
            later=[["tenure"], ["adjuster_cons", "keeper_cons"]],
            inter=[
                f"{s}:{f}_nxt_{t} → tenure:{f}"
                for s, t in (("keeper_cons", "kp"), ("adjuster_cons", "adj"))
                for f in "ahz"
            ],
        ),
        id="durables",
    ),
    pytest.param(
        "housing_frictions_trellis",
        dict(
            n=60,
            occurrences=181,
            terminal=sorted(
                [
                    f"{s}:y_{f}_{t} → terminal:y_{f}_T"
                    for s, t in (("adjuster_saving", "adj"), ("keeper_saving", "kp"))
                    for f in "fh"
                ]
                + HOUSING_WITHIN
            ),
            layers=[["house_choice"], ["adjuster_saving", "keeper_saving"], ["terminal"]],
            within=HOUSING_WITHIN,
            outputs=[
                "adjuster_saving:y_f_adj",
                "adjuster_saving:y_h_adj",
                "keeper_saving:y_f_kp",
                "keeper_saving:y_h_kp",
            ],
            later=[["house_choice"], ["adjuster_saving", "keeper_saving"]],
            inter=[
                "keeper_saving:y_f_kp → house_choice:y_f",
                "keeper_saving:y_h_kp → house_choice:y_h",
                "adjuster_saving:y_f_adj → house_choice:y_f",
                "adjuster_saving:y_h_adj → house_choice:y_h",
            ],
        ),
        id="housing-frictions",
    ),
]


# the same for the two registries whose rows carry a strict mark of expected
# failure
WHOLE = {
    "retirement-choice": dict(
        n=20,
        occurrences=61,
        terminal=RETIREMENT_WITHIN
        + ["retiree_cons:b_ret → bequest:a_bq", "worker_cons:b → bequest:a_bq"],
        layers=[["ret_choice"], ["retiree_cons", "worker_cons"], ["bequest"]],
        within=RETIREMENT_WITHIN,
        outputs=["retiree_cons:b_ret", "worker_cons:b"],
        later=[["ret_choice"], ["retiree_cons", "worker_cons"]],
        inter=["worker_cons:b → ret_choice:a", "retiree_cons:b_ret → retiree_cons:a_ret"],
    ),
    "pension-retirement": dict(
        n=15,
        occurrences=46,
        terminal=[
            f"retire_choice:y_{a}_{b} → terminal:y_{a}_T"
            for a, b in (("f", "rt"), ("f", "wk"), ("p", "rt"), ("p", "wk"))
        ]
        + ["retiree_saving:y_f_ret → terminal:y_f_T", "retiree_saving:y_p_ret → terminal:y_p_T"]
        + PENSION_WITHIN,
        layers=[["retiree_saving", "worker_saving"], ["retire_choice"], ["terminal"]],
        within=PENSION_WITHIN,
        outputs=[
            "retire_choice:y_f_rt",
            "retire_choice:y_f_wk",
            "retire_choice:y_p_rt",
            "retire_choice:y_p_wk",
            "retiree_saving:y_f_ret",
            "retiree_saving:y_p_ret",
        ],
        later=[["retiree_saving", "worker_saving"], ["retire_choice"]],
        inter=[
            "retire_choice:y_f_wk → worker_saving:y_f_w",
            "retire_choice:y_p_wk → worker_saving:y_p_w",
            "retire_choice:y_f_rt → retiree_saving:y_f_r",
            "retire_choice:y_p_rt → retiree_saving:y_p_r",
            "retiree_saving:y_f_ret → retiree_saving:y_f_r",
            "retiree_saving:y_p_ret → retiree_saving:y_p_r",
        ],
    ),
}


WHOLE_KNOWN_FAILURES = {
    "retirement-choice": pytest.mark.xfail(
        strict=True,
        reason="The test expects each entry of `methods` of the stage `worker_cons` of "
        "`retirement-choice` to carry the attribute `tag`. Today each entry is a record of the "
        "method, the grid and the handler typed at one place, which has no attribute `tag`, so "
        "the row stops in `whole_trellis` before it reads the trellis.",
    ),
    "pension-retirement": pytest.mark.xfail(
        strict=True,
        reason="The test expects the terminal period of `pension-retirement` to join the fields "
        "y_f and y_p of `worker_saving` to the fields y_f and y_p of `retire_choice`. Today it "
        "joins them to the fields y_f_d and y_p_d of `retire_choice`.",
    ),
}


# the placeholder values of the pension registry's `$fill`, inside the
# declared sets and no calibration of the model
PENSION_FILL = {
    "calibration": {
        "β": 0.9,
        "ρ": 2.0,
        "r_f": 0.02,
        "r_p": 0.03,
        "χ_s": 0.1,
        "μ_w": 0.0,
        "σ_w": 0.1,
        "w_R": 0.5,
    }
}


def whole_trellis(key):
    """The trellis of a registry of `WHOLE`: the registry of
    `retirement-choice` elaborated, calibrated and methodized, after a check
    that the one method of the stage `worker_cons` whose tag is `egm` stands
    at the place `policy:Evaluation` with the handler `asva:make_egm_1d`; or
    the registry of `pension-retirement` assembled with `PENSION_FILL`."""
    if key == "retirement-choice":
        syntactic = load_recipe(RETIREMENT, "spec.yml")
        methodized = methodize_trellis(
            calibrate_trellis(elaborate_trellis(syntactic), syntactic), syntactic
        )
        worker = methodized["periods"][0]["stages"]["worker_cons"]
        assert [
            (str(place), method.handler)
            for place, method in worker.methods.items()
            if method.tag == "egm"
        ] == [("policy:Evaluation", "asva:make_egm_1d")]
        return methodized
    return assemble_trellis(PENSION, "spec.yml", fill=PENSION_FILL)


@pytest.fixture(scope="module")
def durables_trellis_with_wage_schedule():
    """The trellis of the durables application of 51 periods, the wage schedule
    written into its recipe between load_recipe and the verbs, then
    calibrated, methodized and configured."""
    syntactic = wage_schedule_writer()(load_recipe(DURABLES, "spec.yml"))
    return configure_trellis(
        methodize_trellis(calibrate_trellis(elaborate_trellis(syntactic), syntactic), syntactic),
        syntactic,
    )


@pytest.fixture(scope="module")
def housing_frictions_trellis():
    """The trellis of the housing frictions application of 60 periods, as
    assemble_trellis makes it."""
    return assemble_trellis(HOUSING, "spec.yml")


# each row elaborates a registry whole, so the test runs only with --complete;
# both rows carry a strict mark of expected failure
@pytest.mark.complete_set
@pytest.mark.parametrize(
    "key", [pytest.param(key, marks=WHOLE_KNOWN_FAILURES.get(key, ())) for key in WHOLE]
)
def test_the_retirement_and_pension_registries_elaborate_as_whole_trellises_with_their_joins(key):
    """The trellis of each of the registries of `retirement-choice` and
    `pension-retirement` has the periods and the stage occurrences of its
    registry, the joins, the outputs and the layers written for its terminal
    period and for each other period, the inter-period joins written for each
    pair of periods, and each continuation state field joined to exactly one
    arrival field."""
    expected = WHOLE[key]
    trellis = whole_trellis(key)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    assert (len(periods), len(positions(trellis))) == (expected["n"], expected["occurrences"])
    terminal = period_joins(periods[0])
    assert [arrow(join) for join in terminal["joins"]] == expected["terminal"] and terminal[
        "outputs"
    ] == []
    assert computable_together(periods[0]) == expected["layers"]
    for h in range(1, expected["n"]):
        within = period_joins(periods[h])
        assert [arrow(join) for join in within["joins"]] == expected["within"]
        assert [f"{k}:{f}" for k, f in within["outputs"]] == expected["outputs"]
        assert computable_together(periods[h]) == expected["later"]
        assert [
            arrow(join) for join in inter_period_joins(mappings[h - 1], periods[h], periods[h - 1])
        ] == expected["inter"]
    # every continuation state field of every occurrence joins exactly one
    # arrival field, within its period or across its pair of periods
    sources = Counter(
        (h, join["from"])
        for h in range(expected["n"])
        for join in period_joins(periods[h])["joins"]
    )
    sources += Counter(
        (h + 1, join["from"])
        for h in range(expected["n"] - 1)
        for join in inter_period_joins(mappings[h], periods[h + 1], periods[h])
    )
    continuations = sum(
        1
        for period in periods
        for stage in period["stages"].values()
        for sort in fields(stage).values()
        if sort.perch == "cntn" and sort.role == "state"
    )
    assert set(sources.values()) == {1} and len(sources) == continuations


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_a_registry_elaborates_to_its_periods_and_stage_occurrences(
    trellis_name, expected, request
):
    """The trellis of a registry has the number of periods and of stage
    occurrences of its registry."""
    trellis = request.getfixturevalue(trellis_name)
    assert (len(trellis["periods"]), len(positions(trellis))) == (
        expected["n"],
        expected["occurrences"],
    )


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_the_terminal_period_of_a_registry_joins_its_stages_and_leaves_no_output(
    trellis_name, expected, request
):
    """The terminal period of a registry makes the joins written for it, so
    that every continuation field joins a stage of the period and none leaves
    it."""
    terminal_joins = period_joins(request.getfixturevalue(trellis_name)["periods"][0])
    assert [arrow(join) for join in terminal_joins["joins"]] == expected["terminal"]
    assert terminal_joins["outputs"] == []


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_the_terminal_period_of_a_registry_is_computed_in_its_layers(
    trellis_name, expected, request
):
    """The stages of the terminal period of a registry stand in the layers that
    its joins order."""
    terminal_period = request.getfixturevalue(trellis_name)["periods"][0]
    assert computable_together(terminal_period) == expected["layers"]


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_each_period_of_a_registry_but_the_terminal_one_joins_its_stages_and_leaves_its_outputs(
    trellis_name, expected, request
):
    """Each period of a registry other than the terminal period joins the
    branch fields to the stages they enter, and the continuation fields of its
    last stages leave the period."""
    periods = request.getfixturevalue(trellis_name)["periods"]
    number_of_other_periods = expected["n"] - 1
    found = [period_joins(period) for period in periods[1:]]
    assert [[arrow(join) for join in joins["joins"]] for joins in found] == [
        expected["within"]
    ] * number_of_other_periods
    assert [[f"{key}:{field}" for key, field in joins["outputs"]] for joins in found] == [
        expected["outputs"]
    ] * number_of_other_periods


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_the_stages_of_each_period_but_the_terminal_one_stand_in_the_layers_that_its_joins_order(
    trellis_name, expected, request
):
    """The stages of each period of a registry other than the terminal period
    stand in the layers that its joins order."""
    periods = request.getfixturevalue(trellis_name)["periods"]
    assert [computable_together(period) for period in periods[1:]] == [expected["later"]] * (
        expected["n"] - 1
    )


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_each_pair_of_periods_of_a_registry_is_joined_by_its_inter_period_joins(
    trellis_name, expected, request
):
    """The inter-period mapping of each pair of periods of a registry joins the
    continuation fields of the earlier period to the arrival fields of the
    later one."""
    trellis = request.getfixturevalue(trellis_name)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    joined = [
        [arrow(join) for join in inter_period_joins(mappings[h - 1], periods[h], periods[h - 1])]
        for h in range(1, len(periods))
    ]
    assert joined == [expected["inter"]] * (expected["n"] - 1)


@pytest.mark.complete_set
@pytest.mark.parametrize(("trellis_name", "expected"), REGISTRIES)
def test_each_continuation_state_of_a_registry_joins_exactly_one_arrival_field(
    trellis_name, expected, request
):
    """Every continuation state field of every stage occurrence of a registry
    joins exactly one arrival field, within its period or across its pair of
    periods."""
    trellis = request.getfixturevalue(trellis_name)
    periods, mappings, n = trellis["periods"], trellis["inter_connectors"], expected["n"]
    sources = Counter(
        (h, join["from"]) for h in range(n) for join in period_joins(periods[h])["joins"]
    )
    sources += Counter(
        (h + 1, join["from"])
        for h in range(n - 1)
        for join in inter_period_joins(mappings[h], periods[h + 1], periods[h])
    )
    continuations = sum(
        1
        for period in periods
        for stage in period["stages"].values()
        for sort in stage.fields().values()
        if sort.perch == "cntn" and sort.role == "state"
    )
    assert set(sources.values()) == {1} and len(sources) == continuations


@pytest.mark.complete_set
def test_the_durables_recipe_is_refused_without_its_wage_schedule_and_elaborates_with_it(
    durables_trellis_with_wage_schedule,
):
    """assemble_trellis refuses the recipe of the durables application without
    the wage schedule that its code writes, naming the income level Y, and
    with the schedule written the recipe gives its 51 periods."""
    with pytest.raises(ValueError, match="'Y'"):
        assemble_trellis(DURABLES, "spec.yml")
    assert len(durables_trellis_with_wage_schedule["periods"]) == 51


# the value of the taste for children, which the paper gives as a distribution
# across women and does not report: a value inside its declared set and no
# calibration of the model
CHILDBEARING_FILL = {"calibration": {"ω": 1.0}}


# the title of a card by the direction and the name of its builder
TITLE = {
    "backward/cntn_to_dcsn": "BACKWARD BUILDER cntn_to_dcsn",
    "forward/dcsn_to_cntn": "FORWARD BUILDER dcsn_to_cntn",
    "backward/policy": "POLICY BUILDER policy",
}


# the joins, outputs and layers of the childbearing registry: within a period
# other than the terminal period, in the terminal period, and between two
# periods
WITHIN = [
    "attempt:a_try → fecundity:a_fec",
    "attempt:age_try → fecundity:age_fec",
    "cons_wait:age_c → attempt:age_att",
    "cons_wait:b_wait → attempt:a_att",
    "fecundity:a_chl → cons_childless:a_childless",
    "fecundity:a_mth → cons_mother:a_mother",
]


TERMINAL = sorted(
    WITHIN
    + [
        "attempt:a_next → terminal_wait:a_tw",
        "attempt:age_next → terminal_wait:age_tw",
        "cons_childless:b_childless → terminal_childless:a_tc",
        "cons_mother:b_mother → terminal_mother:a_tm",
    ]
)


INTER = [
    "attempt:a_next → cons_wait:a_wait",
    "attempt:age_next → cons_wait:age",
    "cons_mother:b_mother → cons_mother:a_mother",
    "cons_childless:b_childless → cons_childless:a_childless",
]


OUTPUTS = [
    ("attempt", "a_next"),
    ("attempt", "age_next"),
    ("cons_childless", "b_childless"),
    ("cons_mother", "b_mother"),
]


# the outputs of the terminal period, the boundary data of the three routes
OUTPUTS_0 = [
    ("terminal_childless", "b_tc"),
    ("terminal_mother", "b_tm"),
    ("terminal_wait", "age_twc"),
    ("terminal_wait", "b_tw"),
]


LAYERS = [["cons_wait"], ["attempt"], ["fecundity"], ["cons_childless", "cons_mother"]]


LAYERS_0 = [
    ["cons_wait"],
    ["attempt"],
    ["fecundity", "terminal_wait"],
    ["cons_childless", "cons_mother"],
    ["terminal_childless", "terminal_mother"],
]


# the rules that the aggregation of the decision card of fecundity prints: the
# expectation over the shock s of the tuple of the branch values, for the
# value and its derivative
FECUNDITY_RULES = (
    "𝑉 "
    "= E_{s}[(𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)) + ω, "
    "𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]] "
    "on (a_fecd, age_fecd) ∈ Xa × Xt "
    "𝑑𝑉 "
    "= E_{s}[(𝑑𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)), "
    "𝑑𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]] "
    "on (a_fecd, age_fecd) ∈ Xa × Xt"
)


# the weighted sum that the definition of the aggregation of fecundity states
FECUNDITY_CASE = (
    "(𝜋(age_fecd) · (V_mth≻ + ω) + (1 − 𝜋(age_fecd)) · V_chl≻, "
    "𝜋(age_fecd) · dV_mth≻ + (1 − 𝜋(age_fecd)) · dV_chl≻)"
)


# This test elaborates the childbearing registry whole, 183 stage occurrences
# over 36 periods, so it runs only with --complete.
@pytest.mark.complete_set
@pytest.mark.xfail(
    strict=True,
    reason="The test expects the printed card of the decision builder `cntn_to_dcsn` of the "
    "stage `attempt` of the childbearing model to state what the example page shows. Today "
    "the card differs from the page in several of its sections, its signature among them.",
)
def test_the_childbearing_registry_elaborates_as_a_whole_trellis_with_its_joins_and_cards():
    """`assemble_trellis` refuses the childbearing registry without a value of
    the taste for children ω and, with one, makes a trellis with the periods,
    the stage occurrences, the joins, the outputs, the layers and the
    inter-period joins written for it, and the five cards of its branching
    stages state what the example page shows."""
    with pytest.raises(ValueError, match="'ω'"):
        assemble_trellis(CHILDBEARING, "spec.yml")
    trellis = assemble_trellis(CHILDBEARING, "spec.yml", fill=CHILDBEARING_FILL)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    assert (len(periods), len(mappings), len(positions(trellis))) == (36, 35, 183)
    terminal = period_joins(periods[0])
    assert [arrow(join) for join in terminal["joins"]] == TERMINAL and terminal[
        "outputs"
    ] == OUTPUTS_0
    assert computable_together(periods[0]) == LAYERS_0
    for h in range(1, 36):
        within = period_joins(periods[h])
        assert [arrow(join) for join in within["joins"]] == WITHIN and within["outputs"] == OUTPUTS
        assert computable_together(periods[h]) == LAYERS
        assert [
            arrow(join) for join in inter_period_joins(mappings[h - 1], periods[h], periods[h - 1])
        ] == INTER
    # every continuation state field joins one arrival field, apart from the
    # four outputs of the terminal period, `OUTPUTS_0`
    sources = Counter(
        (h, join["from"]) for h in range(36) for join in period_joins(periods[h])["joins"]
    )
    sources += Counter(
        (h + 1, join["from"])
        for h in range(35)
        for join in inter_period_joins(mappings[h], periods[h + 1], periods[h])
    )
    continuations = sum(
        1
        for period in periods
        for stage in period["stages"].values()
        for sort in fields(stage).values()
        if sort.perch == "cntn" and sort.role == "state"
    )
    assert set(sources.values()) == {1} and len(sources) == continuations - len(OUTPUTS_0)
    # the five cards of the branching stages that the example page shows: the
    # three cards of `attempt` and the forward card of `fecundity`, compared
    # whole, then the decision card of `fecundity`, compared in parts
    stages = {
        name: elaborate_stage(load_stage(CHILDBEARING / "stages" / f"{name}.bl"))
        for name in ("attempt", "fecundity")
    }
    for name, key in (
        ("attempt", "backward/cntn_to_dcsn"),
        ("attempt", "forward/dcsn_to_cntn"),
        ("attempt", "backward/policy"),
        ("fecundity", "forward/dcsn_to_cntn"),
    ):
        direction, builder = key.split("/")
        graph = {"backward": stages[name].builder.bwd, "forward": stages[name].builder.fwd}[
            direction
        ]
        assert (
            differing_card_sections(
                graph[builder],
                card_shown_on_the_page(CHILDBEARING_EXAMPLE, f"STAGE {name} / {TITLE[key]}"),
            )
            == []
        ), (name, key)
    # the decision card of `fecundity`: the keys of its operations, its
    # signature and its sections `Where` and `Source` as the example page
    # shows them, the rules of its Aggregation, and the weighted sum that the
    # definition of its aggregator states
    decision = stages["fecundity"].builder.bwd["cntn_to_dcsn"]
    card, drawn = (
        str(decision),
        card_shown_on_the_page(
            CHILDBEARING_EXAMPLE, "STAGE fecundity / BACKWARD BUILDER cntn_to_dcsn"
        ),
    )
    assert [str(key) for key in decision.primitives.list()] == [
        "Pullback:mother",
        "Pullback:childless",
        "Aggregation",
        "Evaluation",
    ]
    assert {flat(line) for line in card_section_lines(card, "Signature")[1:]} == {
        flat(line) for line in card_section_lines(drawn, "Signature")[1:]
    }
    for heading in ("Where", "Source"):
        assert flat("\n".join(card_section_lines(card, heading))) == flat(
            "\n".join(card_section_lines(drawn, heading))
        ), heading
    [aggregation] = [
        entry
        for entry in operations_entries(card_section_lines(card, "Operations")[1:])
        if entry["key"] == "Aggregation"
    ]
    assert flat("\n".join(aggregation["rule"])) == flat(FECUNDITY_RULES)
    assert flat(FECUNDITY_CASE) in flat(
        str(stages["fecundity"].definitions.denote("fecundity:G:cntn_to_dcsn"))
    )


# the two entrepreneur stages, which the package refuses since the block
# dcsn_to_cntn of each lists the controls k, c and d beside its branches,
# whereas the package constructs a branching block whose label is a control
# only when that control is the block's one control; each is replaced by a
# stand-in, a stage without branches that declares the same arrival and
# continuation fields, which are all that the joins of a period read
ENTREPRENEUR_STANDINS = {
    "young_entrepreneur": """@stage: young_entrepreneur

Xa := ℝ₊
Y  := ℝ₊₊
Θ  := ℝ₊

[id=arvl_to_dcsn, (a_ye : Xa, y_ye : Y, θ_ye : Θ) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_ye
    y = y_ye
    θ = θ_ye
}

[id=dcsn_to_cntn, (a, y, θ) : !dcsn -> (a_ye_ea : Xa, y_ye_ea : Y, θ_ye_ea : Θ, \
a_ye_wk : Xa, y_ye_wk : Y, θ_ye_wk : Θ) : !cntn] {
    a_ye_ea = a
    y_ye_ea = y
    θ_ye_ea = θ
    a_ye_wk = a
    y_ye_wk = y
    θ_ye_wk = θ
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
""",
    "old_entrepreneur": """@stage: old_entrepreneur

Xa := ℝ₊
Y  := ℝ₊₊
Θ  := ℝ₊

[id=arvl_to_dcsn, (a_oe : Xa, θ_oe : Θ) : !arvl -> (a : Xa, θ : Θ) : !dcsn] {
    a = a_oe
    θ = θ_oe
}

[id=dcsn_to_cntn, (a, θ) : !dcsn -> (a_oe_ed : Xa, θ_oe_ed : Θ, a_oe_rt : Xa) : !cntn] {
    a_oe_ed = a
    θ_oe_ed = θ
    a_oe_rt = a
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
""",
}


# the arrival fields of a Cagetti–De Nardi period that several branch fields
# join, each
# with the number of the branch fields that join it
SOURCES = {
    "young_choice:a_yc": 4,
    "young_choice:y_yc": 4,
    "young_choice:θ_yc": 4,
    "retiree:a_rt": 4,
    "old_choice:a_oc": 2,
    "old_choice:θ_oc": 2,
    "worker:a_wk": 2,
    "worker:y_wk": 2,
    "worker:θ_wk": 2,
}


@pytest.fixture(scope="module")
def cagetti_de_nardi_joins():
    """The joins of each period of the Cagetti–De Nardi registry, elaborated
    with each entrepreneur stage replaced by its stand-in."""
    syntactic = copy.deepcopy(load_recipe(CAGETTI_DE_NARDI_REGISTRY, "spec.yml"))
    for period in syntactic["periods"]:
        for key, text in ENTREPRENEUR_STANDINS.items():
            record = period["stages"][key]
            record["stage"] = {"text": text, "origin": f"standin:{key}"}
            # a stand-in text replaces the stage and takes no addition of the
            # stage it replaces
            record["methods"] = []
            record["provenance"] = {
                **record["provenance"],
                "origin": f"standin:{key}",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
    return [period_joins(period) for period in elaborate_trellis(syntactic)["periods"]]


def test_each_cagetti_de_nardi_period_with_the_entrepreneurs_stood_in_has_its_joins_and_outputs(
    cagetti_de_nardi_joins,
):
    """The terminal period of the Cagetti–De Nardi registry makes 40 joins and
    leaves no output, and each of the two other periods, `periods[1]` and
    `periods[2]`, makes 31 and leaves 9."""
    assert [(len(joins["joins"]), len(joins["outputs"])) for joins in cagetti_de_nardi_joins] == [
        (40, 0),
        (31, 9),
        (31, 9),
    ]


def test_several_branch_fields_join_one_arrival_field_in_each_cagetti_de_nardi_period(
    cagetti_de_nardi_joins,
):
    """In each of the three periods of the Cagetti–De Nardi registry, four
    branch fields join each arrival field of the young's choice and of the
    retiree, and two join each arrival field of the old's choice and of the
    worker."""
    counted = [
        Counter(f"{join['to'][0]}:{join['to'][1]}" for join in joins["joins"])
        for joins in cagetti_de_nardi_joins
    ]
    assert [{target: n for target, n in sources.items() if n > 1} for sources in counted] == [
        SOURCES
    ] * 3


@pytest.mark.parametrize(
    ("name", "outputs"),
    [
        pytest.param("tenure", ["h_kp", "w_adj", "w_kp", "z_adj", "z_kp"], id="tenure, a choice"),
        pytest.param(
            "retiree_death",
            ["a_rd_rt", "a_rd_yc", "y_rd_yc", "θ_rd_yc"],
            id="retiree_death, a draw whose forward builders are refused",
        ),
    ],
)
def test_a_period_of_one_branching_stage_placed_by_hand_leaves_its_branch_fields(
    name, outputs, request
):
    """A period of one elaborated branching stage, accreted by hand, is
    elaborated, and its outputs are the branch fields at the continuation
    perch."""
    trellis = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {name: request.getfixturevalue(name)}, "connectors": []},
    )
    assert period_joins(elaborate_trellis(trellis)["periods"][0])["outputs"] == [
        (name, field) for field in outputs
    ]
