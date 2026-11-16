"""The values of derived parameters at a calibration: the value of a
definition and the order of evaluation, the branch that a definition by cases
chooses, infinite values and the declared sets that hold them, the conditions
that such values give, the kernels that compute the values, the natural
borrowing limit of the buffer-stock model, and the definitions table, the
sheet and a card that print derived parameters."""

import functools
import json
import math
import warnings

import numpy
import pytest
from application_files import (
    BUFFER_STOCK_BASELINE_CALIBRATION,
    MARKET_RESOURCES,
    PERFECT_FORESIGHT_CALIBRATION,
    consumption_at_human_wealth,
)
from stage_builders import (
    calibration_refusal_sentence,
    declared_set_of,
    methodized_copy,
    stage_from_text,
    undecided_memberships,
)
from stage_texts import (
    GROWTH_LINE,
    HUMAN_WEALTH_DEFINITION,
    HUMAN_WEALTH_RIGHT_SIDE_BY_CASES,
    RESOURCES_LINE,
    ZERO_DRAW_PROBABILITY_LINE,
    buffer_stock_text,
    perfect_foresight_text,
)

from bellman.native.hypergraphs import copy_native
from bellman.native.predicates import Member
from bellman.refusal_examples import EXPLICIT_POLICY
from bellman.refusals import ConstructionError
from bellman.stage.calibration_requirements import declared_set_terms, membership, predicate_value
from bellman.syntax import terms

# human wealth by cases, on a declared set that holds the infinity of its
# second branch
BY_CASES = f"h : ℝ_{{+∞}} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}"


# human wealth by cases with a finite second branch
FINITE = "h := if Γ < R then 1/(1 - Γ/R) else 1000"


# the second branch has no real value at ρ = 2, where it divides by zero, nor
# at ρ = 5/2, where it takes the square root of a negative number
UNDEFINED = "h := if Γ < R then 1/(1 - Γ/R) else 1/(ρ - 2) + (ρ - 3)^(1/2)"


# human wealth with a floor on its divisor, which the calibration does not
# reach: 1 - Γ/R = 1/52 exceeds 1/100
FLOORED = "h := 1/max(1 - Γ/R, 1/100, 1/200)"


# two parameters that a calibration gives as integers, N = 2 and M = 4
INTEGERS = "h := max(N, M)^(-1)"


# max and min of two integers written as numbers, under a negative integer
# power
MAX_OF_INTEGERS = "h := max(1, 2)^(-1)"
MIN_OF_INTEGERS = "h := min(2, 4)^(-2)"


# a definition by cases whose two branches are integers, under a negative
# integer power: h is 1/2 where Γ < R and 1/3 otherwise
INTEGER_BRANCHES = "h0 := if Γ < R then 2 else 3\nh := h0^(-1)"


# the same two branches under arithmetic that is exact in integers and rounds
# in floats: (h0^60 + 1) - h0^60 is 1 in integers and 0 in floats, and
# calibration, whose value of h0 is a float, gives h the value 1/(1 - Γ/R)
EXACT_INTEGERS = "h0 := if Γ < R then 2 else 3\nh := (h0^60 + 1) - h0^60 + 1/(1 - Γ/R)"


def declarations_and_first_block(text):
    """A stage text up to its block `dcsn_to_cntn`: its declarations and its
    first block, whose encoding is small."""
    return text[: text.index("[id=dcsn_to_cntn")]


def perfect_foresight_stage(*lines, changes=(), first_block_alone=False):
    """The symbolic stage of the perfect-foresight text with `lines` after the
    growth factor and each pair of `changes` replaced, whole or with its first
    block alone."""
    declared = "".join(line + "\n" for line in lines)
    text = perfect_foresight_text((GROWTH_LINE, GROWTH_LINE + declared), *changes)
    return stage_from_text(declarations_and_first_block(text) if first_block_alone else text)


def condition_of_the_definition(stage, name):
    """The one condition that a stage records for the definition of the
    derived parameter `name`."""
    (owned,) = [
        item
        for item in stage.obligations()
        if item.entries and str(item.entries[0]).endswith(f":derived:{name}")
    ]
    return owned


@pytest.fixture(scope="module")
def cached_perfect_foresight_stage():
    """`cached_perfect_foresight_stage(*lines, changes=())`: the stage that
    `perfect_foresight_stage` makes, one stage for each text, which a test
    that binds it copies first."""
    return functools.cache(perfect_foresight_stage)


@pytest.fixture(scope="module")
def human_wealth_stage(cached_perfect_foresight_stage):
    """`human_wealth_stage(definition)`: the symbolic perfect-foresight stage
    with `definition` as human wealth, and N and M on ℤ for `INTEGERS`."""

    def make(definition):
        integer_lines = ("N : ℤ", "M : ℤ") if definition == INTEGERS else ()
        return cached_perfect_foresight_stage(
            *integer_lines, changes=((HUMAN_WEALTH_DEFINITION, definition),)
        )

    return make


@pytest.fixture(scope="module")
def cases_with_infinity_versions(human_wealth_stage):
    """The stage of human wealth `BY_CASES`, symbolic and calibrated at a
    finite and at an infinite value, by name."""
    symbolic = human_wealth_stage(BY_CASES)
    return {
        "symbolic": symbolic,
        "finite": copy_native(symbolic).calibrate(PERFECT_FORESIGHT_CALIBRATION),
        "infinite": copy_native(symbolic).calibrate({**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}),
    }


# R = 1.04 and Γ = 1.02 at the calibration, so that 1 - Γ/R is 1/52
@pytest.mark.parametrize(
    "definition, change, expected",
    [
        pytest.param(BY_CASES, {}, 52.0, id="by cases, first branch"),
        pytest.param(BY_CASES, {"Γ": 1.05}, math.inf, id="by cases, growth above interest"),
        pytest.param(FINITE, {}, 52.0, id="a finite branch, first branch"),
        pytest.param(FINITE, {"Γ": 1.04}, 1000.0, id="a finite branch, growth equal to interest"),
        pytest.param(FINITE, {"Γ": 1.05}, 1000.0, id="a finite branch, growth above interest"),
        pytest.param("h := if Γ <= R then 1 else 2", {}, 1.0, id="at most"),
        pytest.param("h := if Γ = R then 1 else 2", {}, 2.0, id="equal to"),
        pytest.param("h := if Γ >= R then 1 else 2", {}, 2.0, id="at least"),
        pytest.param("h : ℝ_{-∞} := if Γ > R then 1 else -inf", {}, -math.inf, id="minus inf"),
        pytest.param(
            "h := if R - Γ > 1 then 1 else if R - Γ > 0 then 2 else 3", {}, 2.0, id="nested"
        ),
        pytest.param(
            "h := if max(Γ, R) = R then min(Γ, R) else log(R)",
            {},
            1.02,
            id="min, max and log in a test and a branch",
        ),
        pytest.param(INTEGER_BRANCHES, {}, 1 / 2, id="integer branches, first branch"),
        pytest.param(
            INTEGER_BRANCHES, {"Γ": 1.04}, 1 / 3, id="integer branches, growth equal to interest"
        ),
        pytest.param(
            INTEGER_BRANCHES, {"Γ": 1.05}, 1 / 3, id="integer branches, growth above interest"
        ),
        pytest.param(
            EXACT_INTEGERS, {}, 52.0, id="integer branches in floating point, first branch"
        ),
        # h0 = 3 gives h = 1/(1 - 1.05/1.04) = -104
        pytest.param(
            EXACT_INTEGERS,
            {"Γ": 1.05},
            -104.0,
            id="integer branches in floating point, second branch",
        ),
        pytest.param(FLOORED, {}, 52.0, id="max of three"),
        pytest.param(MAX_OF_INTEGERS, {}, 0.5, id="max of two integers"),
        pytest.param(MIN_OF_INTEGERS, {}, 0.25, id="min of two integers"),
        pytest.param(INTEGERS, {"N": 2, "M": 4}, 0.25, id="max of two integer parameters"),
    ],
)
def test_calibration_computes_human_wealth_from_its_definition_and_keeps_no_value_of_it(
    definition, change, expected, human_wealth_stage
):
    """Calibration computes human wealth from its definition, by cases from the
    chosen branch, and the calibration that the stage keeps holds none."""
    values = {**PERFECT_FORESIGHT_CALIBRATION, **change}
    bound = copy_native(human_wealth_stage(definition)).calibrate(values)
    assert bound.par["h"].value == pytest.approx(expected)
    assert "h" not in bound.bindings.calibration


# θ_min = 0.3 and ξ_u = 0.1, and 1 - Γ/R is 1/52
@pytest.mark.parametrize(
    "definition, expected",
    [
        pytest.param("x := min(ξ_u, θ_min)", 0.1, id="the least of two"),
        pytest.param("x := max(ξ_u, θ_min)", 0.3, id="the greatest of two"),
        pytest.param("x := min(θ_min, ξ_u, 1/R)", 0.1, id="the least of three"),
        pytest.param("x := max(θ_min, ξ_u, 1/R)", 1 / 1.04, id="the greatest of three"),
        pytest.param("x := min(ξ_u)", 0.1, id="min of one argument"),
        pytest.param("x := 1/max(1 - Γ/R, 1/2)", 2.0, id="a floor on a divisor"),
        pytest.param("x := -min(ξ_u, θ_min)*log(exp(2))", -0.2, id="min with log and exp"),
        pytest.param("x := max(h, 60) - min(h, 60)", 8.0, id="min and max of human wealth"),
    ],
)
def test_min_and_max_take_the_least_and_the_greatest_argument_and_calibration_keeps_none(
    definition, expected
):
    """Calibration gives min and max the least and the greatest argument, and
    the calibration that the stage keeps holds no value of them."""
    stage = perfect_foresight_stage("θ_min : (0, 1]", "ξ_u : ℝ₊", definition)
    bound = stage.calibrate({**PERFECT_FORESIGHT_CALIBRATION, "θ_min": 0.3, "ξ_u": 0.1})
    assert bound.par["x"].value == pytest.approx(expected)
    assert "x" not in bound.bindings.calibration


def test_the_branch_that_the_test_does_not_choose_is_not_evaluated(human_wealth_stage):
    """At Γ = R the first branch of human wealth by cases, whose division by
    zero refuses the definition without cases, is not evaluated."""
    bound = copy_native(human_wealth_stage(BY_CASES)).calibrate(
        {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}
    )
    assert bound.par["h"].value == math.inf and "h" not in bound.bindings.calibration
    with pytest.raises(ConstructionError, match="the divisor `1 - Γ/R` is 0.0"):
        perfect_foresight_stage().calibrate({**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04})


@pytest.mark.parametrize(
    "reading, finite_value",
    [
        pytest.param("1 - h", -51.0, id="in a formula"),
        pytest.param("-h", -52.0, id="under a sign"),
        pytest.param("max(h, 60)", 60.0, id="in a call"),
        pytest.param("if h > 60 then 1 else 0", 0.0, id="in a test"),
        pytest.param("if Γ < R then 1 else h", 1.0, id="as the branch that the test chooses"),
        pytest.param("h", 52.0, id="as the whole right side"),
    ],
)
def test_a_definition_that_reads_an_infinite_value_has_no_value(
    reading, finite_value, derived_parameter_stages
):
    """A definition w that reads h takes its value where h is finite, and the
    calibration is refused at w where h is infinite, naming that value."""
    change = (HUMAN_WEALTH_DEFINITION, f"{BY_CASES}\nw := {reading}")
    values = derived_parameter_stages.calibration
    bound = derived_parameter_stages.stage(change).calibrate({"calibration": values})
    assert bound.par["w"].value == pytest.approx(finite_value)
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage(change).calibrate({"calibration": {**values, "Γ": 1.04}})
    error = refused.value
    # w is defined on line 9, after the definition of h
    assert (error.rule, error.address) == (
        "derived-parameter",
        f"{derived_parameter_stages.origin}:9",
    )
    assert (
        f"the derived parameter w, defined as `{reading}`, has no value: the value inf "
        "of h is no finite number; "
    ) in error.message
    assert error.write == "Write parameter values at which the definition of w has a value"


@pytest.fixture(scope="module")
def min_bound_stage():
    """The perfect-foresight stage with a parameter b declared on a set whose
    bound calls min, and q := max(β, R) on the declared set (0, 3)."""
    return perfect_foresight_stage("b : ℝ₊₊ @ (0, min(R, 2))", "q : (0, 3) := max(β, R)")


def test_a_bound_that_calls_min_is_decided_at_calibration(min_bound_stage):
    """Calibration admits b below min(R, 2) and refuses b above it, naming
    the condition at the value of R."""
    values = {**PERFECT_FORESIGHT_CALIBRATION, "b": 1.0}
    assert undecided_memberships(copy_native(min_bound_stage).calibrate(values)) == []
    assert (
        "the condition b < min(R, 2) of the declared set at R = 1.04"
        in calibration_refusal_sentence(min_bound_stage, {**values, "b": 1.5})
    )


def test_a_definition_that_calls_max_is_held_to_its_declared_set(min_bound_stage):
    """A calibration at which q := max(β, R) lies outside its declared set
    is refused at q."""
    # R = 3.5 gives q = 3.5, outside (0, 3)
    values = {**PERFECT_FORESIGHT_CALIBRATION, "b": 1.0, "R": 3.5}
    assert "derived parameter 'q'" in calibration_refusal_sentence(min_bound_stage, values)


# a parameter T on ℝ_{+∞}, the real numbers with positive infinity added,
# which an endpoint reads
T_LINE = ("T : ℝ_{+∞}",)


# a definition w by cases on (0, 10), whose second branch is finite
W_ON_AN_INTERVAL = "w : (0, 10) := if Γ < R then 1/(1 - Γ/R) else 1"


# Each row declares h by cases on a set. With T the upper endpoint of (0, T],
# the infinite value lies in the set where T is infinite and outside it where
# T is 100. The definition w takes its second branch, 1, where Γ = R, and its
# first branch, 52, where Γ < R.
BY_CASES_ON_SETS = [
    *[
        pytest.param((), declared, "h", {"Γ": gamma}, value, None, id=label)
        for declared, words in (
            ("ℝ_{+∞}", "the reals with the infinity"),
            ("ℝ̄", "the extended reals"),
            ("(0, inf]", "an interval closed at infinity"),
            ("(0, 1) \\/ [2, inf]", "a union closed at infinity"),
        )
        for gamma, value, where in ((1.02, 52.0, "finite"), (1.04, math.inf, "infinite"))
        for label in (f"admitted, {words}, {where}",)
    ],
    pytest.param((), "[60, inf]", "h", {"Γ": 1.04}, math.inf, None, id="admitted, above 60"),
    pytest.param(
        (),
        "[60, inf]",
        "h",
        {},
        None,
        (
            "derived parameter 'h'",
            "lies outside the declared set [60, inf] at R = 1.04, Γ = 1.02",
        ),
        id="refused, a finite value below 60",
    ),
    pytest.param(
        T_LINE,
        "(0, T]",
        "h",
        {"Γ": 1.04, "T": math.inf},
        math.inf,
        None,
        id="admitted, to T = inf",
    ),
    pytest.param(
        T_LINE,
        "(0, T]",
        "h",
        {"Γ": 1.04, "T": 100.0},
        None,
        (
            "derived parameter 'h'",
            "the value inf of h",
            "lies outside the declared set (0, T]",
        ),
        id="refused, to T = 100, infinite",
    ),
    pytest.param((W_ON_AN_INTERVAL,), "ℝ_{+∞}", "w", {"Γ": 1.04}, 1.0, None, id="admitted, w"),
    pytest.param(
        (W_ON_AN_INTERVAL,),
        "ℝ_{+∞}",
        "w",
        {},
        None,
        (
            "derived parameter 'w'",
            "lies outside the declared set (0, 10) at R = 1.04, Γ = 1.02",
        ),
        id="refused, w at its first branch",
    ),
]


@pytest.mark.parametrize("lines, declared, name, change, expected, phrases", BY_CASES_ON_SETS)
def test_calibration_holds_the_value_of_a_definition_by_cases_to_its_declared_set(
    lines, declared, name, change, expected, phrases, cached_perfect_foresight_stage
):
    """Calibration admits a value of a definition by cases inside its declared
    set and refuses one outside, whether the set holds the infinity or not."""
    definition = f"h : {declared} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}"
    stage = cached_perfect_foresight_stage(
        *lines, changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    values = {**PERFECT_FORESIGHT_CALIBRATION, **change}
    if phrases is None:
        bound = copy_native(stage).calibrate(values)
        assert bound.par[name].value == pytest.approx(expected)
        assert undecided_memberships(bound) == []
    else:
        sentence = calibration_refusal_sentence(stage, values)
        assert [phrase for phrase in phrases if phrase not in sentence] == []


@pytest.mark.parametrize(
    "version, status",
    [
        pytest.param("symbolic", "required", id="symbolic"),
        pytest.param("finite", "established", id="a finite value"),
        pytest.param("infinite", "established", id="the infinite value"),
    ],
)
def test_a_definition_with_an_infinite_branch_owns_the_condition_of_a_value_in_its_set(
    version, status, cases_with_infinity_versions
):
    """Human wealth by cases owns one condition, a value in ℝ_{+∞}, which
    calibration establishes at a finite and at an infinite value."""
    owned = condition_of_the_definition(cases_with_infinity_versions[version], "h")
    assert (owned.condition, owned.status) == ("arithmetic-definedness", status)
    assert owned.explanation == (
        f"The derived parameter h, defined as `{HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}`, must have a "
        "value in ℝ_{+∞} at the calibration."
    )


# definitions on a declared set whose endpoint is a name or which has a
# condition, each with the lines that it declares
NAMED_ENDPOINT = (("T : ℝ₊₊",), "h : (0, T] := 1/(1 - Γ/R)")
NAMED_ENDPOINT_BY_CASES = (T_LINE, f"h : (0, T] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}")
CONDITION_BY_CASES = ((), f"h : ℝ̄ @ (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}")


@pytest.mark.parametrize(
    "lines, definition, change",
    [
        pytest.param(*NAMED_ENDPOINT, {"T": 100.0}, id="a named endpoint"),
        pytest.param(*NAMED_ENDPOINT_BY_CASES, {"T": 100.0}, id="by cases, a named endpoint"),
        pytest.param(
            *NAMED_ENDPOINT_BY_CASES, {"Γ": 1.04, "T": math.inf}, id="by cases, T and h infinite"
        ),
        pytest.param(*CONDITION_BY_CASES, {}, id="by cases, a condition"),
        pytest.param(*CONDITION_BY_CASES, {"Γ": 1.04}, id="by cases, a condition, h infinite"),
    ],
)
def test_a_calibration_that_the_declared_set_admits_establishes_the_condition_of_the_definition(
    lines, definition, change, cached_perfect_foresight_stage
):
    """A calibration that the declared set admits establishes the condition of
    the definition, where the set has a named endpoint or a condition."""
    typed = cached_perfect_foresight_stage(
        *lines, changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    bound = copy_native(typed).calibrate({**PERFECT_FORESIGHT_CALIBRATION, **change})
    assert undecided_memberships(bound) == []
    owned = condition_of_the_definition(bound, "h")
    assert (owned.condition, owned.status) == ("arithmetic-definedness", "established")


@pytest.mark.parametrize(
    "lines, definition",
    [
        pytest.param(*NAMED_ENDPOINT, id="a named endpoint"),
        pytest.param(*NAMED_ENDPOINT_BY_CASES, id="by cases, a named endpoint"),
        pytest.param(*CONDITION_BY_CASES, id="by cases, a condition"),
    ],
)
def test_the_symbolic_stage_requires_the_condition_of_a_value_in_the_reals_with_the_infinity(
    lines, definition, cached_perfect_foresight_stage
):
    """Before calibration a definition on a set with a named endpoint or a
    condition requires a value in ℝ_{+∞}."""
    typed = cached_perfect_foresight_stage(
        *lines, changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    owned = condition_of_the_definition(typed, "h")
    assert (owned.condition, owned.status) == ("arithmetic-definedness", "required")
    assert owned.explanation.endswith("must have a value in ℝ_{+∞} at the calibration.")


@pytest.mark.parametrize(
    "calibrated, status",
    [
        pytest.param(False, "required", id="symbolic"),
        pytest.param(True, "established", id="calibrated"),
    ],
)
def test_a_definition_by_cases_without_an_infinite_branch_owns_the_condition_of_a_real_value(
    calibrated, status, human_wealth_stage
):
    """A definition by cases with no infinite branch owns the condition of a
    finite real value, as a definition that calls log does."""
    plain = human_wealth_stage(FINITE)
    version = copy_native(plain).calibrate(PERFECT_FORESIGHT_CALIBRATION) if calibrated else plain
    owned = condition_of_the_definition(version, "h")
    assert (owned.condition, owned.status) == ("arithmetic-definedness", status)
    assert owned.explanation.endswith("must have a finite real value at the calibration.")


@pytest.mark.parametrize(
    "definition, printed",
    [
        pytest.param(
            BY_CASES,
            f"h = inf : ℝ_{{+∞}} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            id="the reals with the infinity",
        ),
        pytest.param(
            f"h : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            f"h = inf : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            id="an interval closed at infinity",
        ),
    ],
)
def test_the_record_of_a_definition_by_cases_prints_its_infinite_value_with_its_set(
    definition, printed, human_wealth_stage
):
    """The record of human wealth by cases, calibrated at its infinite value,
    prints the value `inf` before its set and its definition."""
    infinite = copy_native(human_wealth_stage(definition)).calibrate(
        {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}
    )
    assert str(infinite.par["h"]) == printed


@pytest.mark.parametrize(
    "definition, phrases",
    [
        pytest.param(
            BY_CASES,
            ("h  ∈ ℝ_{+∞},  := if Γ < R then 1/(1 − Γ/R) else ∞", "= ∞"),
            id="the reals with the infinity",
        ),
        pytest.param(
            f"h : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            ("  h  ∈ (0, ∞],  := if Γ < R then 1/(1 − Γ/R) else ∞\n     = ∞\n",),
            id="an interval closed at infinity",
        ),
    ],
)
def test_the_card_of_a_calibrated_definition_prints_an_infinite_value_as_infinity(
    definition, phrases, human_wealth_stage
):
    """The card of human wealth by cases, calibrated at its infinite value,
    prints the infinity of its set, of its branch and of its value as `∞`."""
    infinite = copy_native(human_wealth_stage(definition)).calibrate(
        {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}
    )
    card = str(infinite.definitions.denote("perfect_foresight:derived:h"))
    assert [phrase for phrase in phrases if phrase not in card] == []


# debt on ℝ₊ bounded by human wealth
DEBT = "debt : ℝ₊ @ [0, h)"


# human wealth declared on ℝ_{+∞}, the real numbers with positive infinity
# added, with no definition
H_DECLARED = "h : ℝ_{+∞}"


# debt on ℝ bounded by human wealth: its condition refuses a negative debt
DEBT_ON_THE_REALS = "debt : ℝ @ [0, h)"


@pytest.mark.parametrize(
    "definition, change, expected, phrases",
    [
        pytest.param(BY_CASES, {"debt": 10.0}, 52.0, None, id="admitted, derived, finite"),
        pytest.param(
            BY_CASES, {"Γ": 1.04, "debt": 1e6}, math.inf, None, id="admitted, derived, infinite"
        ),
        pytest.param(
            H_DECLARED, {"h": math.inf, "debt": 1e6}, math.inf, None, id="admitted, declared"
        ),
        pytest.param(
            BY_CASES,
            {"debt": 60.0},
            None,
            ("parameter 'debt'", "the condition debt < h of the declared set at h = 51.99"),
            id="refused, derived, debt above a finite h",
        ),
    ],
)
def test_an_endpoint_that_is_the_bare_name_of_a_parameter_reads_as_its_value_finite_or_infinite(
    definition, change, expected, phrases, cached_perfect_foresight_stage
):
    """The endpoint h of the set of debt is read at its value, finite or
    infinite, whether h is derived or declared."""
    stage = cached_perfect_foresight_stage(
        DEBT_ON_THE_REALS, changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    values = {**PERFECT_FORESIGHT_CALIBRATION, **change}
    if phrases is None:
        bound = copy_native(stage).calibrate(values)
        assert bound.par["h"].value == pytest.approx(expected)
        assert undecided_memberships(bound) == []
    else:
        sentence = calibration_refusal_sentence(stage, values)
        assert [phrase for phrase in phrases if phrase not in sentence] == []


@pytest.mark.parametrize(
    "debt, definition, change, reason",
    [
        pytest.param(debt, definition, change, reason, id=f"{part}, {kind} h")
        for debt, part, reason in (
            (DEBT_ON_THE_REALS, "on the reals", "does not satisfy the condition debt >= 0"),
            (DEBT, "on the positive reals", "lies outside the declared set ℝ₊"),
        )
        # Γ = R = 1.04 gives h = inf
        for definition, change, kind in (
            (BY_CASES, {"Γ": 1.04}, "derived"),
            (H_DECLARED, {"h": math.inf}, "declared"),
        )
    ],
)
def test_a_negative_debt_is_refused_by_the_first_of_its_two_sets_that_excludes_it(
    debt, definition, change, reason, cached_perfect_foresight_stage
):
    """Where h is infinite, a debt of -1 is refused by ℝ₊ in ℝ₊ @ [0, h), and
    by the condition debt >= 0 of [0, h) in ℝ @ [0, h)."""
    stage = cached_perfect_foresight_stage(debt, changes=((HUMAN_WEALTH_DEFINITION, definition),))
    values = {**PERFECT_FORESIGHT_CALIBRATION, **change, "debt": -1.0}
    phrases = ("parameter 'debt'", f"the value -1.0 {reason}")
    sentence = calibration_refusal_sentence(stage, values)
    assert [phrase for phrase in phrases if phrase not in sentence] == []


@pytest.mark.parametrize(
    "lines, changes, change",
    [
        pytest.param(
            ("w : (h, inf)",), ((HUMAN_WEALTH_DEFINITION, BY_CASES),), {"Γ": 1.04}, id="derived"
        ),
        pytest.param(("T : ℝ̄", "w : (T, inf)"), (), {"T": math.inf}, id="declared"),
    ],
)
def test_an_interval_whose_lower_endpoint_is_the_infinity_holds_no_number(lines, changes, change):
    """A value of w is refused where the lower endpoint of its interval is
    valued at the infinity."""
    stage = perfect_foresight_stage(*lines, changes=changes)
    values = {**PERFECT_FORESIGHT_CALIBRATION, **change, "w": 1e6}
    assert "the value 1000000.0 lies outside the declared set" in calibration_refusal_sentence(
        stage, values
    )


# each set of extended reals, a name for it, the values that it holds and
# the values that it does not hold
EXTENDED_REALS = (
    ("ℝ̄", "the extended reals", (5.0, math.inf, -math.inf), ()),
    ("ℝ_{+∞}", "the reals with the infinity", (5.0, math.inf), (-math.inf,)),
    ("ℝ_{-∞}", "the reals with the negative infinity", (5.0, -math.inf), (math.inf,)),
    ("(0, inf]", "an interval closed at infinity", (5.0, math.inf), (-math.inf, 0.0)),
)


# a name for each value of a parameter declared on a set of extended reals
VALUE_NAMES = {
    5.0: "a finite number",
    math.inf: "the infinity",
    -math.inf: "the negative infinity",
    0.0: "zero",
}


@pytest.mark.parametrize(
    "declared, value, inside",
    [
        pytest.param(declared, value, inside, id=f"{words}, {VALUE_NAMES[value]} {outcome}")
        for declared, words, held, not_held in EXTENDED_REALS
        for values, inside, outcome in ((held, True, "admitted"), (not_held, False, "refused"))
        for value in values
    ],
)
def test_a_parameter_declared_on_the_extended_reals_takes_the_values_that_its_set_holds(
    declared, value, inside, cached_perfect_foresight_stage
):
    """A parameter on a set of extended reals admits a finite number and the
    infinity of each side that the set reaches, and refuses other values."""
    stage = cached_perfect_foresight_stage(f"T : {declared}")
    values = {**PERFECT_FORESIGHT_CALIBRATION, "T": value}
    if inside:
        assert undecided_memberships(copy_native(stage).calibrate(values)) == []
    else:
        assert (
            f"the value {value!r} lies outside the declared set {declared}"
        ) in calibration_refusal_sentence(stage, values)


@pytest.fixture(scope="module")
def sets_of_numbers():
    """The perfect-foresight stage with T declared on the extended reals, a
    named set of extended reals and a named interval."""
    return perfect_foresight_stage("T : ℝ̄", "Xe := {x : ℝ̄ | x >= 0}", "Xr := [0, inf)")


# each form of a set, a name for it, and whether it holds the infinity and
# the negative infinity, None where neither procedure decides
INFINITIES_HELD = (
    ("ℝ", "the reals", (False, False)),
    ("ℝ₊₊", "the positive reals", (False, False)),
    ("ℤ", "the integers", (False, False)),
    ("ℝ̄", "the extended reals", (True, True)),
    ("ℝ_{+∞}", "the reals with the infinity", (True, False)),
    ("ℝ_{-∞}", "the reals with the negative infinity", (False, True)),
    ("ℝ_{±∞}", "the reals with both infinities", (True, True)),
    ("(0, inf)", "an interval open at infinity", (False, False)),
    ("(0, inf]", "an interval closed at infinity", (True, False)),
    ("[-inf, 0)", "an interval closed at the negative infinity", (False, True)),
    ("[-inf, inf]", "the closed extended interval", (True, True)),
    ("(0, T]", "an interval closed at a parameter at infinity", (True, False)),
    ("(0, T)", "an interval open at a parameter at infinity", (False, False)),
    ("{1, …, 5}", "a range of integers", (False, False)),
    ("ℝ̄ @ (0, inf)", "the extended reals with a condition open at infinity", (False, False)),
    ("ℝ̄ @ (0, inf]", "the extended reals with a condition closed at infinity", (True, False)),
    ("(0, 1) \\/ (1, inf]", "a union closed at infinity", (True, False)),
    ("ℝ̄ \\ (0, inf]", "the extended reals less an interval closed at infinity", (False, True)),
    ("ℝ \\ {0}", "the reals less zero", (False, False)),
    ("Xe", "a named set of extended reals", (True, False)),
    ("Xr", "a named interval open at infinity", (False, False)),
    ("Foo", "an undefined name", (None, None)),
)


@pytest.mark.parametrize(
    "written, value, answer",
    [
        *[
            pytest.param(written, infinity, answer, id=f"{words}, {sign}")
            for written, words, held in INFINITIES_HELD
            for infinity, answer, sign in zip(
                (math.inf, -math.inf), held, ("the infinity", "the negative infinity")
            )
        ],
        *[
            pytest.param(written, 5.0, True, id=f"{words}, a finite number")
            for written, words, _ in INFINITIES_HELD
            if written in ("ℝ̄", "ℝ_{+∞}", "ℝ_{-∞}", "ℝ_{±∞}")
        ],
    ],
)
def test_membership_and_the_value_of_a_condition_give_one_answer_at_an_infinity_or_a_number(
    written, value, answer, sets_of_numbers
):
    """`membership`, for a value and its set, and `predicate_value`, for a
    recorded condition, give one answer at each infinity in each form of a
    set, and at the number 5 in a set of extended reals."""
    at = {**PERFECT_FORESIGHT_CALIBRATION, "T": math.inf}
    setexpr = declared_set_of(f"x : {written}")
    definitions = dict(sets_of_numbers.definitions)
    judged = membership(sets_of_numbers, definitions, setexpr, value, at)[0]
    assert (judged if judged in (True, False) else None) is answer
    predicate = Member(terms.Sym(terms.Constant("w")), setexpr)
    named = declared_set_terms(sets_of_numbers)
    assert predicate_value(predicate, {**at, "w": value}, named).value is answer


# h by cases and h declared on ℝ_{+∞}, each with the calibrations at which h
# is infinite and 52, and the words that name its infinite value
INFINITE_HUMAN_WEALTH = (
    (
        "derived h",
        BY_CASES,
        {"Γ": 1.04},
        {},
        f"h = inf (the derived parameter h := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES})",
    ),
    ("declared h", H_DECLARED, {"h": math.inf}, {"h": 52.0}, "h = inf"),
)


# the declared set of debt is ℝ₊ @ (0, bound), and ℝ @ (-inf, -h) for the
# bound -h, which lies below zero
@pytest.mark.parametrize(
    "bound, declared, definition, at_infinity, supplies",
    [
        pytest.param(
            bound,
            f"ℝ @ (-inf, {bound})" if bound == "-h" else f"ℝ₊ @ (0, {bound})",
            definition,
            at_infinity,
            supplies,
            id=f"{words}, {kind}",
        )
        for bound, words in (
            ("2*h", "twice h"),
            ("h + 1", "h plus one"),
            ("h/2", "half of h"),
            ("max(h, 1)", "max of h and one"),
            ("-h", "minus h"),
        )
        for kind, definition, at_infinity, _, supplies in INFINITE_HUMAN_WEALTH
    ],
)
def test_a_bound_that_computes_with_a_name_valued_at_an_infinity_has_no_value(
    bound, declared, definition, at_infinity, supplies
):
    """A bound of a declared set that computes with h has no value where h is
    infinite: the calibration is refused at that bound."""
    stage = perfect_foresight_stage(
        f"debt : {declared}", changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    sentence = calibration_refusal_sentence(
        stage, {**PERFECT_FORESIGHT_CALIBRATION, **at_infinity, "debt": 1.0}
    )
    phrases = (
        "parameter 'debt'",
        f"the bound `{bound}` of the declared set {declared} has no value at {supplies}: the "
        "value inf of h is no finite number; a declared set is defined at the values only where "
        "each of its bounds has a value; ",
    )
    assert [phrase for phrase in phrases if phrase not in sentence] == [], sentence


@pytest.mark.parametrize(
    "bound, definition, at_infinity, at_finite",
    [
        pytest.param(bound, definition, at_infinity, at_finite, id=f"{words}, {kind}")
        for bound, words in (
            ("2*inf", "twice the infinity"),
            ("max(inf, 1)", "max of the infinity and one"),
        )
        for kind, definition, at_infinity, at_finite, _ in INFINITE_HUMAN_WEALTH
    ],
)
def test_a_bound_that_computes_with_the_written_infinity_is_refused_with_advice_at_any_calibration(
    bound, definition, at_infinity, at_finite
):
    """A bound that computes with the written `inf` has no value whether h is
    infinite or finite, and the refusal advises another bound."""
    declared = f"ℝ₊ @ (0, {bound})"
    reason = "has no value: it computes with `inf`, and no arithmetic of infinities is defined"
    stage = perfect_foresight_stage(
        f"debt : {declared}", changes=((HUMAN_WEALTH_DEFINITION, definition),)
    )
    sentence = calibration_refusal_sentence(
        stage, {**PERFECT_FORESIGHT_CALIBRATION, **at_infinity, "debt": 1.0}
    )
    phrases = (
        "parameter 'debt'",
        f"the bound `{bound}` of the declared set {declared} {reason}; a declared set is "
        "defined at the values only where each of its bounds has a value; ",
    )
    assert [phrase for phrase in phrases if phrase not in sentence] == [], sentence
    assert sentence.endswith("; write another bound"), sentence
    finite = calibration_refusal_sentence(
        stage, {**PERFECT_FORESIGHT_CALIBRATION, **at_finite, "debt": 1.0}
    )
    assert reason in finite and finite.endswith("; write another bound"), finite


def test_the_declared_set_of_a_setting_is_refused_at_configuration_where_its_bound_has_no_value(
    human_wealth_stage,
):
    """Configuration refuses a value of the setting tol under
    `setting-outside-set` where the bound h + 1 of its set has no value."""
    configured = methodized_copy(human_wealth_stage(BY_CASES), "tol : (0, h + 1)\n").calibrate(
        {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}
    )
    with pytest.raises(ConstructionError) as refused:
        copy_native(configured).configure({"tol": 0.5})
    assert refused.value.rule == "setting-outside-set"
    assert "the bound `h + 1` of the declared set (0, h + 1) has no value" in refused.value.message


def test_a_key_inf_of_a_calibration_source_is_no_name_of_a_stage():
    """A key `inf` of a calibration source gives the written infinity in a
    bound no value, in a stage that declares no name `inf`."""
    stray = perfect_foresight_stage("debt : ℝ₊ @ (0, 2*inf)")
    values = {**PERFECT_FORESIGHT_CALIBRATION, "debt": 1.0, "inf": 3.0}
    assert "it computes with `inf`" in calibration_refusal_sentence(stray, values)


def test_a_key_inf_of_a_settings_source_is_no_name_of_a_stage():
    """A key `inf` of a settings source gives the written infinity in the bound
    of the set of a setting no value."""
    with_setting = methodized_copy(perfect_foresight_stage(), "tol : (0, 2*inf)\n").calibrate(
        PERFECT_FORESIGHT_CALIBRATION
    )
    with pytest.raises(ConstructionError) as refused:
        copy_native(with_setting).configure({"tol": 0.5, "inf": 3.0})
    assert "it computes with `inf`" in refused.value.message


# the law of motion of resources with h added and taken away, so that the
# line computes with human wealth
COMPUTES_WITH_H = (RESOURCES_LINE, "    m = R_n*k + 1 + h - h           :: [id=market_resources]")


@pytest.fixture(scope="module")
def resources_line_stage():
    """`resources_line_stage(definition)`: the symbolic stage with `definition`
    as h and the line `COMPUTES_WITH_H`; a test that binds it binds a copy."""

    @functools.cache
    def make(definition):
        return stage_from_text(
            perfect_foresight_text((HUMAN_WEALTH_DEFINITION, definition), COMPUTES_WITH_H)
        )

    return make


def conditions_of_the_resources_line(stage):
    """The conditions that `stage` records for the line of resources, each as
    its name and its explanation."""
    return sorted(
        (item.condition, item.explanation)
        for item in stage.obligations()
        if "arvl_to_dcsn" in item.explanation
    )


@pytest.mark.parametrize(
    "definition, declaration",
    [
        pytest.param(BY_CASES, H_DECLARED, id="by cases on the reals with the infinity"),
        pytest.param(
            "h : (0, inf] := 1/(1 - Γ/R)",
            "h : (0, inf]",
            id="a formula on an interval closed at infinity",
        ),
    ],
)
def test_a_line_that_reads_a_derived_parameter_whose_set_may_hold_an_infinity_owns_its_conditions(
    definition, declaration, resources_line_stage
):
    """A line that computes with a derived parameter whose set may hold an
    infinity owns the conditions that a parameter on that set gives it."""
    owned = conditions_of_the_resources_line(resources_line_stage(definition))
    assert owned != []
    assert owned == conditions_of_the_resources_line(resources_line_stage(declaration))


@pytest.mark.parametrize(
    "definition",
    [
        pytest.param(HUMAN_WEALTH_DEFINITION, id="no declared set"),
        pytest.param("h : (0, 100) := 1/(1 - Γ/R)", id="a finite interval"),
        # a set of extended reals whose condition excludes both infinities
        # holds neither
        pytest.param(
            "h : ℝ̄ @ (0, 100) := 1/(1 - Γ/R)", id="the extended reals with a finite condition"
        ),
    ],
)
def test_a_line_that_reads_a_derived_parameter_whose_set_holds_no_infinity_owns_no_condition(
    definition, resources_line_stage
):
    """A line that computes with a derived parameter whose set holds no
    infinity owns no condition, where by cases on ℝ_{+∞} it owns some."""
    conditions_by_cases = conditions_of_the_resources_line(resources_line_stage(BY_CASES))
    assert conditions_by_cases != []
    assert conditions_of_the_resources_line(resources_line_stage(definition)) == []


def test_a_line_that_reads_human_wealth_by_cases_owns_the_conditions_of_finite_arithmetic(
    resources_line_stage,
):
    """A line that computes with human wealth by cases on ℝ_{+∞} owns the
    conditions that its operands are finite and that the set is numeric."""
    owned = conditions_of_the_resources_line(resources_line_stage(BY_CASES))
    assert (
        "finite-real-arithmetic",
        "The operands of Sub at arvl_to_dcsn.market_resources must be finite real numbers.",
    ) in owned
    assert (
        "numeric-domain-compatibility",
        "The set ℝ_{+∞} used in arithmetic at arvl_to_dcsn.market_resources must be numeric.",
    ) in owned


def test_the_conditions_of_a_line_stay_required_at_an_infinite_value(resources_line_stage):
    """At the infinite value of human wealth by cases, the conditions of a
    line that computes with it stay required."""
    at_infinity = copy_native(resources_line_stage(BY_CASES)).calibrate(
        {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04}
    )
    assert {
        item.status for item in at_infinity.obligations() if "market_resources" in item.explanation
    } == {"required"}


def test_a_power_of_an_infinite_value_is_refused_with_a_sentence_that_is_true_of_it():
    """A line with the square root of human wealth is admitted at a finite
    value and refused at the infinite one with a sentence true of it."""
    power = (RESOURCES_LINE, "    m = R_n*k + h^(1/2)             :: [id=market_resources]")
    rooted = stage_from_text(perfect_foresight_text((HUMAN_WEALTH_DEFINITION, BY_CASES), power))
    assert copy_native(rooted).calibrate(PERFECT_FORESIGHT_CALIBRATION).par["h"].value == (
        pytest.approx(52.0)
    )
    sentence = calibration_refusal_sentence(rooted, {**PERFECT_FORESIGHT_CALIBRATION, "Γ": 1.04})
    assert "calibration h = inf makes" in sentence and "h > 0 false" not in sentence


@pytest.fixture(scope="module")
def encoded_versions():
    """Stages with their first block alone: debt bounded by human wealth by
    cases, symbolic and at a finite and an infinite value, and min and max."""
    small = perfect_foresight_stage(
        DEBT, changes=((HUMAN_WEALTH_DEFINITION, BY_CASES),), first_block_alone=True
    )
    values = PERFECT_FORESIGHT_CALIBRATION
    return {
        "symbolic": small,
        "finite": copy_native(small).calibrate({**values, "debt": 10.0}),
        "infinite": copy_native(small).calibrate({**values, "Γ": 1.04, "debt": 1e6}),
        "min and max": perfect_foresight_stage(
            changes=((HUMAN_WEALTH_DEFINITION, "h := max(min(Γ, R), 1/2)"),),
            first_block_alone=True,
        ),
    }


@pytest.mark.parametrize("version", ["symbolic", "finite", "infinite", "min and max"])
def test_the_encoding_of_a_stage_with_a_derived_parameter_is_a_strict_json_document_of_the_schema(
    version, encoded_versions, encoding_validator
):
    """The encoding of each stage is a valid document of the schema in strict
    JSON: `json.dumps` and the validator each raise otherwise."""
    written = json.dumps(encoded_versions[version].encoding(), allow_nan=False, ensure_ascii=False)
    encoding_validator.validate(json.loads(written))


def test_the_encoding_writes_an_infinite_value_as_the_float_inf(encoded_versions):
    """The encoding at the infinite value of human wealth writes it `{"float":
    "inf"}`, where the encoding at a finite value holds no such float."""
    finite_text, infinite_text = (
        json.dumps(encoded_versions[name].encoding(), allow_nan=False, ensure_ascii=False)
        for name in ("finite", "infinite")
    )
    assert '{"float": "inf"}' in infinite_text
    assert '{"float": "inf"}' not in finite_text


# human wealth read through q, which the file defines after h, and a power of
# the negative number -q; R_n written through log and exp
EVALUATION_ORDER = (
    (HUMAN_WEALTH_DEFINITION, "h := 1/(1 - q)\nq := Γ/R\nz := (-q)^ρ"),
    ("R_n := R/Γ", "R_n := exp(log(R) - log(Γ))"),
)


@pytest.fixture(scope="module")
def evaluation_order_stage(derived_parameter_stages):
    """The symbolic perfect-foresight stage with the definitions
    `EVALUATION_ORDER`; a test that binds it binds a copy."""
    return derived_parameter_stages.stage(*EVALUATION_ORDER)


@pytest.fixture(scope="module")
def evaluation_order_calibrated(evaluation_order_stage, derived_parameter_stages):
    """A copy of `evaluation_order_stage` calibrated at the calibration of
    the perfect-foresight stage, at which ρ = 2."""
    return copy_native(evaluation_order_stage).calibrate(
        {"calibration": derived_parameter_stages.calibration}
    )


# q = Γ/R at Γ = 1.02 and R = 1.04
Q = 1.02 / 1.04


def test_a_derived_parameter_is_evaluated_after_the_derived_parameters_it_reads(
    evaluation_order_stage, evaluation_order_calibrated
):
    """Human wealth h, which reads q, takes its value 1/(1 - q) although the
    file defines q after h."""
    assert list(evaluation_order_stage.par)[4:] == ["h", "q", "z", "R_n"]
    assert evaluation_order_calibrated.par["h"].value == pytest.approx(1 / (1 - Q))


def test_a_power_of_a_negative_base_takes_its_value_where_its_exponent_is_an_integer(
    evaluation_order_calibrated,
):
    """z := (-q)^ρ takes the value q² at ρ = 2, although the declared set of
    ρ holds numbers that are no integers."""
    assert evaluation_order_calibrated.par["z"].value == pytest.approx(Q**2)


def test_the_condition_of_a_power_of_a_negative_base_is_established_with_its_value_as_evidence(
    evaluation_order_calibrated,
):
    """The one condition that z owns is established at the calibration, with
    the value of z as its evidence."""
    owned = condition_of_the_definition(evaluation_order_calibrated, "z")
    assert owned.status == "established"
    assert owned.evidence == (f"calibration z = {evaluation_order_calibrated.par['z'].value!r}",)


def test_the_definitions_table_counts_the_derived_parameters(evaluation_order_calibrated):
    """The definitions table, `stage.definitions.list()`, heads its group of
    derived parameters with their number."""
    assert "DERIVED PARAMETERS 4" in str(evaluation_order_calibrated.definitions.list())


def test_the_sheet_of_a_stage_lists_the_derived_parameters_by_their_definitions(
    evaluation_order_calibrated,
):
    """The sheet of a stage prints the number of its derived parameters and
    each by its definition, in the order of the file."""
    assert "derived parameters       4   h := 1/(1 - q), q := Γ/R, z := (-q)^ρ" in str(
        evaluation_order_calibrated
    )


def test_the_card_of_a_definition_prints_a_superscript_exponent_and_the_parameters_it_reads(
    derived_parameter_stages,
):
    """The card of h := Γ^2 prints Γ² and lists Γ, the one parameter that it
    reads, under `Definitions referenced`."""
    stage = derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, "h := Γ^2"))
    card = str(stage.definitions.denote("perfect_foresight:derived:h"))
    assert "  h  := Γ²\n" in card
    assert card.split("Definitions referenced\n")[1].splitlines()[:-1] == [
        "  Γ     perfect_foresight:parameter:Γ"
    ]


def test_the_kernel_of_a_law_of_motion_takes_the_declared_parameters_that_it_reads(
    evaluation_order_calibrated,
):
    """The kernel of the law of motion of resources, which reads R_n, takes
    R and Γ as its arguments."""
    kernel = evaluation_order_calibrated.builder["arvl", "dcsn"]["Pushforward"].kernel()
    assert kernel.parameters == ("R", "Γ")


def test_the_kernel_writes_log_and_exp_as_the_functions_of_numpy(evaluation_order_calibrated):
    """The kernel of the law of motion writes R_n through its definition,
    with log and exp as NumPy's functions."""
    kernel = evaluation_order_calibrated.builder["arvl", "dcsn"]["Pushforward"].kernel()
    assert "    R_n = np.exp(np.log(R) - np.log(Γ))\n" in kernel.python


def test_the_compiled_kernel_of_a_law_of_motion_gives_its_value(evaluation_order_calibrated):
    """The compiled kernel of the law of motion m = R_n*k + 1 gives R/Γ + 1
    at k = 1."""
    law = evaluation_order_calibrated.builder["arvl", "dcsn"]["Pushforward"]
    kernel = law.kernel()
    # the arguments are k, then the parameters R and Γ
    assert law.compile_kernel()(numpy.array([1.0]), *kernel.parameter_values) == pytest.approx(
        [1.04 / 1.02 + 1]
    )


# the calibration of the kernels, where `INTEGERS` alone reads N and M
KERNEL_VALUES = {**PERFECT_FORESIGHT_CALIBRATION, "N": 2, "M": 4}


@pytest.fixture(scope="module")
def consumption_kernel(human_wealth_stage):
    """`consumption_kernel(definition)`: the kernel of the consumption line of
    the explicit policy, compiled, and its parameter values."""

    @functools.cache
    def make(definition):
        explicit = {"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"}
        stage = methodized_copy(human_wealth_stage(definition), explicit).calibrate(
            {"calibration": KERNEL_VALUES}
        )
        consumption = stage.builder.policy.primitives["consumption:Aggregation"]
        kernel = consumption.kernel()
        held = dict(zip(kernel.parameters, kernel.parameter_values, strict=True))
        return kernel, consumption.compile_kernel(), held

    return make


def calibrated_wealth(stage, change):
    """The value of human wealth in a copy of `stage` calibrated at
    `KERNEL_VALUES` with the values `change`."""
    return copy_native(stage).calibrate({**KERNEL_VALUES, **change}).par["h"].value


@pytest.mark.parametrize(
    "definition, parameters",
    [
        pytest.param(BY_CASES, ("β", "ρ", "R", "Γ"), id="by cases"),
        pytest.param(FLOORED, ("β", "ρ", "R", "Γ"), id="max of three"),
        pytest.param(INTEGERS, ("β", "ρ", "R", "N", "M"), id="max of two integer parameters"),
    ],
)
def test_the_kernel_of_the_explicit_policy_takes_the_declared_parameters_alone(
    definition, parameters, consumption_kernel
):
    """The kernel of the consumption line of the explicit policy takes as
    arguments the declared parameters it reads, and no derived parameter."""
    kernel, _, _ = consumption_kernel(definition)
    assert kernel.parameters == parameters


def test_the_kernel_holds_the_calibrated_values_of_integer_parameters(consumption_kernel):
    """The kernel of a definition that reads N and M holds the values 2 and
    4 that the calibration gives them."""
    _, _, held = consumption_kernel(INTEGERS)
    assert held["N"] == 2 and held["M"] == 4


@pytest.mark.parametrize(
    "definition, line",
    [
        pytest.param(BY_CASES, f"# derived parameter: {BY_CASES}\n", id="the comment line"),
        pytest.param(
            BY_CASES,
            "    h = by_cases(Γ < R, lambda: 1/(1 - Γ/R), lambda: np.inf)\n",
            id="a conditional",
        ),
        pytest.param(
            FLOORED, "    h = 1/np.maximum(np.maximum(1 - Γ/R, 1/100), 1/200)\n", id="max of three"
        ),
        # the first argument is a float where no argument is surely one
        pytest.param(
            INTEGERS, "    h = np.maximum(1.0*N, M)**(-1)\n", id="max of two integer parameters"
        ),
        pytest.param(
            MIN_OF_INTEGERS, "    h = np.minimum(1.0*2, 4)**(-2)\n", id="min of two integers"
        ),
        pytest.param(
            INTEGER_BRANCHES,
            "    h0 = by_cases(Γ < R, lambda: 2, lambda: 3)\n",
            id="integer branches",
        ),
        pytest.param(INTEGER_BRANCHES, "    h = h0**(-1)\n", id="a power of a derived parameter"),
    ],
)
def test_the_kernel_writes_a_derived_parameter_through_its_definition(
    definition, line, consumption_kernel
):
    """The kernel writes a derived parameter through its definition, a
    conditional through `by_cases` and min and max as NumPy writes them."""
    kernel, _, _ = consumption_kernel(definition)
    assert line in kernel.python


# R = 1.04: the test of each definition by cases chooses the first branch
# where Γ < R and the second where Γ >= R
@pytest.mark.parametrize(
    "definition, change",
    [
        pytest.param(BY_CASES, {"Γ": 1.02}, id="by cases, the first branch"),
        pytest.param(BY_CASES, {"Γ": 1.05}, id="by cases, the infinite branch"),
        pytest.param(FINITE, {"Γ": 1.02}, id="a finite branch, the first branch"),
        pytest.param(FINITE, {"Γ": 1.05}, id="a finite branch, the second branch"),
        *[
            pytest.param(INTEGER_BRANCHES, {"Γ": gamma}, id=f"integer branches, {where}")
            for gamma, where in (
                (1.02, "the first branch"),
                (1.04, "the second branch where growth equals interest"),
                (1.05, "the second branch where growth exceeds interest"),
            )
        ],
        # the second branch is complex at ρ = 5/2, and no warning announces it
        pytest.param(
            UNDEFINED, {"ρ": 2.5, "Γ": 1.02}, id="an undefined branch at 2.5, the first branch"
        ),
        # the chosen integer branch is a float, as calibration's value is, so
        # that arithmetic which is exact in integers gives the kernel what it
        # gives calibration; h does not depend on the branch in floats
        pytest.param(
            EXACT_INTEGERS, {"Γ": 1.02}, id="integer branches in floating point, the first branch"
        ),
        pytest.param(
            EXACT_INTEGERS, {"Γ": 1.05}, id="integer branches in floating point, the second branch"
        ),
    ],
)
def test_the_compiled_kernel_gives_at_one_value_the_consumption_at_the_calibrated_wealth(
    definition, change, consumption_kernel, human_wealth_stage
):
    """At one value of each parameter the compiled kernel gives the
    consumption at the value that calibration gives human wealth: the branch
    that the test chooses, as a float."""
    _, compiled, held = consumption_kernel(definition)
    wealth = calibrated_wealth(human_wealth_stage(definition), change)
    consumption = compiled(MARKET_RESOURCES, **{**held, **change})
    assert numpy.allclose(consumption, consumption_at_human_wealth(wealth))


@pytest.mark.parametrize(
    "definition, change",
    [
        # at Γ = R = 1.04 the first branch divides by zero
        pytest.param(BY_CASES, {"Γ": 1.04}, id="by cases, a first branch without a value"),
        pytest.param(FINITE, {"Γ": 1.04}, id="a finite branch, a first branch without a value"),
        # at ρ = 2 the second branch divides by zero
        pytest.param(
            UNDEFINED, {"ρ": 2.0, "Γ": 1.02}, id="an undefined branch, a second branch at 2"
        ),
    ],
)
def test_the_compiled_kernel_evaluates_no_branch_that_the_test_does_not_choose(
    definition, change, consumption_kernel, human_wealth_stage
):
    """At one value of each parameter the compiled kernel gives the consumption
    at the calibrated human wealth without evaluating a branch that the test
    does not choose, whose warning would be an error."""
    _, compiled, held = consumption_kernel(definition)
    wealth = calibrated_wealth(human_wealth_stage(definition), change)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        consumption = compiled(MARKET_RESOURCES, **{**held, **change})
    assert numpy.allclose(consumption, consumption_at_human_wealth(wealth))


@pytest.mark.parametrize(
    "definition, fixed, growths",
    [
        pytest.param(BY_CASES, {}, (1.02, 1.04, 1.05), id="by cases"),
        pytest.param(FINITE, {}, (1.02, 1.04, 1.05), id="a finite branch"),
        # two integer branches are selected as floats, so that the negative
        # power of the selected value is that of calibration
        pytest.param(INTEGER_BRANCHES, {}, (1.02, 1.04, 1.05), id="integer branches"),
        pytest.param(
            EXACT_INTEGERS, {}, (1.02, 1.05, 1.02), id="integer branches in floating point"
        ),
        # the test holds at each entry, and the second branch, chosen at
        # none, has no real value
        pytest.param(UNDEFINED, {"ρ": 2.0}, (1.02, 1.03, 1.02), id="an undefined branch at 2"),
        pytest.param(UNDEFINED, {"ρ": 2.5}, (1.02, 1.03, 1.02), id="an undefined branch at 2.5"),
    ],
)
def test_the_compiled_kernel_gives_at_each_entry_of_an_array_the_calibrated_consumption(
    definition, fixed, growths, consumption_kernel, human_wealth_stage
):
    """At an array of growth factors the compiled kernel gives at each entry
    the real consumption at the calibrated human wealth: the branch that the
    test chooses there, as a float."""
    _, compiled, held = consumption_kernel(definition)
    stage = human_wealth_stage(definition)
    wealth = [calibrated_wealth(stage, {**fixed, "Γ": gamma}) for gamma in growths]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        consumption = compiled(MARKET_RESOURCES, **{**held, **fixed, "Γ": numpy.array(growths)})
    assert numpy.isrealobj(consumption)
    assert numpy.allclose(consumption, consumption_at_human_wealth(wealth)), definition


@pytest.mark.parametrize(
    "definition",
    [
        pytest.param(FLOORED, id="max of three"),
        pytest.param(MAX_OF_INTEGERS, id="max of two integers"),
        pytest.param(MIN_OF_INTEGERS, id="min of two integers"),
        pytest.param(INTEGERS, id="max of two integer parameters"),
    ],
)
def test_the_compiled_kernel_of_min_and_max_gives_the_value_that_calibration_gives(
    definition, consumption_kernel, human_wealth_stage
):
    """The compiled kernel of min or max of floats or of integers, under a
    negative power, gives the consumption at the calibrated human wealth."""
    kernel, compiled, _ = consumption_kernel(definition)
    wealth = calibrated_wealth(human_wealth_stage(definition), {})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        consumption = compiled(MARKET_RESOURCES, *kernel.parameter_values)
    assert numpy.allclose(consumption, consumption_at_human_wealth(wealth))


# The lowest transitory income ξ_min is the employed floor where unemployment
# has probability zero, and otherwise the lower of that floor and the income
# in unemployment. The natural borrowing limit a_Nat is minus its present
# value where Γ*ψ_min < R, and -inf otherwise. The artificial limit a_Art lies
# above it.
NATURAL_LIMIT = (
    "θ_min : (0, 1]",
    "ψ_min : (0, 1]",
    "ξ_u : ℝ₊",
    "ξ_min := if p_zero = 0 then θ_min else min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))",
    "a_Nat : ℝ_{-∞} := if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf",
    "a_Art : (-inf, 0] @ (a_Nat, inf)",
)


# Γ = R = 1.03 and ψ_min = 0.8, so that the natural limit is -4 times the
# lowest income
LIMIT_VALUES = {**BUFFER_STOCK_BASELINE_CALIBRATION, "θ_min": 0.3, "ξ_u": 0.1, "ψ_min": 0.8}


# the buffer-stock stage with its declarations and its first block alone, in
# the default set, and the whole stage, in the complete set
STAGE_PARTS = [
    pytest.param(True, id="first block alone"),
    pytest.param(False, id="whole stage", marks=pytest.mark.complete_set),
]


@pytest.fixture(scope="module")
def natural_limit_stage():
    """`natural_limit_stage(first_block_alone)`: the buffer-stock stage with
    `NATURAL_LIMIT`, where unemployment may be absent, whole or its first
    block."""

    @functools.cache
    def make(first_block_alone):
        absent = ZERO_DRAW_PROBABILITY_LINE.replace("(0,1)", "[0,1)")
        stated = buffer_stock_text().replace(
            ZERO_DRAW_PROBABILITY_LINE, absent + "".join(line + "\n" for line in NATURAL_LIMIT)
        )
        text = declarations_and_first_block(stated) if first_block_alone else stated
        return stage_from_text(text, "buffer_stock.bl")

    return make


# the employed floor θ_min*(1 - p_zero*ξ_u)/(1 - p_zero) at ξ_u = 0.5
FLOOR = 0.3 * (1 - 0.005 * 0.5) / 0.995


@pytest.mark.parametrize("first_block_alone", STAGE_PARTS)
@pytest.mark.parametrize(
    "change, lowest, limit",
    [
        pytest.param(
            {"a_Art": -0.3}, 0.1, -0.4, id="the unemployment event with positive probability"
        ),
        pytest.param({"ξ_u": 0.5, "a_Art": -1.0}, FLOOR, -4 * FLOOR, id="income above the floor"),
        pytest.param(
            {"p_zero": 0.0, "a_Art": -1.0}, 0.3, -1.2, id="the unemployment event absent"
        ),
        pytest.param(
            {"p_zero": 0.0, "ξ_u": 0.0, "a_Art": -1.0},
            0.3,
            -1.2,
            id="the unemployment event absent, no unemployment income",
        ),
        pytest.param(
            {"ψ_min": 1.0, "a_Art": -50.0}, 0.1, -math.inf, id="growth equal to interest"
        ),
        pytest.param(
            {"ψ_min": 1.0, "R": 1.01, "a_Art": -50.0}, 0.1, -math.inf, id="growth above interest"
        ),
    ],
)
def test_the_natural_borrowing_limit_is_the_negative_present_value_of_the_lowest_income(
    change, lowest, limit, first_block_alone, natural_limit_stage
):
    """Calibration gives the lowest income ξ_min and the natural limit a_Nat,
    minus its present value where Γ*ψ_min < R and -inf otherwise."""
    assert buffer_stock_text().count(ZERO_DRAW_PROBABILITY_LINE) == 1
    stage = natural_limit_stage(first_block_alone)
    bound = copy_native(stage).calibrate({**LIMIT_VALUES, **change})
    assert undecided_memberships(bound) == []
    assert (bound.par["ξ_min"].value, bound.par["a_Nat"].value) == (
        pytest.approx(lowest),
        pytest.approx(limit),
    )


@pytest.mark.parametrize("first_block_alone", STAGE_PARTS)
@pytest.mark.parametrize(
    "change, phrases",
    [
        pytest.param(
            {"a_Art": -0.5},
            (
                "parameter 'a_Art'",
                "the condition a_Art > a_Nat of the declared set at a_Nat = -0.4",
            ),
            id="refused below a finite limit",
        ),
        pytest.param(
            {"p_zero": 0.0, "a_Art": -1.3},
            ("parameter 'a_Art'",),
            id="refused, the unemployment event absent",
        ),
        pytest.param({"ψ_min": 1.0, "a_Art": 0.0}, None, id="admitted, growth equal to interest"),
        pytest.param(
            {"ψ_min": 1.0, "R": 1.01, "a_Art": 0.0}, None, id="admitted, growth above interest"
        ),
    ],
)
def test_an_artificial_borrowing_limit_lies_above_the_natural_one(
    change, phrases, first_block_alone, natural_limit_stage
):
    """An artificial limit below a finite natural limit is refused, and
    every artificial limit is admitted where the natural limit is -inf."""
    assert buffer_stock_text().count(ZERO_DRAW_PROBABILITY_LINE) == 1
    stage = natural_limit_stage(first_block_alone)
    values = {**LIMIT_VALUES, **change}
    if phrases is None:
        bound = copy_native(stage).calibrate(values)
        assert undecided_memberships(bound) == []
        assert bound.par["a_Nat"].value == -math.inf
    else:
        sentence = calibration_refusal_sentence(stage, values)
        assert [phrase for phrase in phrases if phrase not in sentence] == []


@pytest.mark.parametrize("first_block_alone", STAGE_PARTS)
@pytest.mark.parametrize(
    "change",
    [
        pytest.param(None, id="symbolic"),
        pytest.param({"a_Art": -0.3}, id="a finite natural limit"),
        pytest.param({"a_Art": -50.0, "ψ_min": 1.0}, id="an infinite natural limit"),
    ],
)
def test_the_encoding_of_the_buffer_stock_stage_with_its_limits_is_a_document_of_the_schema(
    change, first_block_alone, natural_limit_stage, encoding_validator
):
    """The encoding of the stage, symbolic and at a finite and an infinite
    natural limit, is a valid document in strict JSON: each call raises
    otherwise."""
    assert buffer_stock_text().count(ZERO_DRAW_PROBABILITY_LINE) == 1
    stage = natural_limit_stage(first_block_alone)
    version = stage if change is None else copy_native(stage).calibrate({**LIMIT_VALUES, **change})
    document = json.dumps(version.encoding(), allow_nan=False, ensure_ascii=False)
    encoding_validator.validate(json.loads(document))


@pytest.mark.parametrize("first_block_alone", STAGE_PARTS)
def test_the_encoding_writes_an_infinite_natural_limit_as_the_float_minus_inf(
    first_block_alone, natural_limit_stage
):
    """The encoding of the stage calibrated where the natural limit is -inf
    writes that value `{"float": "-inf"}`."""
    stage = natural_limit_stage(first_block_alone)
    bound = copy_native(stage).calibrate({**LIMIT_VALUES, "a_Art": -50.0, "ψ_min": 1.0})
    assert '{"float": "-inf"}' in json.dumps(bound.encoding())
