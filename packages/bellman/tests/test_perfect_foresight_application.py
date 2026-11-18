"""The perfect-foresight consumption application: its stage solved in two
ways, by the closed form that its methods file types with `!explicit`,
compared with independent formulas and with the identities of the model,
and by the endogenous grid method of its second methods file, and the scalar
evaluators of the application's numerical module."""

import math
from types import SimpleNamespace

import numpy as np
import pytest
from application_files import PERFECT_FORESIGHT_CALIBRATION, RETURN_IMPATIENCE_FAILING_CALIBRATION
from stage_builders import closed_form_check, stage_from_text

from bellman.refusals import ConstructionError
from bellman.stage.representations import families

# a calibration at which the closed form holds although the discount factor
# normalized by growth, βΓ^(1-ρ) = 0.9 × 0.5^(-1) = 1.8, lies above one
NORMALIZED_DISCOUNT_ABOVE_ONE = {"β": 0.9, "ρ": 2.0, "R": 1.04, "Γ": 0.5}


# a discount factor one rounding step below its bound R^(ρ-1) = 0.9, at which
# q = (βR)^(1/ρ)/R computes to one
ROUNDING = {"calibration": {"β": 0.8999999999999999, "ρ": 2.0, "R": 0.9, "Γ": 0.81}}


# total wealth m - L from 10⁻³ to 100, 201 points spaced evenly in logarithm
TOTAL_WEALTH = np.geomspace(1e-3, 100.0, 201)


# The independent formulas are the closed form derived by hand in the
# application's `economics.md` and written in Python as the functions of the
# application's module whose names begin with `reference_`: the coefficients
# q = (βR)^(1/ρ)/R, κ = 1 - q, h = 1/(1 - Γ/R) and L = 1 - h, and the
# consumption, values and marginal values built from them. No route of the
# module reads them. The second calibration is β = 0.90, ρ = 2, R = 1.04 and
# Γ = 1.01, at which human wealth is 1/(1 - 1.01/1.04).


# the three calibrations at which the closed form is compared with the
# independent formulas and its identities are checked, each the name of the
# fixture of its stage; each test of these tables first checks that the
# calibration of the third row has the normalized discount factor 1.8
CLOSED_FORM_CALIBRATIONS = [
    pytest.param("closed_form_at_the_baseline_calibration", id="baseline-calibration"),
    pytest.param("closed_form_at_the_second_calibration", id="second-calibration"),
    pytest.param(
        "closed_form_with_a_normalized_discount_factor_above_one",
        id="normalized-discount-factor-above-one",
    ),
]


# the four comparisons of the gridded route with the closed form, by
# their key in the fixture `gridded_comparisons`
SAVINGS_GRIDS = [
    pytest.param("5 savings", id="5-savings"),
    pytest.param("50 savings", id="50-savings"),
    pytest.param("500 savings", id="500-savings"),
    pytest.param("50 savings at the second calibration", id="50-savings-second-calibration"),
]


def normalized_discount_factor(calibration):
    """The discount factor normalized by growth, βΓ^(1-ρ), of a
    calibration."""
    return calibration["β"] * calibration["Γ"] ** (1 - calibration["ρ"])


def bound_stage(application, route, calibration):
    """The stage that the application's module binds from the calibration
    `calibration` by the route `route`: the closed form, which reads no
    setting, or the endogenous grid method on 5 savings from -10 to 60."""
    if route == "endogenous grid":
        # the count of savings n_a, then the bounds a_min and a_max
        return application.gridded_stage(5, -10.0, 60.0, calibration)
    return application.closed_form_stage(calibration)


@pytest.fixture(scope="module")
def application():
    """The numerical module `code/closed_form_check.py` of the
    perfect-foresight application."""
    return closed_form_check()


@pytest.fixture(scope="module")
def baseline_closed_form(application, perfect_foresight_solutions):
    """The closed form that the closed-form stage holds at the baseline
    calibration: its coefficients and its five compiled functions."""
    return application.closed_form(perfect_foresight_solutions.closed)


@pytest.fixture(scope="module")
def closed_form_at_the_baseline_calibration(perfect_foresight_solutions):
    """The closed-form stage at the baseline calibration, with the 401
    levels of resources from -30 to 50 at which its identities are
    checked."""
    return SimpleNamespace(
        stage=perfect_foresight_solutions.closed, interval=perfect_foresight_solutions.resources
    )


@pytest.fixture(scope="module")
def closed_form_at_the_second_calibration(perfect_foresight_solutions):
    """The closed-form stage at the second calibration, at which human wealth
    is 1/(1 - 1.01/1.04), with the 401 levels of resources from -30 to 50."""
    return SimpleNamespace(
        stage=perfect_foresight_solutions.alternative,
        interval=perfect_foresight_solutions.resources,
    )


@pytest.fixture(scope="module")
def closed_form_with_a_normalized_discount_factor_above_one(application):
    """The closed-form stage at `NORMALIZED_DISCOUNT_ABOVE_ONE`, with 401
    levels of resources from 0 to 50."""
    return SimpleNamespace(
        stage=application.closed_form_stage({"calibration": NORMALIZED_DISCOUNT_ABOVE_ONE}),
        interval=np.linspace(0.0, 50.0, 401),
    )


@pytest.fixture(scope="module")
def gridded_comparisons(perfect_foresight_solutions):
    """The comparisons of the gridded route with the closed form on
    5, 50 and 500 savings from -40 to 60 at the baseline calibration, and on
    50 savings from -33 to 60 at the second calibration."""
    return {
        "5 savings": perfect_foresight_solutions.comparisons[5],
        "50 savings": perfect_foresight_solutions.comparisons[50],
        "500 savings": perfect_foresight_solutions.comparisons[500],
        "50 savings at the second calibration": perfect_foresight_solutions.alternative_comparison,
    }


@pytest.fixture(scope="module")
def gridded_envelope_condition(application, perfect_foresight_solutions):
    """The compiled envelope condition D_{m}V = c^(-ρ) of the gridded stage
    on 50 savings, as a function of m and c."""
    gridded = perfect_foresight_solutions.comparisons[50].gridded
    return application.kernel_function(
        gridded.builder["cntn", "dcsn"].kernels(), "marginal:Derivative:1"
    )


@pytest.fixture(scope="module")
def gridded_arrival_marginal(
    application, perfect_foresight_solutions, baseline_closed_form, gridded_envelope_condition
):
    """The compiled derivative line of the arrival value of the gridded
    stage on 50 savings, its parameters, the points k = L + w of
    `TOTAL_WEALTH`, and the decision marginal it reads there: the compiled
    envelope condition at the resources that the law of motion gives and at
    the closed-form consumption there."""
    gridded = perfect_foresight_solutions.comparisons[50].gridded
    kernels = gridded.builder["dcsn", "arvl"].kernels()
    k = baseline_closed_form.limit + TOTAL_WEALTH
    following = application.kernel_function(kernels, "Pullback")(k=k)
    return SimpleNamespace(
        marginal=application.kernel_function(kernels, "marginal:Derivative:1"),
        parameters=application.parameters(gridded),
        k=k,
        decision_marginal=gridded_envelope_condition(
            m=following, c=baseline_closed_form.consumption(following)
        ),
    )


@pytest.fixture(scope="module")
def value_interpolations(application, perfect_foresight_solutions):
    """The comparisons of the decision value and the arrival value of the
    closed form with their Linear and PCHIP evaluators on 5, 50 and 500
    equally spaced nodes from -30 to 50, at a fixed sample of 1000 points,
    by the family's word and the count of nodes."""
    return {
        (word, count): application.value_interpolation(
            perfect_foresight_solutions.closed, word, count
        )
        for word in ("Linear", "pchip")
        for count in (5, 50, 500)
    }


@pytest.fixture(scope="module")
def value_evaluators_on_five_nodes(application, baseline_closed_form):
    """The Linear and PCHIP evaluators of the decision value of the closed
    form on the coordinate m, at the five nodes -30, -10, 10, 30 and 50, by
    the family's word."""
    nodes = np.linspace(-30.0, 50.0, 5)
    values = baseline_closed_form.value(nodes)
    return {
        "Linear": application.Linear(nodes, values, "m"),
        "pchip": application.Pchip(nodes, values, "m"),
    }


@pytest.fixture(scope="module")
def near_limit_checks(application, perfect_foresight_solutions, perfect_foresight_near_route):
    """The checks of the converged policy of the gridded route near the
    limit against the closed form at the 61 levels of total wealth from 10⁻³
    to 1, spaced evenly in logarithm."""
    return application.near_limit(
        perfect_foresight_solutions.closed,
        perfect_foresight_near_route,
        np.geomspace(1e-3, 1.0, 61),
    )


@pytest.fixture(scope="module")
def perfect_foresight_stage_file(application):
    """The text and the origin of the stage file of the application."""
    return application.source(application.STAGE)


# the methods and the settings of the two routes


def test_the_closed_form_methods_file_types_three_builders_explicit_with_generated_evaluations(
    perfect_foresight_solutions,
):
    """The methods of the closed-form stage are `!explicit` on the policy
    builder and on the two value builders, each with the closed form
    generated at its Evaluation."""
    methods = str(perfect_foresight_solutions.closed.methods)
    assert [line.split() for line in methods.splitlines()] == [
        ["cntn_to_dcsn", "!explicit"],
        ["cntn_to_dcsn.evaluate", "!closed_form", "generated", "from", "cntn_to_dcsn.method"],
        ["dcsn_to_arvl", "!explicit"],
        ["dcsn_to_arvl.evaluate", "!closed_form", "generated", "from", "dcsn_to_arvl.method"],
        ["policy", "!explicit"],
        ["policy.evaluate", "!closed_form", "generated", "from", "policy.method"],
    ]


def test_the_closed_form_stage_has_no_settings(perfect_foresight_solutions):
    """The closed-form stage, which the application's module configures from
    the empty source `{"settings": {}}`, lists no setting, where the gridded
    stage lists the three settings of its methods file in
    `test_the_gridded_stage_lists_the_three_settings_of_its_grid_of_savings`."""
    assert list(perfect_foresight_solutions.closed.settings.list()) == []


def test_the_perfect_foresight_application_holds_no_settings_folder(application):
    """The declaration folder of the application holds no folder of
    settings."""
    assert not (application.DECLARATION / "settings").exists()


def test_the_endogenous_grid_methods_file_reads_the_consumption_function_from_the_pairs(
    gridded_comparisons,
):
    """The methods of the gridded stage are `!egm` on the policy
    builder and, at its Evaluation, `!Linear` read from the pairs that the
    method computes."""
    methods = gridded_comparisons["50 savings"].gridded.methods
    assert (
        methods["policy"].word,
        methods["policy.evaluate"].word,
        methods["policy.evaluate"].source,
    ) == ("!egm", "!Linear", "pairs")


def test_the_gridded_stage_lists_the_three_settings_of_its_grid_of_savings(
    gridded_comparisons,
):
    """The settings of the gridded stage are n_a, a_min and a_max,
    each read by `!egm`."""
    settings = gridded_comparisons["50 savings"].gridded.settings
    assert {(row["name"], row["by"]) for row in settings.list()} == {
        (name, "!egm") for name in ("n_a", "a_min", "a_max")
    }


# the closed form at the baseline calibration


def test_the_closed_form_stage_lists_its_derived_parameters_after_the_declared_ones(
    perfect_foresight_solutions,
):
    """`stage.par` of the closed-form stage lists q of the stage file and κ,
    h_lim and L_lim of the methods file after the four declared
    parameters."""
    assert list(perfect_foresight_solutions.closed.par)[4:] == ["q", "κ", "h_lim", "L_lim"]


def test_the_return_patience_factor_lies_below_one_at_the_baseline_calibration(
    baseline_closed_form,
):
    """The return patience factor q of the closed-form stage at the baseline
    calibration lies below one, the return impatience condition."""
    assert baseline_closed_form.return_patience < 1


def test_the_growth_factor_lies_below_the_interest_factor_at_the_baseline_calibration(
    application, perfect_foresight_solutions
):
    """The growth factor Γ of the closed-form stage at the baseline
    calibration lies below the interest factor R, the finite human wealth
    condition."""
    parameters = application.parameters(perfect_foresight_solutions.closed)
    assert parameters["Γ"] < parameters["R"]


def test_the_closed_form_gives_kappa_h_and_l_their_values_at_the_baseline_calibration(
    baseline_closed_form,
):
    """At the baseline calibration κ = 1 - (1.04/1.04)^(1/2)/1.04 = 0.04/1.04,
    human wealth h = 1/(1 - 1.02/1.04) = 52 and the natural borrowing limit
    L = 1 - h = -51."""
    form = baseline_closed_form
    assert (form.κ, form.h, form.limit) == (
        pytest.approx(0.04 / 1.04),
        pytest.approx(52.0),
        pytest.approx(-51.0),
    )


def test_a_household_with_no_assets_consumes_twice_its_permanent_income(baseline_closed_form):
    """At the baseline calibration the compiled consumption function gives
    κh = 2 at the resources m = 1."""
    form = baseline_closed_form
    assert form.consumption(1.0) == pytest.approx(form.κ * form.h) == pytest.approx(2.0)


def test_the_compiled_consumption_function_is_kappa_times_total_wealth(
    baseline_closed_form, perfect_foresight_solutions
):
    """At the baseline calibration the compiled consumption function gives
    κ(m - 1 + h) on the 401 levels of resources from -30 to 50, within a
    relative 10⁻¹⁴."""
    form, resources = baseline_closed_form, perfect_foresight_solutions.resources
    assert np.allclose(
        form.consumption(resources), form.κ * (resources - 1 + form.h), rtol=1e-14, atol=0
    )


# the closed form against the independent formulas, at three calibrations, on
# total wealth from 10⁻³ to 100 at the decision and at the arrival perch


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_holds_the_coefficients_of_the_independent_formulas(
    request, application, calibration
):
    """The return patience factor q, κ, human wealth h_lim and the natural
    borrowing limit L_lim that the closed-form stage holds are q, κ, h and L
    of the independent formulas, within a relative 10⁻¹⁴."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held = application.closed_form(stage)
    reference = application.reference_coefficients(application.parameters(stage))
    assert (held.return_patience, held.κ, held.h, held.limit) == pytest.approx(
        (reference.q, reference.κ, reference.h, reference.L), rel=1e-14
    )


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_compiled_consumption_function_is_the_independent_formula(
    request, application, calibration
):
    """The compiled consumption function gives κ(m - L) of the independent
    formulas, within a relative 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held, p = application.closed_form(stage), application.parameters(stage)
    points = held.limit + TOTAL_WEALTH
    assert np.allclose(
        held.consumption(points), application.reference_consumption(p, points), rtol=1e-12, atol=0
    )


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_compiled_decision_value_is_the_independent_formula(request, application, calibration):
    """The compiled decision value gives κ^(-ρ)(m - L)^(1-ρ)/(1-ρ) of the
    independent formulas, within a relative 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held, p = application.closed_form(stage), application.parameters(stage)
    points = held.limit + TOTAL_WEALTH
    assert np.allclose(
        held.value(points), application.reference_value(p, points), rtol=1e-12, atol=0
    )


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_compiled_arrival_value_is_the_independent_formula(request, application, calibration):
    """The compiled arrival value gives Γ^(1-ρ) v(Rk/Γ + 1) of the independent
    formulas, within a relative 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held, p = application.closed_form(stage), application.parameters(stage)
    points = held.limit + TOTAL_WEALTH
    assert np.allclose(
        held.arrival_value(points),
        application.reference_arrival_value(p, points),
        rtol=1e-12,
        atol=0,
    )


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_compiled_decision_marginal_is_the_independent_formula(
    request, application, calibration
):
    """The compiled marginal of the decision value gives κ^(-ρ)(m - L)^(-ρ),
    with κ and L of the independent formulas, within a relative 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held, p = application.closed_form(stage), application.parameters(stage)
    reference = application.reference_coefficients(p)
    points = held.limit + TOTAL_WEALTH
    assert np.allclose(
        held.marginal(points),
        reference.κ ** (-p["ρ"]) * (points - reference.L) ** (-p["ρ"]),
        rtol=1e-12,
        atol=0,
    )


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_compiled_arrival_marginal_is_the_independent_formula(
    request, application, calibration
):
    """The compiled marginal of the arrival value gives RΓ^(-ρ) v′(Rk/Γ + 1),
    with v′(m) = κ^(-ρ)(m - L)^(-ρ) of the independent formulas, within a
    relative 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    stage = request.getfixturevalue(calibration).stage
    held, p = application.closed_form(stage), application.parameters(stage)
    reference = application.reference_coefficients(p)
    points = held.limit + TOTAL_WEALTH
    following = p["R"] * points / p["Γ"] + 1
    assert np.allclose(
        held.arrival_marginal(points),
        p["R"]
        * p["Γ"] ** (-p["ρ"])
        * reference.κ ** (-p["ρ"])
        * (following - reference.L) ** (-p["ρ"]),
        rtol=1e-12,
        atol=0,
    )


# the identities of the closed form, through the compiled kernels of the
# stage file's blocks, on the interval of resources of each calibration


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_satisfies_the_bellman_equation_of_the_stage_file(
    request, application, calibration
):
    """The residual of the Bellman equation of the stage file at the closed
    form lies below 10⁻¹² in absolute value."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    assert np.max(np.abs(application.bellman_residual(row.stage, row.interval))) < 1e-12


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_satisfies_the_arrival_value_block_of_the_stage_file(
    request, application, calibration
):
    """The residual of the arrival value block of the stage file at the
    closed form lies below 10⁻¹² in absolute value."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    assert np.max(np.abs(application.arrival_residual(row.stage, row.interval))) < 1e-12


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_satisfies_the_euler_equation(request, application, calibration):
    """The relative residual of the Euler equation at the closed-form
    consumption lies below 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    assert np.max(application.euler_residual(row.stage, row.interval)) < 1e-12


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_consumption_lies_in_the_feasible_set(request, application, calibration):
    """The closed-form consumption lies in the feasible set 0 < c < m + h[>]
    of the stage file, with h[>] = h_lim - 1, at every level of resources of
    the interval."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    assert application.feasibility(row.stage, row.interval).all()


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_closed_form_meets_the_present_value_budget(request, application, calibration):
    """The present value of the closed-form consumption over N periods and
    the present value of the total wealth left after them sum to total
    wealth, within a relative 10⁻¹², where q^N first falls below 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    reference = application.reference_coefficients(application.parameters(row.stage))
    periods = math.ceil(math.log(1e-12) / math.log(reference.q))
    budget = application.present_value_budget(row.stage, row.interval, periods)
    error = np.abs(budget.present_value + budget.remainder - budget.total_wealth)
    assert np.max(error / budget.total_wealth) < 1e-12


@pytest.mark.parametrize("calibration", CLOSED_FORM_CALIBRATIONS)
def test_the_total_wealth_left_after_n_periods_is_q_to_the_power_n_of_total_wealth(
    request, application, calibration
):
    """The present value of the total wealth that the closed form leaves after
    N periods is q^N times total wealth, within 10⁻¹⁵, where q^N first falls
    below 10⁻¹²."""
    assert normalized_discount_factor(NORMALIZED_DISCOUNT_ABOVE_ONE) == pytest.approx(1.8)
    row = request.getfixturevalue(calibration)
    reference = application.reference_coefficients(application.parameters(row.stage))
    periods = math.ceil(math.log(1e-12) / math.log(reference.q))
    budget = application.present_value_budget(row.stage, row.interval, periods)
    assert np.allclose(
        budget.remainder / budget.total_wealth, reference.q**periods, rtol=0, atol=1e-15
    )


# the derivative line of the arrival value under the endogenous grid method


def test_the_arrival_marginal_value_of_the_gridded_stage_scales_the_decision_marginal(
    gridded_arrival_marginal,
):
    """The compiled derivative line of the arrival value of the gridded stage
    gives RΓ^(-ρ) times the decision marginal value that it reads, within a
    relative 10⁻¹⁴."""
    held, p = gridded_arrival_marginal, gridded_arrival_marginal.parameters
    assert np.allclose(
        held.marginal(k=held.k, **{"D_{m}(V)": held.decision_marginal}),
        p["R"] * p["Γ"] ** (-p["ρ"]) * held.decision_marginal,
        rtol=1e-14,
        atol=0,
    )


def test_the_arrival_marginal_value_of_the_gridded_stage_is_the_independent_formula(
    application, gridded_arrival_marginal
):
    """At the compiled envelope condition and the closed-form consumption the
    compiled derivative line of the arrival value of the gridded stage gives
    RΓ^(-ρ) v′(Rk/Γ + 1) of the independent formulas, within a relative
    10⁻¹²."""
    held, p = gridded_arrival_marginal, gridded_arrival_marginal.parameters
    assert np.allclose(
        held.marginal(k=held.k, **{"D_{m}(V)": held.decision_marginal}),
        application.reference_arrival_marginal(p, held.k),
        rtol=1e-12,
        atol=0,
    )


# the refusals of a calibration, of a grid of savings and of a point


# each calibration that a declared set refuses: the route that binds it, the
# values it changes in the baseline calibration, and the set or the condition
# that the refusal names. The set ℝ₊₊ of human wealth h_lim := 1/(1 - Γ/R),
# which the closed-form methods file declares, is the finite human wealth
# condition Γ < R. The upper bound R^(ρ-1) of the set of β is the return
# impatience condition.
CALIBRATIONS_OUTSIDE_A_DECLARED_SET = [
    pytest.param(
        "closed form",
        {"Γ": 1.06},
        "of h_lim, which the stage defines as `1/(1 - Γ/R)`, lies outside the declared set ℝ₊₊",
        id="growth-factor-above-r",
    ),
    pytest.param(
        "closed form",
        RETURN_IMPATIENCE_FAILING_CALIBRATION,
        "the condition β < R^(ρ - 1)",
        id="discount-factor-above-its-bound",
    ),
    pytest.param(
        "endogenous grid",
        RETURN_IMPATIENCE_FAILING_CALIBRATION,
        "the condition β < R^(ρ - 1)",
        id="discount-factor-above-its-bound-under-the-endogenous-grid-method",
    ),
    pytest.param("closed form", {"ρ": 1.0}, "(1, inf)", id="risk-aversion-of-one"),
    pytest.param("closed form", {"β": math.nan}, "ℝ₊₊", id="discount-factor-not-a-number"),
    # the bound R^(ρ-1) of the set of β has no value at R = inf, and that
    # refusal also names ℝ₊₊, so the row names the value of R
    pytest.param(
        "closed form",
        {"R": math.inf},
        "the value inf lies outside the declared set ℝ₊₊",
        id="infinite-interest-factor",
    ),
    pytest.param(
        "closed form",
        {"Γ": math.nan},
        "the value nan lies outside the declared set ℝ₊₊",
        id="growth-factor-not-a-number",
    ),
]


@pytest.mark.parametrize(("route", "changes", "words"), CALIBRATIONS_OUTSIDE_A_DECLARED_SET)
def test_a_calibration_outside_a_declared_set_is_refused_naming_the_set(
    application, route, changes, words
):
    """Calibration refuses a value of a parameter outside its declared set, a
    discount factor above its bound R^(ρ-1), and a growth factor at which
    human wealth h_lim lies outside its declared set, with a message that
    names the set or the condition."""
    with pytest.raises(ValueError) as refused:
        bound_stage(
            application, route, {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, **changes}}
        )
    assert words in str(refused.value)


def test_a_growth_factor_equal_to_the_interest_factor_is_refused_since_human_wealth_has_no_value(
    application,
):
    """Under the closed-form methods file, calibration refuses Γ = R, at which
    the definition h_lim := 1/(1 - Γ/R) divides by zero, under the rule
    `derived-parameter`."""
    with pytest.raises(ConstructionError) as refused:
        bound_stage(
            application,
            "closed form",
            {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}},
        )
    assert refused.value.rule == "derived-parameter"
    assert "the derived parameter h_lim, defined as `1/(1 - Γ/R)`, has no value" in str(
        refused.value
    )


@pytest.mark.parametrize(
    "route",
    [
        pytest.param("endogenous grid", id="endogenous-grid-method"),
        pytest.param("closed form", id="closed-form"),
    ],
)
def test_a_return_patience_factor_that_computes_to_one_is_refused_by_its_declared_set(
    application, route
):
    """Under each methods file, calibration refuses the discount factor one
    rounding step below its bound, at which q computes to one, by the set
    (0, 1) that the definition of q declares, naming the values that the
    definition reads."""
    with pytest.raises(ValueError) as refused:
        bound_stage(application, route, ROUNDING)
    phrases = (
        "derived parameter 'q'",
        "the value 1.0 of q",
        "lies outside the declared set (0, 1) at β = 0.8999999999999999, ρ = 2.0, R = 0.9",
    )
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


def test_the_gridded_route_refuses_q_of_one_where_its_definition_declares_no_set(
    application, perfect_foresight_stage_file
):
    """Where the definition of q declares no set, the calibration at which q
    computes to one binds under the endogenous grid methods file, and the
    route refuses it by the return impatience condition q < 1."""
    declared = "q : (0,1) := "
    assert perfect_foresight_stage_file["text"].count(declared) == 1
    stage = stage_from_text(
        perfect_foresight_stage_file["text"].replace(declared, "q := "),
        perfect_foresight_stage_file["origin"],
    )
    stage.methodize(application.source(application.GRIDDED_METHODS))
    stage.calibrate(ROUNDING)
    stage.configure({"settings": {"n_a": 5, "a_min": -10.0, "a_max": 60.0}})
    with pytest.raises(ValueError, match=r"return impatience condition q < 1"):
        application.gridded_route(stage)


def test_the_closed_form_refuses_q_of_one_by_kappa_where_its_definition_declares_no_set(
    application, perfect_foresight_stage_file
):
    """Where the definition of q declares no set, calibration under the
    closed-form methods file refuses the calibration at which q computes to
    one, and κ = 1 - q to zero, by the condition κ ∈ (0, inf] of the negative
    power κ^(-ρ)."""
    declared = "q : (0,1) := "
    assert perfect_foresight_stage_file["text"].count(declared) == 1
    stage = stage_from_text(
        perfect_foresight_stage_file["text"].replace(declared, "q := "),
        perfect_foresight_stage_file["origin"],
    )
    stage.methodize(application.source(application.METHODS))
    with pytest.raises(ValueError, match=r"κ ∈ \(0, inf\]"):
        stage.calibrate(ROUNDING)


def test_the_gridded_route_refuses_a_grid_of_savings_below_the_borrowing_limit(
    application,
):
    """The route refuses a grid of savings from -40, below the natural
    borrowing limit L = 1 - 1/(1 - 1.01/1.04), about -33.7, of the second
    calibration."""
    # the count of savings n_a, then the bounds a_min and a_max
    stage = application.gridded_stage(
        50, -40.0, 60.0, {"calibration": {"β": 0.90, "ρ": 2.0, "R": 1.04, "Γ": 1.01}}
    )
    with pytest.raises(ValueError, match="at or below the natural borrowing limit"):
        application.gridded_route(stage)


# each function of the closed form of the application's module, given the
# resources 0, above the natural borrowing limit L = -51, and a point at L or
# one below it, its offset from L, where total wealth is not positive
NONPOSITIVE_TOTAL_WEALTH = [
    pytest.param("consumption", 0.0, id="consumption-at-the-limit"),
    pytest.param("value", -1.0, id="decision-value-below-the-limit"),
    pytest.param("marginal", 0.0, id="decision-marginal-at-the-limit"),
    pytest.param("arrival_value", 0.0, id="arrival-value-at-the-limit"),
    pytest.param("arrival_marginal", -1.0, id="arrival-marginal-below-the-limit"),
]


@pytest.mark.parametrize(("function", "offset_from_the_limit"), NONPOSITIVE_TOTAL_WEALTH)
def test_the_applications_closed_form_functions_refuse_a_point_without_positive_total_wealth(
    baseline_closed_form, function, offset_from_the_limit
):
    """Each of the five functions of the closed form in the application's
    module refuses a point at or below the natural borrowing limit, naming
    total wealth."""
    point = baseline_closed_form.limit + offset_from_the_limit
    with pytest.raises(ValueError, match="total wealth"):
        getattr(baseline_closed_form, function)(np.array([0.0, point]))


# the gridded route against the closed form


@pytest.mark.parametrize("comparison", SAVINGS_GRIDS)
def test_the_gridded_route_reaches_the_closed_form_consumption(gridded_comparisons, comparison):
    """The largest difference between the consumption of the gridded route
    and the closed-form consumption at the 401 levels of resources from -30
    to 50 lies below 10⁻⁹."""
    assert gridded_comparisons[comparison].difference < 1e-9


@pytest.mark.parametrize("comparison", SAVINGS_GRIDS)
def test_the_comparison_with_the_closed_form_interpolates_each_of_its_401_points(
    gridded_comparisons, comparison
):
    """The comparison reads the policy of the gridded route between
    its pairs at each of its 401 levels of resources and extends it at
    none."""
    found = gridded_comparisons[comparison]
    assert (found.interpolated, found.extrapolated) == (401, 0)


@pytest.mark.parametrize("comparison", SAVINGS_GRIDS)
def test_the_gridded_route_converges_below_its_tolerance(gridded_comparisons, comparison):
    """The last change of the consumption function of the gridded route
    lies below its tolerance 10⁻¹²."""
    assert gridded_comparisons[comparison].route.change < 1e-12


@pytest.mark.parametrize("comparison", SAVINGS_GRIDS)
def test_the_gridded_route_reports_its_extended_points_at_each_iteration(
    gridded_comparisons, comparison
):
    """The route records the number of extended points once for each of its
    iterations."""
    found = gridded_comparisons[comparison]
    assert len(found.route.extended) == found.iterations


def test_the_record_of_a_comparison_holds_its_savings_iterations_difference_and_route(
    gridded_comparisons,
):
    """The record of the comparison on 50 savings holds the count of savings,
    the number of iterations, the largest difference and the route."""
    found = gridded_comparisons["50 savings"]
    assert {"n_a", "iterations", "difference", "route"} <= set(vars(found))


def test_the_fixed_point_evaluates_resources_inside_its_pairs_by_its_linear_evaluator(
    gridded_comparisons, perfect_foresight_solutions
):
    """`evaluate` of the fixed point of the route on 50 savings gives at the
    levels of resources from -30 to 50 the values of the Linear evaluator of
    its pairs."""
    route, inside = gridded_comparisons["50 savings"].route, perfect_foresight_solutions.resources
    assert np.array_equal(route.evaluate(inside), route.policy(inside))


def test_the_fixed_point_refuses_a_point_beyond_its_pairs_unless_extrapolation_is_asked_for(
    application, gridded_comparisons
):
    """`evaluate` of the fixed point refuses a point 10 beyond its last pair,
    and with `extrapolate=True` gives there the endpoint-secant extension of
    its Linear evaluator, with a warning that reports the extended point."""
    # the endpoint-secant extension of the application's module continues the
    # secant of the first or the last interval beyond the nodes, on m > L
    # alone, and refuses a value that is not finite or not feasible
    route = gridded_comparisons["50 savings"].route
    beyond = np.array([route.knots[-1] + 10.0])
    with pytest.raises(ValueError, match="outside the pairs"):
        route.evaluate(beyond)
    with pytest.warns(UserWarning, match="endpoint-secant extension gives 1 of the 1 points"):
        extended = route.evaluate(beyond, extrapolate=True)
    assert np.array_equal(
        extended, route.policy.extend(beyond, application.EndpointSecant(route.limit)).values
    )


def test_the_fixed_point_refuses_to_extend_its_policy_to_the_natural_borrowing_limit(
    gridded_comparisons,
):
    """`evaluate` of the fixed point with `extrapolate=True` refuses the
    natural borrowing limit, outside the economic domain of the
    extension."""
    route = gridded_comparisons["50 savings"].route
    with pytest.raises(ValueError, match="restricted to the economic domain"):
        route.evaluate(np.array([route.limit]), extrapolate=True)


# the Linear and PCHIP evaluators of the application's module for the decision
# value and the arrival value on 5, 50 and 500 nodes from -30 to 50; the
# rounding allowance of each comparison is 64 times the machine epsilon times
# the largest absolute value at the nodes


VALUE_EVALUATORS = [
    pytest.param("Linear", "decision", id="linear-decision-value"),
    pytest.param("Linear", "arrival", id="linear-arrival-value"),
    pytest.param("pchip", "decision", id="pchip-decision-value"),
    pytest.param("pchip", "arrival", id="pchip-arrival-value"),
]


@pytest.mark.parametrize(("word", "value"), VALUE_EVALUATORS)
def test_the_error_of_a_value_evaluator_falls_at_each_refinement_of_its_nodes(
    value_interpolations, word, value
):
    """The largest error off the nodes of the evaluator falls from 5 to 50
    nodes and from 50 to 500, unless it lies within the rounding allowance
    already."""
    rows = [getattr(value_interpolations[(word, count)], value) for count in (5, 50, 500)]
    assert all(
        fine.error < coarse.error or coarse.error <= coarse.allowance
        for coarse, fine in zip(rows, rows[1:])
    )


@pytest.mark.parametrize(("word", "value"), VALUE_EVALUATORS)
def test_the_record_of_a_value_interpolation_counts_its_1000_points_as_interpolated(
    value_interpolations, word, value
):
    """The record of the comparison at 5, 50 and 500 nodes counts each of the
    1000 points of the fixed sample as interpolated and none as
    extrapolated."""
    rows = [getattr(value_interpolations[(word, count)], value) for count in (5, 50, 500)]
    assert all((row.interpolated, row.extrapolated) == (1000, 0) for row in rows)


@pytest.mark.parametrize(
    "value",
    [pytest.param("decision", id="decision-value"), pytest.param("arrival", id="arrival-value")],
)
def test_the_error_of_the_linear_value_evaluator_lies_within_its_interpolation_bound(
    value_interpolations, value
):
    """At 5, 50 and 500 nodes the largest error off the nodes of the Linear
    evaluator lies within Δ² max|v″|/8, Δ the spacing of the nodes, and the
    rounding allowance."""
    rows = [getattr(value_interpolations[("Linear", count)], value) for count in (5, 50, 500)]
    assert all(row.error <= row.bound + row.allowance for row in rows)


def test_the_applications_pchip_gives_zero_interior_and_three_point_end_slopes_at_six_nodes(
    application,
):
    """At the nodes 0 to 5 with the values 0, 1, 0.5, 0.5, 2 and -1, where the
    secants on the two sides of each interior node differ in sign or one is
    zero, the PCHIP evaluator of the application's module gives the interior
    slopes zero and the end slopes the three-point estimates 1.75 and
    -5.25."""
    evaluator = application.Pchip(range(6), [0.0, 1.0, 0.5, 0.5, 2.0, -1.0])
    assert evaluator.slopes.tolist() == [1.75, 0.0, 0.0, 0.0, 0.0, -5.25]


def test_the_applications_pchip_limits_an_end_slope_to_three_times_the_end_secant(application):
    """At the nodes 0, 3, 3.2 and 4 with the values 0, 0.3, -2 and 1 the
    three-point estimate at the first node, 10.975, exceeds three times the
    first secant 0.1, whose sign differs from the second secant's, and the
    first slope of the PCHIP evaluator of the application's module is
    3 × 0.1 = 0.3."""
    evaluator = application.Pchip([0.0, 3.0, 3.2, 4.0], [0.0, 0.3, -2.0, 1.0])
    assert evaluator.slopes[0] == pytest.approx(0.3)


# the nodes, the values, the slopes and the absolute tolerance of each
# comparison at unequally spaced nodes; the first row is derived by hand from
# the rules, and both rows are the slopes that SciPy 1.14.1's
# PchipInterpolator gives
UNEQUALLY_SPACED_NODES = [
    pytest.param(
        [0.0, 1.0, 3.0, 3.5],
        [0.0, 1.0, 2.0, 4.0],
        [7 / 6, 9 / 13, 20 / 19, 4.7],
        None,
        id="slopes-derived-by-hand",
    ),
    pytest.param(
        [0.0, 0.1, 3.0, 4.0],
        [0.0, 0.01, 30.0, 31.0],
        [0.0, 0.15177125506072875, 1.6085073025827212, 0.0],
        1e-15,
        id="end-slopes-set-to-zero",
    ),
]


@pytest.mark.parametrize(("nodes", "values", "slopes", "absolute"), UNEQUALLY_SPACED_NODES)
def test_the_applications_pchip_gives_the_slopes_of_scipys_interpolator_at_unequal_spacing(
    application, nodes, values, slopes, absolute
):
    """At unequally spaced nodes the interior slope of the PCHIP evaluator of
    the application's module is the harmonic mean of the two secants
    weighted by the widths, and its end slope the three-point estimate, zero
    where its sign differs from the end secant's."""
    assert application.Pchip(nodes, values).slopes.tolist() == pytest.approx(
        slopes, rel=1e-12, abs=absolute
    )


# the derivatives of the evaluators of the decision value on five nodes, at
# the node -10 and at a point 10⁻⁹ to its left
SIDES_OF_A_NODE = [-10.0 - 1e-9, -10.0]


@pytest.mark.parametrize(
    "word", [pytest.param("Linear", id="linear"), pytest.param("pchip", id="pchip")]
)
def test_a_value_evaluator_offers_the_derivatives_that_its_family_records(
    value_evaluators_on_five_nodes, word
):
    """The evaluator offers, on the coordinate m and with a scalar value, the
    derivative of each order that the registered family of its word
    records."""
    offered = value_evaluators_on_five_nodes[word].derivatives
    assert [
        (derivative.coordinate, derivative.order, derivative.shape) for derivative in offered
    ] == [("m", order, ()) for order in families()[word].derivatives]


def test_the_slopes_of_the_linear_evaluator_differ_on_the_two_sides_of_a_node(
    value_evaluators_on_five_nodes,
):
    """The first derivative of the Linear evaluator of the concave decision
    value is larger left of the node -10 than at it."""
    left, right = value_evaluators_on_five_nodes["Linear"].derivative(SIDES_OF_A_NODE, 1)
    assert left > right


def test_the_first_derivative_of_the_pchip_evaluator_is_continuous_at_a_node(
    value_evaluators_on_five_nodes,
):
    """The first derivative of the PCHIP evaluator differs by less than 10⁻⁶
    on the two sides of the node -10."""
    first = value_evaluators_on_five_nodes["pchip"].derivative(SIDES_OF_A_NODE, 1)
    assert np.ptp(first) < 1e-6


def test_the_second_derivative_of_the_pchip_evaluator_jumps_at_a_node(
    value_evaluators_on_five_nodes,
):
    """The second derivative of the PCHIP evaluator differs by more than 10⁻⁶
    on the two sides of the node -10."""
    second = value_evaluators_on_five_nodes["pchip"].derivative(SIDES_OF_A_NODE, 2)
    assert 1e-6 < np.ptp(second)


def test_the_derivative_of_pchip_on_500_nodes_lies_near_the_authored_envelope_condition(
    application, baseline_closed_form, gridded_envelope_condition
):
    """On 500 nodes from -30 to 50 the first derivative of the PCHIP
    evaluator of the decision value lies within a relative 10⁻⁴ of the
    authored envelope condition D_{m}V = c^(-ρ), at the 1000 points of the
    fixed sample."""
    fine, sample = np.linspace(-30.0, 50.0, 500), application.evaluation_sample(-30.0, 50.0)
    authored = gridded_envelope_condition(m=sample, c=baseline_closed_form.consumption(sample))
    evaluator = application.Pchip(fine, baseline_closed_form.value(fine))
    assert np.max(np.abs(evaluator.derivative(sample) - authored) / authored) < 1e-4


# the converged policy near the borrowing limit, on total wealth from 10⁻³
# to 1


# the mark of the three tests of this part, each of which reads the solution
# that the gridded route computes on the grid of savings near the limit
NEAR_LIMIT_KNOWN_FAILURE = pytest.mark.xfail(
    strict=True,
    reason="The test expects the gridded route to compute the solution on 50 savings from "
    "L + 10⁻⁴ to L + 2, a grid that lies below zero, as the notebook of the application, "
    "`closed-form-and-grid.ipynb`, does under its heading `Near the borrowing limit`. Today "
    "the route takes in the human wealth 0 at its first step, where its natural borrowing "
    "limit is 0 and no saving of that grid lies above it, and it refuses the grid: `!Linear "
    "needs at least two nodes; it is given 0`.",
)


@NEAR_LIMIT_KNOWN_FAILURE
@pytest.mark.parametrize(
    ("measure", "bound"),
    [
        pytest.param("policy_error", 1e-8, id="relative-policy-error"),
        pytest.param("euler", 1e-8, id="relative-euler-residual"),
        pytest.param("bellman", 1e-10, id="scaled-bellman-residual"),
    ],
)
def test_near_the_borrowing_limit_the_converged_policy_meets_the_closed_form(
    near_limit_checks, measure, bound
):
    """Near the natural borrowing limit the largest relative policy error and
    the largest relative Euler residual of the converged policy lie below
    10⁻⁸, and its largest scaled Bellman residual below 10⁻¹⁰."""
    assert getattr(near_limit_checks, measure) < bound


@NEAR_LIMIT_KNOWN_FAILURE
def test_the_record_of_the_near_limit_checks_counts_its_61_points_as_interpolated(
    near_limit_checks,
):
    """The record of the checks near the limit counts each of its 61 points
    as interpolated and none as extrapolated."""
    assert (near_limit_checks.interpolated, near_limit_checks.extrapolated) == (61, 0)


@NEAR_LIMIT_KNOWN_FAILURE
def test_the_converged_policy_near_the_limit_refuses_a_point_below_its_first_pair(
    perfect_foresight_near_route, baseline_closed_form
):
    """The Linear evaluator of the converged policy of the gridded route
    near the limit, whose savings start at L + 10⁻⁴, refuses the resources
    L + 10⁻⁵."""
    with pytest.raises(ValueError, match="outside the closed node interval"):
        perfect_foresight_near_route.policy(baseline_closed_form.limit + 1e-5)


# the failures of the endogenous grid iteration


def test_the_gridded_route_is_refused_at_its_limit_of_iterations(
    application, perfect_foresight_solutions
):
    """The route on 5 savings from -40 to 60, limited to three iterations,
    is refused when it reaches that limit before it converges."""
    with pytest.raises(ValueError, match="limit of iterations"):
        application.gridded_route(perfect_foresight_solutions.comparisons[5].gridded, iterations=3)


def test_the_gridded_route_refuses_a_marginal_value_that_is_not_finite(application):
    """At ρ = 400, where the marginal value underflows, the route on 5 savings
    from -40 to 60 is refused for a value that is not finite."""
    # the count of savings n_a, then the bounds a_min and a_max
    stage = application.gridded_stage(
        5, -40.0, 60.0, {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "ρ": 400.0}}
    )
    with pytest.raises(ValueError, match="not finite"):
        application.gridded_route(stage)


def test_the_gridded_route_refuses_an_extension_that_leaves_the_feasible_set(
    application,
):
    """At ρ = 2.5, on 5 savings from 0.5 to 0.6, above the limit of every
    step, and from a first iterate on the resources 1.5 to 1.6 with
    consumption from 1 to 2, the route is refused when the endpoint-secant
    extension leaves the feasible set."""
    narrow = np.linspace(0.5, 0.6, 5)
    # the count of savings n_a, then the bounds a_min and a_max
    stage = application.gridded_stage(
        5, 0.5, 0.6, {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "ρ": 2.5}}
    )
    with pytest.raises(ValueError, match="leaves the feasible set"):
        application.gridded_route(stage, initial=(narrow + 1.0, np.linspace(1.0, 2.0, 5)))


def test_the_gridded_route_computes_human_wealth_step_by_step(application):
    """The route computes human wealth by the stage's lines from the zero
    that the last period takes in, and reaches the limit of the closed form,
    h[>] = h_lim - 1 with the limit L_lim on savings, while its consumption
    reaches the closed form's at the 401 levels of resources from -30 to 50,
    on 50 savings from -40 to 60."""
    found = application.comparison(50, -40.0, 60.0, np.linspace(-30.0, 50.0, 401))
    closed = application.closed_form_stage()
    assert found.route.human_wealth == pytest.approx(closed.par["h_lim"].value - 1, abs=1e-9)
    assert found.route.limit == pytest.approx(closed.par["L_lim"].value, abs=1e-9)
    assert found.difference < 1e-9 and found.route.change < 1e-12


# the refusals of the scalar evaluators


# each construction that a scalar evaluator of the application refuses, given
# the module, with a phrase of the refusal. An evaluator is constructed from
# its nodes, then its values, and is then called at a point, differentiated at
# a point to an order, or extended to points by the endpoint-secant extension
# whose argument is the natural borrowing limit
EVALUATOR_REFUSALS = [
    pytest.param(
        lambda application: application.Linear([0.0], [1.0]),
        "at least two nodes",
        id="one-node",
    ),
    pytest.param(
        lambda application: application.Pchip([0.0, 1.0, 2.0], [1.0, 2.0]),
        "one value aligned with each node",
        id="a-value-missing",
    ),
    pytest.param(
        lambda application: application.Linear([0.0, 1.0], [[1.0, 2.0], [3.0, 4.0]]),
        "one-dimensional",
        id="values-on-two-coordinates",
    ),
    pytest.param(
        lambda application: application.Linear([0.0, 2.0, 1.0], [1.0, 2.0, 3.0]),
        "strictly increasing",
        id="nodes-out-of-order",
    ),
    pytest.param(
        lambda application: application.Pchip([0.0, 1.0, 1.0], [1.0, 2.0, 3.0]),
        "neither sorted nor merged",
        id="a-repeated-node",
    ),
    pytest.param(
        lambda application: application.Linear([0.0, math.inf], [1.0, 2.0]),
        "not finite",
        id="a-node-that-is-not-finite",
    ),
    pytest.param(
        lambda application: application.Pchip([0.0, 1.0], [math.nan, 2.0]),
        "not finite",
        id="a-value-that-is-not-finite",
    ),
    # 2^53 + 1 has no floating-point number of its own and converts to 2^53
    pytest.param(
        lambda application: application.Linear([2**53, 2**53 + 1], [1.0, 2.0]),
        "merges distinct nodes",
        id="nodes-that-the-conversion-merges",
    ),
    pytest.param(
        lambda application: application.Linear([0.0, 1.0], [1.0, 2.0])(1.5),
        "outside the closed node interval",
        id="a-point-outside-the-nodes",
    ),
    pytest.param(
        lambda application: application.Pchip([0.0, 1.0, 2.0], [1.0, 2.0, 4.0])(-0.5),
        "PCHIP extrapolation is refused",
        id="a-pchip-extrapolation",
    ),
    pytest.param(
        lambda application: application.Linear([0.0, 1.0], [1.0, 2.0]).derivative(0.5, 2),
        "offers the derivatives of orders 1",
        id="a-derivative-order-not-offered",
    ),
    # the point -2 lies below the limit -1
    pytest.param(
        lambda application: application.Linear([0.0, 1.0], [0.5, 1.0]).extend(
            [-2.0], application.EndpointSecant(-1.0)
        ),
        "restricted to the economic domain",
        id="an-extension-below-the-limit",
    ),
    # the secant 1.9 of the first interval gives c = 0.1 - 0.5 × 1.9 < 0 at
    # the point -0.5
    pytest.param(
        lambda application: application.Linear([0.0, 1.0], [0.1, 2.0]).extend(
            [-0.5], application.EndpointSecant(-1.0)
        ),
        "leaves the feasible set",
        id="an-infeasible-extension",
    ),
]


@pytest.mark.parametrize(("construction", "words"), EVALUATOR_REFUSALS)
def test_the_scalar_evaluators_refuse_data_and_points_outside_their_rules(
    application, construction, words
):
    """The Linear and PCHIP evaluators of the application refuse data that
    are not one finite value for each of two or more strictly increasing
    finite nodes, a point outside the nodes, a PCHIP extrapolation and a
    derivative order not offered, and the endpoint-secant extension refuses
    a point at or below its limit and an infeasible value, with a message
    that names the condition."""
    with pytest.raises(ValueError) as refused:
        construction(application)
    assert words in str(refused.value)
