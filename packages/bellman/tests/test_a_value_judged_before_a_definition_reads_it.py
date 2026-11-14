"""The acceptance file of the change "A value is judged against its own
declared set before a definition that reads it is evaluated" (CDC, 12
November 2026): one test for each item, named `test_item_<n>_<claim>`, each
reading `calibrate` on the buffer-stock stage with lines added.

Calibration checks that each value lies in its declared set and that each
derived parameter's definition has a value. One faulty value can fail
several of these checks, and the first to fail is the one the refusal
names. The items say which that is; no item changes what calibrates.

1. A value outside its set is refused at its own parameter where a derived
   parameter computes with it: an unemployment income at or above 1/℘ is
   refused at `ξ_u`, by the condition of its set, and not at the definition
   whose `log` has no value there.
2. The same value is refused at its own parameter where another parameter's
   set reads a derived parameter computed from it, in whatever order the
   file declares the two.
3. The derived parameter that the set reads is valued first, wherever the
   file defines it.
4. A derived value outside the set its definition declares is refused at
   that definition, before a definition that reads it is evaluated.
5. A parameter and a derived parameter that read each other are judged as
   before, after the definition has its value; and a calibration that was
   bound is bound, with the same values, in every order of the lines.

Seven items were added at AAS's review of 13 November 2026. Before a
definition is evaluated, the values that the set of a value it reads reads
are judged with that value, so that the rule of AMD-GRAM-004 §4 holds among
them: a faulty value is refused at its own name, and not at a name whose
set reads it (items 6 to 8). Items 9 to 12 hold what the judgment that
follows the last definition answers, which the judgment before a
definition does not change: a calibration that binds, a refusal where a
derived parameter of the set has no value yet, and which of several faulty
values is named.

6. A value outside its set is refused at its own parameter where a
   definition reads a second parameter whose set reads the first, in
   whatever order the file declares the two.
7. A derived value outside the set its definition declares is refused at
   that definition where a definition reads a parameter whose set reads
   the derived parameter.
8. A set written by name is read through its definition, in items 3 and 6
   as a set written in place is.
9. A derived parameter that a set reads is valued first only where its
   value needs no derived parameter that is being valued: a calibration
   binds, with the same values, where the set of a parameter reads a
   derived parameter whose definition reads, through another definition,
   that parameter.
10. A value that the judgment before a definition refuses is refused in a
    sentence of the usual form where a derived parameter that its set reads
    has no value yet.
11. Before a definition is evaluated, a value is refused only where it lies
    outside its set by itself. Values that lie outside their sets only at
    the value of each other wait for the judgment that follows the last
    definition, which names a value faulty by itself where there is one and
    the first of the file otherwise.
12. Of two values that lie outside their sets by themselves and are judged
    together, the first of the file is named.
13. Before a definition is evaluated, a value is not refused at the value
    of a name that is not yet judged, which may prove to be the faulty
    one.
"""

import pytest
from conftest import DERIVED_BUFFER_STOCK_CALIBRATION, derived_buffer_stock_text, stage_from_text

from bellman.refusals import ConstructionError

PROBABILITY = 'p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]\n'
VALUES = {**DERIVED_BUFFER_STOCK_CALIBRATION, "p_zero": 0.4}

INCOME = "ξ_u : ℝ₊ @ [0, ξ_u_sup)"
BOUND = "ξ_u_sup : ℝ_{+∞} := if p_zero = 0 then inf else 1/p_zero"
SCALE = "ξ_scale := (1 - p_zero*ξ_u)/(1 - p_zero)"
LOG = "μ_emp := log(ξ_scale)"
LIMIT = "a_Art : (-inf, 0] @ (a_Nat, inf)"
LOWEST = "ξ_min := min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))"
NATURAL = "a_Nat : ℝ_{-∞} := if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf"
BETWEEN = "ξ_mid : (ξ_u, ξ_u_sup)"
GAP = "ξ_gap := ξ_u_sup - ξ_mid"
CAP = "ξ_cap : (0, 2) := 1/p_zero"

# the refusal of an unemployment income at 1/℘ = 2.5, by its own set
AT_ITS_OWN_SET = (
    r"parameter 'ξ_u' .*the value 2\.5 does not satisfy the condition ξ_u < ξ_u_sup of the "
    r"declared set at ξ_u_sup = 2\.5"
)


def _calibrated(lines, **values):
    """The buffer-stock stage with `lines` declared after its probability of
    a zero draw, calibrated at `VALUES` and `values`."""
    text = derived_buffer_stock_text()
    assert text.count(PROBABILITY) == 1
    declared = "".join(line + "\n" for line in lines)
    stage = stage_from_text(text.replace(PROBABILITY, PROBABILITY + declared), "buffer_stock.bl")
    return stage.calibrate({**VALUES, **values})


def test_item_1_a_value_outside_its_set_is_refused_at_its_own_parameter_and_not_at_a_definition():
    lines = (INCOME, BOUND, SCALE, LOG)
    for income in (2.5, 3.0):
        with pytest.raises(ValueError, match="parameter 'ξ_u' ") as refused:
            _calibrated(lines, ξ_u=income)
        # no refusal of a definition: the rule `derived-parameter` is not the one given
        assert not isinstance(refused.value, ConstructionError)
        assert "ξ_u < ξ_u_sup" in str(refused.value) and "log" not in str(refused.value)
    with pytest.raises(ValueError, match=AT_ITS_OWN_SET):
        _calibrated(lines, ξ_u=2.5)
    # inside its set the income calibrates, and the logarithm has its value
    assert _calibrated(lines, ξ_u=1.0).par["μ_emp"].value == pytest.approx(0.0)
    # a definition with no value at values that lie in their sets is refused as before
    with pytest.raises(ConstructionError, match="the derived parameter μ_emp") as undefined:
        _calibrated(("ξ_u : ℝ₊", SCALE, LOG), ξ_u=2.5)
    assert undefined.value.rule == "derived-parameter"


def test_item_2_the_file_s_order_of_two_parameters_does_not_choose_the_one_refused():
    rest = ("θ_min : (0, 1]", "ψ_min : (0, 1]", BOUND, LOWEST, NATURAL)
    values = {"θ_min": 0.3, "ψ_min": 0.8, "a_Art": -0.1}
    for first, second in ((LIMIT, INCOME), (INCOME, LIMIT)):
        with pytest.raises(ValueError, match=AT_ITS_OWN_SET):
            _calibrated((first, second) + rest, ξ_u=2.5, **values)
    # a limit outside its own set, at an income inside its set, is refused at the limit
    with pytest.raises(ValueError, match="parameter 'a_Art' .*the condition a_Art > a_Nat"):
        _calibrated((LIMIT, INCOME) + rest, ξ_u=1.0, **{**values, "a_Art": -5.0})


def test_item_3_the_derived_parameter_a_set_reads_is_valued_first_wherever_the_file_defines_it():
    # the bound of the income is defined after the two definitions that read the income
    with pytest.raises(ValueError, match=AT_ITS_OWN_SET):
        _calibrated((INCOME, SCALE, LOG, BOUND), ξ_u=2.5)
    assert _calibrated((INCOME, SCALE, LOG, BOUND), ξ_u=1.0).par["ξ_u_sup"].value == 2.5


def test_item_4_a_derived_value_outside_its_set_is_refused_before_a_definition_reads_it():
    lines = ("ξ_u : ℝ₊", "q : (0, 1) := p_zero*ξ_u", "h := 1/(1 - q)")
    # at q = 1 the definition of h divides by zero; q is refused, by its own set
    with pytest.raises(ValueError, match=r"derived parameter 'q' .*lies outside the declared set \(0, 1\)") as refused:
        _calibrated(lines, ξ_u=2.5)
    assert "the value 1.0 of q" in str(refused.value) and not isinstance(refused.value, ConstructionError)
    assert _calibrated(lines, ξ_u=1.0).par["h"].value == pytest.approx(1 / 0.6)


def test_item_5_names_that_read_each_other_and_a_calibration_that_binds_are_as_before():
    # x is bounded by y, and y is defined from x: y is valued, and x is judged after it
    each_other = ("x : ℝ @ (y, inf)", "y := 2*x")
    assert _calibrated(each_other, x=-1.0).par["y"].value == -2.0
    with pytest.raises(ValueError, match="parameter 'x' .*the condition x > y of the declared set at y = 2.0"):
        _calibrated(each_other, x=1.0)
    # one calibration, every order of the lines: bound, with the same values
    lines = (LIMIT, INCOME, "θ_min : (0, 1]", "ψ_min : (0, 1]", BOUND, LOWEST, NATURAL, SCALE, LOG)
    values = {"θ_min": 0.3, "ψ_min": 0.8, "a_Art": -0.1, "ξ_u": 1.0}
    names = ("ξ_u_sup", "ξ_min", "a_Nat", "ξ_scale", "μ_emp")
    answers = [
        tuple(_calibrated(ordered, **values).par[name].value for name in names)
        for ordered in (lines, lines[::-1], lines[4:] + lines[:4])
    ]
    assert answers[0] == answers[1] == answers[2]
    assert answers[0][0] == 2.5 and answers[0][3] == pytest.approx(1.0)


def test_item_6_a_value_is_refused_at_its_own_parameter_and_not_at_one_whose_set_reads_it():
    # the definition reads ξ_mid alone, and the set of ξ_mid reads the income:
    # at an income of 3.0, above its bound 2.5, no ξ_mid lies in (3.0, 2.5)
    at_the_income = (
        r"parameter 'ξ_u' .*the value 3\.0 does not satisfy the condition ξ_u < ξ_u_sup"
    )
    for first, second in ((INCOME, BETWEEN), (BETWEEN, INCOME)):
        with pytest.raises(ValueError, match=at_the_income):
            _calibrated((first, second, BOUND, GAP), ξ_u=3.0, ξ_mid=2.8)
    # at an income inside its set, a value outside (ξ_u, ξ_u_sup) is refused
    # at its own parameter, and a value inside it calibrates
    lines = (INCOME, BETWEEN, BOUND, GAP)
    outside = r"parameter 'ξ_mid' .*the value 0\.5 lies outside the declared set \(ξ_u, ξ_u_sup\)"
    with pytest.raises(ValueError, match=outside):
        _calibrated(lines, ξ_u=1.0, ξ_mid=0.5)
    assert _calibrated(lines, ξ_u=1.0, ξ_mid=2.0).par["ξ_gap"].value == pytest.approx(0.5)


def test_item_7_a_derived_value_is_refused_at_its_definition_and_not_at_a_set_that_reads_it():
    # ξ_cap = 1/℘ = 2.5 lies outside its own set (0, 2), and ξ_b = 2.7 lies
    # outside (0, ξ_cap) at that value; the definition reads ξ_b alone
    at_the_cap = (
        r"derived parameter 'ξ_cap' .*the value 2\.5 of ξ_cap.* outside the declared set \(0, 2\)"
    )
    for below in ("ξ_b : (0, ξ_cap)", "ξ_b : ℝ @ (0, ξ_cap)"):
        with pytest.raises(ValueError, match=at_the_cap):
            _calibrated((CAP, below, "ξ_twice := 2*ξ_b"), ξ_b=2.7)
    # where ξ_cap lies in its set, at ℘ = 0.8, a value of ξ_b above it is
    # refused at ξ_b, and a value below it calibrates
    lines = (CAP, "ξ_b : (0, ξ_cap)", "ξ_twice := 2*ξ_b")
    at_its_own_set = r"parameter 'ξ_b' .*the value 2\.7 lies outside the declared set \(0, ξ_cap\)"
    with pytest.raises(ValueError, match=at_its_own_set):
        _calibrated(lines, ξ_b=2.7, p_zero=0.8)
    assert _calibrated(lines, ξ_b=1.0, p_zero=0.8).par["ξ_twice"].value == 2.0


def test_item_8_a_set_written_by_name_is_read_through_its_definition():
    # item 3: the bound that the named set reads is defined after the two
    # definitions that read the income, and is valued first
    lines = ("Xu := [0, ξ_u_sup)", "ξ_u : Xu", SCALE, LOG, BOUND)
    with pytest.raises(ValueError, match="parameter 'ξ_u' ") as refused:
        _calibrated(lines, ξ_u=3.0)
    assert not isinstance(refused.value, ConstructionError)
    assert "the value 3.0 lies outside the declared set [0, ξ_u_sup)" in str(refused.value)
    assert _calibrated(lines, ξ_u=1.0).par["μ_emp"].value == pytest.approx(0.0)
    # item 6: the income that the named set reads is judged with ξ_mid
    lines = ("Xmid := (ξ_u, ξ_u_sup]", "ξ_mid : Xmid", INCOME, GAP, BOUND)
    with pytest.raises(ValueError, match="parameter 'ξ_u' .*the condition ξ_u < ξ_u_sup"):
        _calibrated(lines, ξ_u=3.0, ξ_mid=2.8)
    assert _calibrated(lines, ξ_u=1.0, ξ_mid=2.0).par["ξ_gap"].value == pytest.approx(0.5)


def test_item_9_a_derived_parameter_that_a_set_reads_is_not_valued_before_one_it_needs():
    # the set of x reads z, z is defined from y, and y is defined from x:
    # y is valued without z, and x is judged after the last definition
    lines = ("y := x + 1", "x : (0, z)", "z := 2*y")
    for ordered in (lines, lines[::-1], lines[1:] + lines[:1]):
        bound = _calibrated(ordered, x=1.0)
        assert (bound.par["y"].value, bound.par["z"].value) == (2.0, 4.0)
    with pytest.raises(ValueError, match=r"parameter 'x' .*the value -5\.0 lies outside"):
        _calibrated(lines, x=-5.0)
    # the same through two further definitions, and where y declares a set
    chain = ("y := x + 1", "x : (0, w)", "z := 2*y", "w := z + 1")
    assert _calibrated(chain, x=1.0).par["w"].value == 5.0
    typed = ("y : (0, 9) := x + 1", "x : (0, z)", "z := 2*y")
    assert _calibrated(typed, x=1.0).par["z"].value == 4.0
    at_its_own_set = r"derived parameter 'y' .*the value 21\.0 of y.* outside the declared set"
    with pytest.raises(ValueError, match=at_its_own_set):
        _calibrated(typed, x=20.0)


def test_item_10_a_value_is_refused_before_a_derived_parameter_its_set_reads_has_a_value():
    # t_d = ℘ - 1 = -0.6 lies outside [0, 1), which the left side of the
    # difference decides alone; the right side reads a derived parameter
    # that is defined from t_d and has no value when t_d is refused
    at_its_definition = (
        r"derived parameter 't_d' .*the value -0\.6 of t_d.* outside the declared set"
    )
    for lines in (
        ("t_f := t_d + 1", "t_d : [0, 1) \\ [t_f, 2) := p_zero - 1"),
        ("t_d : [0, 1) \\ [t_f, 2) := p_zero - 1", "t_f := t_d + 1"),
        ("t_a := 2*t_d", "t_b := t_a + 1", "t_d : [0, 1) \\ [t_b, 2) := p_zero - 1"),
    ):
        with pytest.raises(ValueError, match=at_its_definition):
            _calibrated(lines)
    # the same through a parameter whose set reads t_d
    lines = ("t_f := t_y + 1", "t_y : ℝ @ (t_d, inf)", "t_d : [0, 1) \\ [t_f, 2) := p_zero - 1")
    with pytest.raises(ValueError, match=at_its_definition):
        _calibrated(lines, t_y=5.0)
    # inside its set the derived value calibrates
    inside = ("t_f := t_d + 1", "t_d : [0, 1) \\ [t_f, 2) := p_zero")
    assert _calibrated(inside).par["t_f"].value == pytest.approx(1.4)


def test_item_11_values_faulty_only_through_each_other_wait_for_the_last_judgment():
    # t_x and t_y bound each other through a derived parameter, so each lies
    # outside its set only at the value of the other, and a definition
    # reads t_y
    pair = ("t_k := 0*p_zero", "t_x : ℝ @ (t_y + t_k, 10)", "t_y : ℝ @ (t_x + t_k, 10)")
    reads = ("t_g := 2*t_y",)
    # no value is faulty by itself: the first of the file is named
    with pytest.raises(ValueError, match=r"parameter 't_x' .*the condition t_x > t_y \+ t_k"):
        _calibrated(pair + reads, t_x=1.0, t_y=1.0)
    # a value faulty by itself, which no definition reads, is named
    alone = ("t_b := 1/p_zero", "t_w : ℝ @ (0, t_b)")
    for lines in (pair + alone + reads, alone + pair + reads):
        with pytest.raises(ValueError, match="parameter 't_w' .*the condition t_w < t_b"):
            _calibrated(lines, t_x=1.0, t_y=1.0, t_w=3.0)
    # and so is a derived value outside the set its definition declares
    lines = ("t_c : (0, 2) := 1/p_zero",) + pair + reads
    with pytest.raises(ValueError, match="derived parameter 't_c' .*the value 2.5 of t_c"):
        _calibrated(lines, t_x=1.0, t_y=1.0)


def test_item_12_of_two_values_faulty_by_themselves_the_first_of_the_file_is_named():
    # one definition reads both, the second of the file first
    lines = ("t_b := 1/p_zero", "t_x : ℝ @ (0, t_b)", "t_y : ℝ @ (0, t_b)", "t_g := t_y + t_x")
    with pytest.raises(ValueError, match="parameter 't_x' .*the condition t_x < t_b"):
        _calibrated(lines, t_x=3.0, t_y=3.0)


def test_item_13_a_value_is_not_refused_at_the_value_of_a_name_not_yet_judged():
    # t_n = 1 lies outside its set only at t_m = 5, and t_m lies outside its
    # own set, whose bound t_a = 2 is defined from t_n: t_m cannot be judged
    # before t_a has its value, and it is the faulty one
    start = ("t_k := 0*p_zero", "t_n : ℝ @ (t_m + t_k, 10)")
    lines = start + ("t_m : ℝ @ (0, t_a)", "t_a := 2*t_n")
    for ordered in (lines, lines[::-1]):
        with pytest.raises(ValueError, match="parameter 't_m' .*the condition t_m < t_a"):
            _calibrated(ordered, t_n=1.0, t_m=5.0)
    # the same where the bound reaches t_a through a further definition
    lines = start + ("t_m : ℝ @ (0, t_d)", "t_d := t_a + 1", "t_a := 2*t_n")
    with pytest.raises(ValueError, match="parameter 't_m' .*the condition t_m < t_d"):
        _calibrated(lines, t_n=1.0, t_m=5.0)
    # and where the faulty value is a derived parameter's
    lines = start + ("t_m : ℝ @ (0, t_a) := 5*p_zero/0.4", "t_a := 2*t_n")
    with pytest.raises(ValueError, match="derived parameter 't_m' .*the value 5.0 of t_m"):
        _calibrated(lines, t_n=1.0)
    # with every value inside its set the calibration binds
    lines = start + ("t_m : ℝ @ (0, t_a)", "t_a := 2*t_n")
    assert _calibrated(lines, t_n=6.0, t_m=5.0).par["t_a"].value == 12.0
