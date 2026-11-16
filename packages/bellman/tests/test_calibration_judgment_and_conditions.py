"""What a calibration judges: the order in which it judges declared and
derived values against their sets and names the value that it refuses, and
the conditions of a stage that it decides at the values or leaves
required."""

import functools

import pytest
from application_files import BUFFER_STOCK_BASELINE_CALIBRATION
from stage_builders import stage_from_text
from stage_texts import ZERO_DRAW_PROBABILITY_LINE, buffer_stock_text, changed

from bellman.native import predicates
from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.typing import typed_expressions

# The tests of the order of judgment declare their lines after the probability
# ℘ of a zero transitory draw in the stage file of the buffer-stock
# application, `ZERO_DRAW_PROBABILITY_LINE`, and calibrate at its values with ℘
# = 0.4.
BUFFER_STOCK_VALUES = {**BUFFER_STOCK_BASELINE_CALIBRATION, "p_zero": 0.4}


# the income of an unemployed agent, below the bound ξ_u_sup
UNEMPLOYMENT_INCOME = "ξ_u : ℝ₊ @ [0, ξ_u_sup)"


# the bound of that income, 1/℘ = 2.5
INCOME_BOUND = "ξ_u_sup : ℝ_{+∞} := if p_zero = 0 then inf else 1/p_zero"


# the scale of the employed income, which is 0 at ξ_u = 1/℘
SCALE = "ξ_scale := (1 - p_zero*ξ_u)/(1 - p_zero)"


# the logarithm of that scale, which has no value where the scale is 0
LOG_MEAN = "μ_emp := log(ξ_scale)"


# an artificial borrowing limit above the natural one, a_Nat
ARTIFICIAL_LIMIT = "a_Art : (-inf, 0] @ (a_Nat, inf)"


# the lowest income draw
LOWEST_DRAW = "ξ_min := min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))"


# the natural borrowing limit, which the lowest draw gives
NATURAL_LIMIT = "a_Nat : ℝ_{-∞} := if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf"


# the lines that the natural borrowing limit reads, and values of the two
# lowest shocks and of the artificial limit inside their sets
LIMIT_DEFINITIONS = ("θ_min : (0, 1]", "ψ_min : (0, 1]", INCOME_BOUND, LOWEST_DRAW, NATURAL_LIMIT)
LIMIT_VALUES = {"θ_min": 0.3, "ψ_min": 0.8, "a_Art": -0.1}


# a parameter whose set reads the income and its bound
BETWEEN_INCOME_AND_BOUND = "ξ_mid : (ξ_u, ξ_u_sup)"


# the distance from ξ_mid to the bound
DISTANCE_TO_THE_BOUND = "ξ_gap := ξ_u_sup - ξ_mid"


# a derived parameter 1/℘ declared on the set (0, 2)
DERIVED_UPPER_BOUND = "ξ_cap : (0, 2) := 1/p_zero"


# the refusal of an unemployment income at 1/℘ = 2.5, by its own set
INCOME_REFUSED_AT_ITS_OWN_SET = (
    r"parameter 'ξ_u' .*the value 2\.5 does not satisfy the condition ξ_u < ξ_u_sup of the "
    r"declared set at ξ_u_sup = 2\.5"
)


# three lines in which the set of x reads z, z is defined from y and y from x
CHAIN = ("y := x + 1", "x : (0, z)", "z := 2*y")


# two parameters that bound each other through a derived parameter, and a
# definition that reads one of them
PAIR_BOUNDING_EACH_OTHER = (
    "t_k := 0*p_zero",
    "t_x : ℝ @ (t_y + t_k, 10)",
    "t_y : ℝ @ (t_x + t_k, 10)",
)
READS_T_Y = ("t_g := 2*t_y",)


# a parameter whose set (0, 1/℘) does not hold the value 3 given to it
FAULTY_ALONE = ("t_b := 1/p_zero", "t_w : ℝ @ (0, t_b)")


# a parameter t_n bounded below by t_m, and t_m bounded above by t_a,
# which is defined from t_n
T_N_BOUNDED_BY_T_M = ("t_k := 0*p_zero", "t_n : ℝ @ (t_m + t_k, 10)")
T_M_BOUNDED_BY_T_A = T_N_BOUNDED_BY_T_M + ("t_m : ℝ @ (0, t_a)", "t_a := 2*t_n")


# a stage of one block whose line raises the parameter ρ to the power η
POWER_OF_PARAMETERS = """@stage: parameters
ρ : ℝ
η : ℝ
[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = ρ^η + x :: [id=value]
}
"""


# a stage of one block whose line divides by ρ - η and by its input x
TWO_DIVISORS = """@stage: parameters
ρ : ℝ
η : ℝ
[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = 1/(ρ-η) + 1/x :: [id=value]
}
"""


# denominators that are zero at r = s, and nonzero at r = s + 1 with r and s
# integers that floating-point numbers do not tell apart
EXACT_DENOMINATORS = [
    pytest.param("r/1-s", 2**53 + 1, 2**53, id="integer-division"),
    pytest.param("r/2-s/2", 2**53 + 1, 2**53, id="rational-difference"),
    pytest.param("1/r-1/s", 10**400 + 1, 10**400, id="large-reciprocals"),
    pytest.param("r^(-1)-s^(-1)", 2**53 + 1, 2**53, id="negative-powers"),
    pytest.param("r-s", 10**400 + 1, 10**400, id="large-integers"),
]


# the stages whose conditions the tests of the listing of conditions read
CONDITION_STAGES = [
    "cons",
    "port",
    "ez_savings",
    "cons_savings_iid",
    "sa_savings",
    "cons_calibrated",
    "cons_methodized",
]


def calibrated_buffer_stock(lines, **values):
    """The buffer-stock stage with `lines` declared after its probability of
    a zero draw, calibrated at `BUFFER_STOCK_VALUES` and `values`."""
    declared = "".join(line + "\n" for line in lines)
    text = changed(
        buffer_stock_text(), (ZERO_DRAW_PROBABILITY_LINE, ZERO_DRAW_PROBABILITY_LINE + declared)
    )
    stage = stage_from_text(text, "buffer_stock.bl")
    return stage.calibrate({**BUFFER_STOCK_VALUES, **values})


@pytest.fixture(scope="module")
def cons_dividing_by_rho_minus_6(cons_with_egm_lines_text):
    """`cons_dividing_by_rho_minus_6(binder)`: the symbolic stage of `cons`
    with an explicit policy candidate, whose inverse Euler line adds
    1/(ρ − 6) and whose argmax binds the variable `binder`; made once for
    each binder."""

    @functools.cache
    def make(binder):
        source = changed(
            cons_with_egm_lines_text,
            ("𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])", "𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) + 1/(ρ-6)"),
            (
                "argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])",
                f"argmax_{{{binder} : Γ(m_d)}}(𝑢({binder}) + V[>])",
            ),
        )
        return stage_from_text(source)

    return make


@pytest.fixture(scope="module")
def stage_dividing_by():
    """`stage_dividing_by(denominator)`: the symbolic stage of one block,
    with the parameters r and s, whose line adds 1/(denominator) to its
    input; made once for each denominator."""

    @functools.cache
    def make(denominator):
        return stage_from_text(
            "@stage: parameters\nr : ℝ\ns : ℝ\n"
            "[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n"
            f" y = x + 1/({denominator}) :: [id=value]\n}}\n"
        )

    return make


@pytest.fixture(scope="module")
def stage_with_a_power_of_parameters():
    """The symbolic stage of `POWER_OF_PARAMETERS`."""
    return stage_from_text(POWER_OF_PARAMETERS)


def arithmetic_conditions(stage):
    """The conditions of arithmetic definedness that `stage` lists."""
    return [item for item in stage.obligations() if item.condition == "arithmetic-definedness"]


# --- the order in which a calibration judges its values ---


@pytest.mark.parametrize(
    "income, refusal",
    [
        (
            2.5,
            r"parameter 'ξ_u' .*the value 2\.5 does not satisfy the condition ξ_u < ξ_u_sup "
            r"of the declared set at ξ_u_sup = 2\.5",
        ),
        (
            3.0,
            r"parameter 'ξ_u' .*the value 3\.0 does not satisfy the condition ξ_u < ξ_u_sup "
            r"of the declared set at ξ_u_sup = 2\.5",
        ),
    ],
    ids=["at-the-bound", "above-the-bound"],
)
def test_an_income_outside_its_set_is_refused_at_its_own_parameter_and_not_at_a_definition(
    income, refusal
):
    """An income outside its declared set is refused at that parameter, and
    not at the logarithm that has no value there, while an income inside
    the set calibrates."""
    lines = (UNEMPLOYMENT_INCOME, INCOME_BOUND, SCALE, LOG_MEAN)
    with pytest.raises(ValueError, match=refusal) as refused:
        calibrated_buffer_stock(lines, ξ_u=income)
    # a refusal of a definition would be a ConstructionError under the rule
    # `derived-parameter` and would name the logarithm
    assert not isinstance(refused.value, ConstructionError)
    assert "log" not in str(refused.value)
    # at ξ_u = 1, ξ_scale = (1 - 0.4)/0.6 = 1, whose logarithm is 0
    assert calibrated_buffer_stock(lines, ξ_u=1.0).par["μ_emp"].value == pytest.approx(0.0)


def test_a_definition_with_no_value_at_values_inside_their_sets_is_refused_at_the_definition():
    """A derived parameter whose definition has no value at values that lie
    in their sets is refused at that definition, under the rule
    `derived-parameter`."""
    # at ξ_u = 2.5, ξ_scale = (1 - 0.4*2.5)/0.6 = 0, which has no logarithm
    with pytest.raises(ConstructionError, match="the derived parameter μ_emp") as undefined:
        calibrated_buffer_stock(("ξ_u : ℝ₊", SCALE, LOG_MEAN), ξ_u=2.5)
    assert undefined.value.rule == "derived-parameter"


@pytest.mark.parametrize(
    "first, second",
    [(ARTIFICIAL_LIMIT, UNEMPLOYMENT_INCOME), (UNEMPLOYMENT_INCOME, ARTIFICIAL_LIMIT)],
    ids=["limit-first", "income-first"],
)
def test_the_order_of_two_parameters_in_the_file_does_not_choose_the_one_refused(first, second):
    """Where an income outside its set puts the artificial limit outside its
    own set too, the income is refused, whichever of the two the file
    declares first."""
    # at ξ_u = 2.5 the lowest draw is 0, so a_Nat = 0 and a_Art = -0.1 < a_Nat
    with pytest.raises(ValueError, match=INCOME_REFUSED_AT_ITS_OWN_SET):
        calibrated_buffer_stock((first, second) + LIMIT_DEFINITIONS, ξ_u=2.5, **LIMIT_VALUES)


def test_a_limit_outside_its_set_at_an_income_inside_its_set_is_refused_at_the_limit():
    """An artificial limit below the natural borrowing limit is refused at
    the limit where the income lies inside its set."""
    with pytest.raises(ValueError, match="parameter 'a_Art' .*the condition a_Art > a_Nat"):
        calibrated_buffer_stock(
            (ARTIFICIAL_LIMIT, UNEMPLOYMENT_INCOME) + LIMIT_DEFINITIONS,
            ξ_u=1.0,
            **{**LIMIT_VALUES, "a_Art": -5.0},
        )


def test_a_derived_bound_of_a_declared_set_is_valued_before_a_value_is_judged_against_that_set():
    """The bound that the income's set reads is valued before the income is
    judged, although the file defines it after the two definitions that
    read the income."""
    lines = (UNEMPLOYMENT_INCOME, SCALE, LOG_MEAN, INCOME_BOUND)
    with pytest.raises(ValueError, match=INCOME_REFUSED_AT_ITS_OWN_SET):
        calibrated_buffer_stock(lines, ξ_u=2.5)
    assert calibrated_buffer_stock(lines, ξ_u=1.0).par["ξ_u_sup"].value == 2.5


def test_a_derived_value_outside_its_set_is_refused_before_a_definition_reads_it():
    """A derived value outside the set that its definition declares is
    refused at that derived parameter, before a definition that reads it is
    valued."""
    lines = ("ξ_u : ℝ₊", "q : (0, 1) := p_zero*ξ_u", "h := 1/(1 - q)")
    # at ξ_u = 2.5, q = 0.4*2.5 = 1, at which the definition of h divides by
    # zero
    with pytest.raises(
        ValueError, match=r"derived parameter 'q' .*lies outside the declared set \(0, 1\)"
    ) as refused:
        calibrated_buffer_stock(lines, ξ_u=2.5)
    assert "the value 1.0 of q" in str(refused.value) and not isinstance(
        refused.value, ConstructionError
    )
    # at ξ_u = 1, q = 0.4 and h = 1/0.6
    assert calibrated_buffer_stock(lines, ξ_u=1.0).par["h"].value == pytest.approx(1 / 0.6)


def test_a_parameter_bounded_by_a_definition_that_reads_it_is_judged_after_the_definition():
    """Where x is bounded below by y and y is defined from x, y is valued
    first and x is judged at its value."""
    each_other = ("x : ℝ @ (y, inf)", "y := 2*x")
    # at x = -1, y = -2 lies below x
    assert calibrated_buffer_stock(each_other, x=-1.0).par["y"].value == -2.0
    # at x = 1, y = 2 lies above x
    with pytest.raises(
        ValueError, match="parameter 'x' .*the condition x > y of the declared set at y = 2.0"
    ):
        calibrated_buffer_stock(each_other, x=1.0)


def test_a_calibration_gives_the_same_derived_values_in_every_order_of_the_lines():
    """A calibration of the same lines in three orders gives the same
    values of the five derived parameters."""
    lines = (ARTIFICIAL_LIMIT, UNEMPLOYMENT_INCOME) + LIMIT_DEFINITIONS + (SCALE, LOG_MEAN)
    values = {**LIMIT_VALUES, "ξ_u": 1.0}
    names = ("ξ_u_sup", "ξ_min", "a_Nat", "ξ_scale", "μ_emp")
    answers = [
        tuple(calibrated_buffer_stock(ordered, **values).par[name].value for name in names)
        for ordered in (lines, lines[::-1], lines[4:] + lines[:4])
    ]
    assert answers[0] == answers[1] == answers[2]
    # ξ_u_sup = 1/0.4 = 2.5 and ξ_scale = (1 - 0.4)/0.6 = 1
    assert answers[0][0] == 2.5 and answers[0][3] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "first, second",
    [
        (UNEMPLOYMENT_INCOME, BETWEEN_INCOME_AND_BOUND),
        (BETWEEN_INCOME_AND_BOUND, UNEMPLOYMENT_INCOME),
    ],
    ids=["income-first", "income-second"],
)
def test_a_value_is_refused_at_its_own_parameter_and_not_at_one_whose_set_reads_it(first, second):
    """An income above its bound is refused at the income, and not at ξ_mid,
    whose set (ξ_u, ξ_u_sup) reads the income, whichever of the two the
    file declares first."""
    # at an income of 3.0, above its bound 2.5, no ξ_mid lies in (3.0, 2.5)
    with pytest.raises(
        ValueError,
        match=r"parameter 'ξ_u' .*the value 3\.0 does not satisfy the condition ξ_u < ξ_u_sup",
    ):
        calibrated_buffer_stock(
            (first, second, INCOME_BOUND, DISTANCE_TO_THE_BOUND), ξ_u=3.0, ξ_mid=2.8
        )


def test_a_value_outside_a_set_that_reads_other_parameters_is_refused_at_its_own_parameter():
    """At an income inside its set, a value of ξ_mid outside (ξ_u, ξ_u_sup)
    is refused at ξ_mid, and a value inside it calibrates."""
    lines = (UNEMPLOYMENT_INCOME, BETWEEN_INCOME_AND_BOUND, INCOME_BOUND, DISTANCE_TO_THE_BOUND)
    with pytest.raises(
        ValueError,
        match=r"parameter 'ξ_mid' .*the value 0\.5 lies outside the declared set "
        r"\(ξ_u, ξ_u_sup\)",
    ):
        calibrated_buffer_stock(lines, ξ_u=1.0, ξ_mid=0.5)
    # ξ_gap = ξ_u_sup - ξ_mid = 2.5 - 2.0
    calibrated = calibrated_buffer_stock(lines, ξ_u=1.0, ξ_mid=2.0)
    assert calibrated.par["ξ_gap"].value == pytest.approx(0.5)


@pytest.mark.parametrize(
    "below",
    ["ξ_b : (0, ξ_cap)", "ξ_b : ℝ @ (0, ξ_cap)"],
    ids=["set-as-the-type", "set-after-the-type"],
)
def test_a_derived_value_is_refused_at_its_definition_and_not_at_a_set_that_reads_it(below):
    """A derived value ξ_cap outside its own set is refused at its
    definition, and not at ξ_b, whose set (0, ξ_cap) reads it."""
    # ξ_cap = 1/℘ = 2.5 lies outside its own set (0, 2), and ξ_b = 2.7 lies
    # outside (0, ξ_cap) at that value; the definition reads ξ_b alone
    at_the_cap = (
        r"derived parameter 'ξ_cap' .*the value 2\.5 of ξ_cap.* outside the declared set \(0, 2\)"
    )
    with pytest.raises(ValueError, match=at_the_cap):
        calibrated_buffer_stock((DERIVED_UPPER_BOUND, below, "ξ_twice := 2*ξ_b"), ξ_b=2.7)


def test_a_value_above_a_derived_bound_inside_its_own_set_is_refused_at_its_own_parameter():
    """Where ξ_cap lies in its set, at ℘ = 0.8, a value of ξ_b above it is
    refused at ξ_b, and a value below it calibrates."""
    # ξ_cap = 1/0.8 = 1.25
    lines = (DERIVED_UPPER_BOUND, "ξ_b : (0, ξ_cap)", "ξ_twice := 2*ξ_b")
    with pytest.raises(
        ValueError,
        match=r"parameter 'ξ_b' .*the value 2\.7 lies outside the declared set \(0, ξ_cap\)",
    ):
        calibrated_buffer_stock(lines, ξ_b=2.7, p_zero=0.8)
    assert calibrated_buffer_stock(lines, ξ_b=1.0, p_zero=0.8).par["ξ_twice"].value == 2.0


def test_a_set_written_by_name_is_judged_after_the_derived_parameter_that_it_reads():
    """A set written by name, whose definition reads a bound that the file
    defines last, is read through its definition: the bound is valued
    first, and an income outside the set is refused at the income."""
    lines = ("Xu := [0, ξ_u_sup)", "ξ_u : Xu", SCALE, LOG_MEAN, INCOME_BOUND)
    with pytest.raises(ValueError, match="parameter 'ξ_u' ") as refused:
        calibrated_buffer_stock(lines, ξ_u=3.0)
    assert not isinstance(refused.value, ConstructionError)
    assert "the value 3.0 lies outside the declared set [0, ξ_u_sup)" in str(refused.value)
    assert calibrated_buffer_stock(lines, ξ_u=1.0).par["μ_emp"].value == pytest.approx(0.0)


def test_a_value_is_refused_at_its_own_parameter_and_not_at_one_whose_named_set_reads_it():
    """An income above its bound is refused at the income, and not at ξ_mid,
    whose set written by name reads the income, while values inside their
    sets calibrate."""
    lines = (
        "Xmid := (ξ_u, ξ_u_sup]",
        "ξ_mid : Xmid",
        UNEMPLOYMENT_INCOME,
        DISTANCE_TO_THE_BOUND,
        INCOME_BOUND,
    )
    with pytest.raises(ValueError, match="parameter 'ξ_u' .*the condition ξ_u < ξ_u_sup"):
        calibrated_buffer_stock(lines, ξ_u=3.0, ξ_mid=2.8)
    # ξ_gap = ξ_u_sup - ξ_mid = 2.5 - 2.0
    calibrated = calibrated_buffer_stock(lines, ξ_u=1.0, ξ_mid=2.0)
    assert calibrated.par["ξ_gap"].value == pytest.approx(0.5)


@pytest.mark.parametrize(
    "ordered",
    [CHAIN, CHAIN[::-1], CHAIN[1:] + CHAIN[:1]],
    ids=["y-then-x-then-z", "z-then-x-then-y", "x-then-z-then-y"],
)
def test_a_derived_parameter_that_a_set_reads_is_valued_after_one_that_it_needs(ordered):
    """Where the set of x reads z, z is defined from y and y from x, y is
    valued without z and x is judged after the last definition, in each
    order of the lines."""
    # at x = 1, y = 2 and z = 4, so that x lies in (0, z)
    bound = calibrated_buffer_stock(ordered, x=1.0)
    assert (bound.par["y"].value, bound.par["z"].value) == (2.0, 4.0)
    with pytest.raises(ValueError, match=r"parameter 'x' .*the value -5\.0 lies outside"):
        calibrated_buffer_stock(ordered, x=-5.0)


def test_the_definitions_that_a_set_reads_through_two_further_definitions_are_valued_in_order():
    """Where the set of x reads w, defined from z, z from y and y from x,
    the calibration values y, z and w in the order in which each reads the
    one before it, and gives w its value."""
    longer_chain = ("y := x + 1", "x : (0, w)", "z := 2*y", "w := z + 1")
    # at x = 1, y = 2, z = 4 and w = 5
    assert calibrated_buffer_stock(longer_chain, x=1.0).par["w"].value == 5.0


def test_a_derived_parameter_of_the_chain_that_declares_a_set_is_refused_at_that_set():
    """Where y declares the set (0, 9), y is valued and judged before x,
    and a value of y outside its set is refused at y."""
    typed = ("y : (0, 9) := x + 1", "x : (0, z)", "z := 2*y")
    assert calibrated_buffer_stock(typed, x=1.0).par["z"].value == 4.0
    # at x = 20, y = 21
    with pytest.raises(
        ValueError,
        match=r"derived parameter 'y' .*the value 21\.0 of y.* outside the declared set",
    ):
        calibrated_buffer_stock(typed, x=20.0)


@pytest.mark.parametrize(
    "lines, values",
    [
        (("t_f := t_d + 1", "t_d : [0, 1) \\ [t_f, 2) := p_zero - 1"), {}),
        (("t_d : [0, 1) \\ [t_f, 2) := p_zero - 1", "t_f := t_d + 1"), {}),
        (("t_a := 2*t_d", "t_b := t_a + 1", "t_d : [0, 1) \\ [t_b, 2) := p_zero - 1"), {}),
        (
            ("t_f := t_y + 1", "t_y : ℝ @ (t_d, inf)", "t_d : [0, 1) \\ [t_f, 2) := p_zero - 1"),
            {"t_y": 5.0},
        ),
    ],
    ids=[
        "read-by-a-definition-before-it",
        "read-by-a-definition-after-it",
        "read-through-two-definitions",
        "read-through-a-parameter-whose-set-reads-it",
    ],
)
def test_a_derived_value_outside_the_left_side_of_its_set_is_refused_at_its_definition(
    lines, values
):
    """A derived value t_d outside [0, 1), which the left side of its set
    decides alone, is refused at its definition where the right side reads
    a derived parameter defined from t_d, while a value inside the set
    calibrates."""
    # t_d = ℘ - 1 = -0.6
    with pytest.raises(
        ValueError,
        match=r"derived parameter 't_d' .*the value -0\.6 of t_d.* outside the declared set",
    ):
        calibrated_buffer_stock(lines, **values)
    # t_d = ℘ = 0.4 and t_f = 1.4
    inside = ("t_f := t_d + 1", "t_d : [0, 1) \\ [t_f, 2) := p_zero")
    assert calibrated_buffer_stock(inside).par["t_f"].value == pytest.approx(1.4)


def test_of_values_faulty_only_through_each_other_the_first_of_the_file_is_named():
    """Where two values each lie outside their sets only at the value of the
    other, and no value is faulty by itself, the refusal names the first
    of them in the file."""
    with pytest.raises(ValueError, match=r"parameter 't_x' .*the condition t_x > t_y \+ t_k"):
        calibrated_buffer_stock(PAIR_BOUNDING_EACH_OTHER + READS_T_Y, t_x=1.0, t_y=1.0)


@pytest.mark.parametrize(
    "lines, values, refusal",
    [
        (
            PAIR_BOUNDING_EACH_OTHER + FAULTY_ALONE + READS_T_Y,
            {"t_x": 1.0, "t_y": 1.0, "t_w": 3.0},
            "parameter 't_w' .*the condition t_w < t_b",
        ),
        (
            FAULTY_ALONE + PAIR_BOUNDING_EACH_OTHER + READS_T_Y,
            {"t_x": 1.0, "t_y": 1.0, "t_w": 3.0},
            "parameter 't_w' .*the condition t_w < t_b",
        ),
        (
            ("t_c : (0, 2) := 1/p_zero",) + PAIR_BOUNDING_EACH_OTHER + READS_T_Y,
            {"t_x": 1.0, "t_y": 1.0},
            "derived parameter 't_c' .*the value 2.5 of t_c",
        ),
    ],
    ids=["declared-value-after-the-pair", "declared-value-before-the-pair", "derived-value"],
)
def test_a_value_faulty_by_itself_is_named_before_values_faulty_only_through_each_other(
    lines, values, refusal
):
    """A value outside its set by itself, declared or derived, is named in
    place of two values that lie outside their sets only through each
    other."""
    with pytest.raises(ValueError, match=refusal):
        calibrated_buffer_stock(lines, **values)


def test_of_two_values_faulty_by_themselves_the_first_of_the_file_is_named():
    """Of two values that each lie outside their sets by themselves, the
    refusal names the first in the file, although a definition reads the
    second first."""
    lines = ("t_b := 1/p_zero", "t_x : ℝ @ (0, t_b)", "t_y : ℝ @ (0, t_b)", "t_g := t_y + t_x")
    with pytest.raises(ValueError, match="parameter 't_x' .*the condition t_x < t_b"):
        calibrated_buffer_stock(lines, t_x=3.0, t_y=3.0)


@pytest.mark.parametrize(
    "lines, values, refusal",
    [
        (
            T_M_BOUNDED_BY_T_A,
            {"t_n": 1.0, "t_m": 5.0},
            "parameter 't_m' .*the condition t_m < t_a",
        ),
        (
            T_M_BOUNDED_BY_T_A[::-1],
            {"t_n": 1.0, "t_m": 5.0},
            "parameter 't_m' .*the condition t_m < t_a",
        ),
        (
            T_N_BOUNDED_BY_T_M + ("t_m : ℝ @ (0, t_d)", "t_d := t_a + 1", "t_a := 2*t_n"),
            {"t_n": 1.0, "t_m": 5.0},
            "parameter 't_m' .*the condition t_m < t_d",
        ),
        (
            T_N_BOUNDED_BY_T_M + ("t_m : ℝ @ (0, t_a) := 5*p_zero/0.4", "t_a := 2*t_n"),
            {"t_n": 1.0},
            "derived parameter 't_m' .*the value 5.0 of t_m",
        ),
    ],
    ids=["in-file-order", "in-reversed-order", "bound-through-a-definition", "derived-value"],
)
def test_a_value_is_not_refused_at_the_value_of_a_name_not_yet_judged(lines, values, refusal):
    """Where t_n = 1 lies outside its set only at t_m = 5, and t_m lies
    outside its own set, whose bound is defined from t_n, t_m is judged
    once its bound has a value and is refused, while values inside their
    sets calibrate."""
    with pytest.raises(ValueError, match=refusal):
        calibrated_buffer_stock(lines, **values)
    # at t_n = 6, t_a = 2*6 = 12
    calibrated = calibrated_buffer_stock(T_M_BOUNDED_BY_T_A, t_n=6.0, t_m=5.0)
    assert calibrated.par["t_a"].value == 12.0


# --- the conditions that a calibration decides ---


@pytest.mark.parametrize(
    "version, status, evidence",
    [("cons", "required", ()), ("cons_calibrated", "established", ("calibration ρ = 6.0",))],
    ids=["symbolic", "calibrated"],
)
def test_calibration_establishes_the_condition_of_the_utility_with_the_value_as_evidence(
    request, version, status, evidence
):
    """The condition that the denominator 1 − ρ of the utility is not zero
    is required before calibration, and established after it with the
    value of ρ as its evidence."""
    (item,) = [
        condition
        for condition in arithmetic_conditions(request.getfixturevalue(version))
        if str(condition.entries[0]) == "cons:function:𝑢"
    ]
    assert item.status == status
    assert item.evidence == evidence
    assert isinstance(item.entries[1], predicates.Not)
    assert typed_expressions.format_expression(item.entries[1], width=None) == "¬(1 − ρ = 0)"


def test_calibration_refuses_a_value_at_which_the_utility_divides_by_zero(cons):
    """At ρ = 1 the utility c^(1-ρ)/(1-ρ) divides by zero, and the
    calibration is refused with the value and the condition that fails."""
    with pytest.raises(ValueError) as refused:
        copy_native(cons).calibrate({"ρ": 1.0})
    assert [word for word in ("ρ", "1.0", "1 - ρ = 0") if word not in str(refused.value)] == []


@pytest.mark.parametrize("version", CONDITION_STAGES)
def test_the_listing_of_the_conditions_names_each_condition_by_its_formula_or_its_sentence(
    request, version
):
    """The printed listing of the conditions of a stage names each
    condition with its formula or, where it has none, its sentence."""
    stage = request.getfixturevalue(version)
    listing = " ".join(str(stage.obligations()).split())
    for item in stage.obligations():
        text = (
            typed_expressions.format_expression(item.predicate, width=None)
            if item.predicate is not None
            else item.explanation
        )
        assert text
        assert item.condition in listing and " ".join(text.split()) in listing


@pytest.mark.parametrize("version", CONDITION_STAGES)
def test_each_stage_lists_its_conditions_of_integrability_admissibility_and_optimality_required(
    request, version
):
    """Each stage, calibrated or not, lists as required each of its
    conditions of integrability of an expectation, admissibility of an
    aggregation and optimality."""
    pending = {"expectation-integrability", "aggregation-admissibility", "optimality"}
    obligations = request.getfixturevalue(version).obligations()
    statuses = {item.status for item in obligations if item.condition in pending}
    assert statuses == {"required"}


@pytest.mark.parametrize("version", CONDITION_STAGES)
def test_no_stage_lists_a_condition_that_the_package_does_not_state(request, version):
    """No stage lists a condition under a name that the package does not
    give to a condition of a stage."""
    # names of analytic conditions that the package does not state as
    # conditions of a stage
    unstated = {
        "single-valuedness",
        "measurable-selection",
        "reverse-solution-coverage",
        "measurable-law-of-motion",
        "measurable-policy",
        "input-derivative-compatibility",
        "total-mass-preservation",
    }
    conditions = {item.condition for item in request.getfixturevalue(version).obligations()}
    assert not conditions & unstated


@pytest.mark.parametrize(
    "binder", ["cp", "ρ"], ids=["argmax-over-cp", "argmax-over-a-variable-named-rho"]
)
def test_calibration_decides_a_condition_on_a_free_parameter_whatever_the_argmax_binds(
    cons_dividing_by_rho_minus_6, binder
):
    """Calibration refuses ρ = 6, at which the inverse Euler line divides by
    zero, and establishes the condition at ρ = 7, whether the argmax binds
    `cp` or a variable of its own named `ρ`."""
    stage = cons_dividing_by_rho_minus_6(binder)
    with pytest.raises(ValueError, match="ρ [-−] 6"):
        copy_native(stage).calibrate({"ρ": 6.0})
    (condition,) = [
        item
        for item in arithmetic_conditions(copy_native(stage).calibrate({"ρ": 7.0}))
        if item.entries[0].block == "policy"
    ]
    assert condition.status == "established" and condition.evidence == ("calibration ρ = 7.0",)


@pytest.mark.parametrize(
    "binder", ["cp", "ρ"], ids=["argmax-over-cp", "argmax-over-a-variable-named-rho"]
)
def test_the_symbolic_stage_holds_two_conditions_of_arithmetic_both_required(
    cons_dividing_by_rho_minus_6, binder
):
    """Before calibration the stage holds two conditions of arithmetic
    definedness, both required."""
    arithmetic = arithmetic_conditions(cons_dividing_by_rho_minus_6(binder))
    assert len(arithmetic) == 2 and all(item.status == "required" for item in arithmetic)


def test_the_declarations_establish_the_range_condition_of_the_saving_before_calibration(
    cons_dividing_by_rho_minus_6,
):
    """Before calibration the declarations establish the range condition of
    the first line of the builder from the decision perch to the
    continuation perch."""
    # the argmax binds `cp`, as the stage file writes it
    assert any(
        item.condition == "range-compatibility"
        and item.status == "established"
        and str(item.entries[0]) == "dcsn_to_cntn.1"
        for item in cons_dividing_by_rho_minus_6("cp").obligations()
    )


def test_calibration_decides_a_free_occurrence_of_a_parameter_and_leaves_a_bound_one_required(
    cons_with_egm_lines_text,
):
    """An occurrence of 1/(ρ − 6) inside an argmax that binds a variable `ρ`
    is not decided by the calibration ρ = 6, and a second occurrence on the
    inverse Euler line, where ρ is the parameter, is refused at ρ = 6 and
    established at ρ = 7."""
    source = changed(
        cons_with_egm_lines_text,
        ("argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])", "argmax_{ρ : Γ(m_d)}(𝑢(ρ) + V[>] + 1/(ρ-6))"),
    )
    bound_only = stage_from_text(source).calibrate({"ρ": 6.0})
    assert {
        str(item.entries[0]): item.status
        for item in arithmetic_conditions(bound_only)
        if item.entries[0].block == "policy"
    } == {"policy.optimality": "required"}
    with_free = changed(source, ("𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])", "𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) + 1/(ρ-6)"))
    mixed = stage_from_text(with_free)
    with pytest.raises(ValueError, match="ρ [-−] 6"):
        mixed.calibrate({"ρ": 6.0})
    # the two occurrences stand on two lines and are two conditions: the one
    # of the piece that realises the inverse Euler line is decided, the one
    # of the line of optimality, marked `!doc`, is not
    conditions = {
        str(item.entries[0]): item.status
        for item in arithmetic_conditions(mixed.calibrate({"ρ": 7.0}))
        if item.entries[0].block == "policy"
    }
    assert conditions == {
        "policy.InvEuler:Aggregation": "established",
        "policy.optimality": "required",
    }


@pytest.mark.parametrize("denominator, r, s", EXACT_DENOMINATORS)
def test_calibration_decides_a_denominator_exactly_at_large_integers(
    stage_dividing_by, denominator, r, s
):
    """Calibration refuses r = s, at which the denominator is zero, and
    establishes the condition at r = s + 1, with the values as evidence."""
    stage = stage_dividing_by(denominator)
    with pytest.raises(ValueError, match="calibration"):
        copy_native(stage).calibrate({"r": s, "s": s})
    conditions = arithmetic_conditions(copy_native(stage).calibrate({"r": r, "s": s}))
    assert conditions and all(item.status == "established" for item in conditions)
    assert any(item.evidence == (f"calibration r = {r!r}, s = {s!r}",) for item in conditions)


@pytest.mark.parametrize(
    "r, s",
    [(2**53 + 1, 2**53), (10**400 + 1, 10**400)],
    ids=["beyond-the-precision-of-a-float", "beyond-the-range-of-a-float"],
)
def test_calibration_binds_integer_values_as_integers(stage_dividing_by, r, s):
    """A calibration binds integer values as Python integers."""
    version = copy_native(stage_dividing_by("r-s")).calibrate({"r": r, "s": s})
    assert dict(version.bindings.calibration) == {"r": r, "s": s}
    assert all(type(value) is int for value in version.bindings.calibration.values())


@pytest.mark.parametrize("denominator, r, s", EXACT_DENOMINATORS)
def test_a_refused_calibration_leaves_every_condition_of_the_stage_required(
    stage_dividing_by, denominator, r, s
):
    """After a calibration refused at r = s, every condition of the stage is
    still required."""
    stage = copy_native(stage_dividing_by(denominator))
    with pytest.raises(ValueError, match="calibration"):
        stage.calibrate({"r": s, "s": s})
    assert all(item.status == "required" for item in stage.obligations())


def test_calibration_establishes_a_parameter_condition_and_leaves_a_state_one_required():
    """Calibration establishes the condition that ρ − η is not zero, with
    the values as its evidence, and leaves required the condition that the
    arrival state x is not zero."""
    # the value of x, which is no parameter, is not bound
    arithmetic = arithmetic_conditions(
        stage_from_text(TWO_DIVISORS).calibrate({"ρ": 3.0, "η": 2.0, "x": 4.0})
    )
    assert {item.status for item in arithmetic} == {"required", "established"}
    (proved,) = [item for item in arithmetic if item.status == "established"]
    assert proved.evidence == ("calibration ρ = 3.0, η = 2.0",)
    assert isinstance(proved.entries[1], predicates.Not)
    assert typed_expressions.format_expression(proved.entries[1], width=None) == "¬(ρ − η = 0)"
    (pending,) = [item for item in arithmetic if item.status == "required"]
    assert pending.evidence == ()
    assert isinstance(pending.entries[1], predicates.Not)
    # the condition belongs to the push-forward from arrival, and writes the
    # arrival state as the card of that push-forward writes it
    assert typed_expressions.format_expression(pending.entries[1], width=None) == "¬(x≺ = 0)"


def test_a_refused_calibration_leaves_the_conditions_and_their_evidence_as_they_were():
    """A second calibration, refused at ρ = η, leaves the conditions of the
    calibrated stage and the evidence of the established one as they
    were."""
    bound = stage_from_text(TWO_DIVISORS).calibrate({"ρ": 3.0, "η": 2.0, "x": 4.0})
    arithmetic = arithmetic_conditions(bound)
    with pytest.raises(ValueError, match="ρ.*η"):
        bound.calibrate({"ρ": 2.0, "η": 2.0})
    (proved,) = [item for item in arithmetic_conditions(bound) if item.status == "established"]
    assert proved.evidence == ("calibration ρ = 3.0, η = 2.0",)
    assert arithmetic_conditions(bound) == arithmetic


@pytest.mark.parametrize(
    "base, exponent",
    [(0.0, 0.0), (0.0, -1.0), (-2.0, 0.5), (0.0, 2.0), (-2.0, 2.0)],
    ids=[
        "zero-to-the-power-zero",
        "zero-to-a-negative-power",
        "negative-to-the-power-one-half",
        "zero-squared",
        "negative-squared",
    ],
)
def test_calibration_establishes_a_power_at_a_positive_base_and_refuses_any_other_base(
    stage_with_a_power_of_parameters, base, exponent
):
    """Since the set ℝ of the exponent admits a non-integer exponent, the
    condition on ρ^η is that the base is positive: calibration establishes
    it at ρ = 2 and refuses a zero or negative base, whatever the value of
    η."""
    calibrated = copy_native(stage_with_a_power_of_parameters).calibrate({"ρ": 2.0, "η": exponent})
    arithmetic = arithmetic_conditions(calibrated)
    assert arithmetic and all(item.status == "established" for item in arithmetic)
    with pytest.raises(ValueError, match="makes ρ > 0 false"):
        copy_native(stage_with_a_power_of_parameters).calibrate({"ρ": base, "η": exponent})


def test_on_the_extended_reals_calibration_establishes_a_power_at_a_positive_base():
    """Where the base is declared on the extended reals, calibration at
    ρ = 2 and η = 0.5 establishes the condition on ρ^η."""
    extended = stage_from_text(changed(POWER_OF_PARAMETERS, ("ρ : ℝ\n", "ρ : ℝ̄\n")))
    decided = arithmetic_conditions(extended.calibrate({"ρ": 2.0, "η": 0.5}))
    assert decided and all(item.status == "established" for item in decided)


@pytest.mark.parametrize(
    "text",
    [
        POWER_OF_PARAMETERS.replace("ρ^η + x", "x^ρ"),
        POWER_OF_PARAMETERS.replace("[id=b", "f(ρ : ℝ) := 1/ρ\n[id=b").replace("ρ^η + x", "f(x)"),
    ],
    ids=["power-of-the-input", "function-of-the-input"],
)
def test_calibration_leaves_a_condition_on_the_input_of_a_line_required(text):
    """A condition of arithmetic that involves the input of the line stays
    required after calibration."""
    arithmetic = arithmetic_conditions(stage_from_text(text).calibrate({"ρ": 2.0, "η": 1.0}))
    assert arithmetic and all(item.status == "required" for item in arithmetic)


def test_calibration_decides_a_line_condition_at_the_value_of_a_derived_parameter(
    derived_parameter_stages,
):
    """A condition of a line that reads a derived parameter is decided at
    the value of its definition: with z := R − 1.04, the divisor of
    m = k/z + 1 is refused at R = 1.04 and established at R = 1.05."""
    changes = (("R_n := R/Γ", "R_n := R/Γ\nz := R - 1.04"), ("m = R_n*k + 1", "m = k/z + 1"))
    with pytest.raises(ValueError) as refused:
        derived_parameter_stages.stage(*changes).calibrate(
            {"calibration": {**derived_parameter_stages.calibration, "R": 1.04}}
        )
    message = str(refused.value)
    assert [word for word in ("z = 0.0", "¬(z = 0)", "false") if word not in message] == []
    stage = derived_parameter_stages.stage(*changes)
    stage.calibrate({"calibration": {**derived_parameter_stages.calibration, "R": 1.05}})
    (condition,) = [
        item for item in arithmetic_conditions(stage) if item.entries[0].block == "arvl_to_dcsn"
    ]
    assert condition.status == "established"
    assert condition.evidence[0].startswith("calibration z = 0.01")
