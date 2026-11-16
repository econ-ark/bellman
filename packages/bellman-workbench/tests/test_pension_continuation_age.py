"""Age and its data in the Workbench pension fixtures."""

from pathlib import Path

import pytest

from bellman.distributions.families import label_weights, numeric_value
from bellman.refusals import ConstructionError
from bellman.trellis import connection_report, elaborate_trellis, load_recipe

from workbench_support import (
    PENSIONS,
    PENSIONS_RECIPE,
    PENSIONS_WORKING_YEARS,
    pensions_copy,
    pensions_life_cycle,
)


@pytest.fixture(
    scope="module",
    params=[(3, 16, 101), (7, 50, 68), (85, 686, 101)],
    ids=["retirement", "working-years", "life-cycle"],
)
def pension_trellis(request, tmp_path_factory):
    periods, occurrences, terminal_age = request.param
    destination = tmp_path_factory.mktemp("pension-age") / "durables"
    if periods == 85:
        folder = pensions_life_cycle(destination)
    else:
        fixture = PENSIONS if periods == 3 else PENSIONS_WORKING_YEARS
        folder = pensions_copy(destination, fixture)
    path = Path(PENSIONS_RECIPE)
    source = load_recipe(folder / path.parent, path.name)
    trellis = elaborate_trellis(source)
    return source, trellis, periods, occurrences, terminal_age


def zero_value(*state):
    return 0.0


def aggregation_output(builder, field):
    (piece,) = (
        piece for piece in builder.output_kernels["Aggregation"].values()
        if piece.outputs == (field,)
    )
    return piece


def test_pension_fixtures_take_terminal_age(pension_trellis):
    source, trellis, periods, occurrences, terminal_age = pension_trellis
    terminal = trellis["periods"][0]["stages"]["bequest_pa"]
    assert len(trellis["periods"]) == periods
    assert sum(len(period["stages"]) for period in trellis["periods"]) == occurrences
    with pytest.raises(ConstructionError, match="missing 'age'"):
        terminal.check_inputs({"V[>]": zero_value})
    with pytest.raises(ConstructionError, match="Continuation field age"):
        terminal.check_inputs({"V[>]": zero_value, "age": 102})
    terminal.check_inputs({"V[>]": zero_value, "age": terminal_age})

    for period in source["periods"]:
        stages = period["stages"]
        for stage in stages.values():
            assert not stage["calibration"].keys() & {"age", "last_age", "t_age"}
        assert stages["shocks"]["calibration"]["Y"] == [0.0] * 85
        if "survival" in stages:
            assert stages["survival"]["calibration"]["p_s"] == [0.98] * 85


def test_pension_routes_supply_age_without_changing_state_pairs(pension_trellis):
    _, trellis, periods, _, _ = pension_trellis
    report = connection_report(trellis)
    pairs, routes, unfinished = {3: (169, 19, 3), 7: (561, 61, 8), 85: (7857, 853, 86)}[periods]
    assert len(report.pairs) == pairs
    assert len(report.routes) == routes
    assert len(report.diagnostics) == unfinished
    assert {item.rule for item in report.diagnostics} == {"route-incomplete"}

    branch_ages = {"rent": "age_rt", "keep": "age_kp", "adjust": "age_adj"}
    for route in report.routes:
        assert route.backward == "compatible"
        components = [
            (component.required.rsplit(":", 1)[1], component.supplied.rsplit(":", 1)[1])
            for component in route.components
            if component.required.rsplit(":", 1)[1].startswith("age")
        ]
        source = route.source[1]
        if source == "survival" and route.branch == "die":
            assert not components
            continue
        if source == "tenure_pa":
            expected = branch_ages[route.branch]
        elif source in {"survival", "allocation", "contribution", "plan_choice", "payout"}:
            expected = "age_sv"
        else:
            expected = "age"
        assert components == [(expected, expected)]


def test_backward_age_transition_reaches_the_authored_periods(pension_trellis):
    _, trellis, periods, _, terminal_age = pension_trellis
    tenure = trellis["periods"][1]["stages"]["tenure_pa"]
    age = aggregation_output(tenure.builder["cntn", "dcsn"].kernels(), "age_sv")
    assert age.arguments == ("age_rt≻", "age_adj≻", "age_kp≻")
    next_age = terminal_age
    payout_ages = []
    for period in trellis["periods"][1:]:
        next_age = age.function(next_age, next_age, next_age)
        if "payout" in period["stages"]:
            payout_ages.append(next_age)

    first_age = {3: 99, 7: 62, 85: 17}[periods]
    assert next_age == first_age
    assert payout_ages == ([] if periods == 3 else [65])


def test_survival_builders_select_the_same_law_at_the_supplied_age(pension_trellis):
    source, trellis, _, _, _ = pension_trellis
    survival = trellis["periods"][1]["stages"]["survival"]
    baseline = source["periods"][1]["stages"]["survival"]["calibration"]["p_s"]
    probabilities = list(baseline)
    probabilities[65 - 17], probabilities[66 - 17] = 0.75, 0.6
    survival = survival.calibrate({"calibration": {"p_s": probabilities}})

    for age, probability in [(65.0, 0.75), (66.0, 0.6)]:
        inputs = {"age_sv": age, "V_sv[>]": zero_value, "V[>]": zero_value}
        forward = survival.builder["dcsn", "cntn"].kernels(inputs=inputs)
        backward = survival.builder["cntn", "dcsn"].kernels(inputs=inputs)
        extension = forward.laws["DistributionExtension:s"]
        assert backward.laws
        for law in (extension, *backward.laws.values()):
            (declaration,) = law.declarations
            assert declaration.subjects == ("s",)
            assert declaration.formals == ("_age",)
            assert declaration.actuals == ("survival:cntn:age_sv",)
            assert tuple(numeric_value(weight, {}) for weight in label_weights(declaration.term)) == (
                probability, 1 - probability
            )

        value = aggregation_output(backward, "V")
        assert "p_s[age_sv]" in value.kernel
        assert value.arguments == ("age_sv", "V_sv≻", "V≻")
        assert value.function(age, 10.0, 0.0, *value.parameter_values) == pytest.approx(10 * probability)
