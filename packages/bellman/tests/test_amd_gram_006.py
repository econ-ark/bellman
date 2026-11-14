"""The acceptance file of AMD-GRAM-006, `min`, `max` and a definition by cases
in a derived parameter, consistent with the internal developer release 0.04:
one test for each acceptance item that this file carries, named
`test_item_<n>_<claim>`.

1. A derived parameter's definition calls `min` and `max`, each of one
   argument or more, and may be written by cases, `if test then a else b`,
   with or without a declared set; a bound of a declared set reads the same
   calls; the printed form is read back as the same term; and `if`, `then`
   and `else` are words of the language and no names.
2. The value at a calibration is the branch the test chooses, and the other
   branch is not evaluated; `min` and `max` evaluate every argument; a
   definition that computes with a name valued at an infinity has no value.
3. A branch written `inf` or `-inf` needs a declared set that holds that
   infinity: a definition whose set cannot hold it is refused when the file
   is read, calibration holds the value, finite or infinite, to the set, and
   the records print the infinity.
4. An endpoint or a side of a bound that is the bare name of a parameter or
   of a derived parameter valued at an infinity is read as that infinity; a
   bound that computes with such a name, or with the written `inf`, has no
   value; the two procedures that judge a membership give one answer for an
   infinite value; and a line of a block that computes with a derived
   parameter whose declared set may hold an infinity owns the conditions
   that a parameter declared on that set gives it.
5. A compiled kernel writes a definition by cases through `by_cases` and
   `min` and `max` through `np.minimum` and `np.maximum`, and its parameters
   are the declared ones. Where the test is one truth value, it evaluates the
   chosen branch alone; where the test is an array, it takes at each entry
   the value of the branch the test chooses there, and a branch neither
   raises nor warns at the entries the test does not choose; `min` and `max`
   of integers, written as numbers or held by parameters, and a definition
   by cases whose branches are integers give what calibration gives.
6. On the buffer-stock application the natural borrowing limit is stated
   whole, with the declared sets its two definitions need, and the stage is
   encoded in a valid document of the schema.

The refusals with their sentences are checked in `test_refusals.py`, and what
the public operations answer beside the items in `test_behaviour.py`. The
kernels of item 5 under JAX's `jit` and with JAX's arrays are checked there
by `test_a_kernel_that_reads_a_definition_by_cases_gives_calibration_s_value_under_jax`,
which a run reports as skipped where JAX is not installed.
"""

import json
import math
import warnings

import numpy as np
import pytest
from conftest import (
    DERIVED_BUFFER_STOCK_CALIBRATION,
    PERFECT_FORESIGHT_CALIBRATION,
    derived_buffer_stock_text,
    methodized,
    perfect_foresight_text,
    stage_from_text,
)

from bellman.native.hypergraphs import copy_native
from bellman.native.predicates import Member
from bellman.refusal_examples import EXPLICIT_POLICY
from bellman.refusals import ConstructionError
from bellman.stage.calibration_requirements import (
    declared_set_terms,
    membership,
    predicate_value,
)
from bellman.syntax import terms as T
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source

MEMBERSHIP = "calibration-domain-membership"
GROWTH = 'Γ : ℝ₊₊          :: ["permanent income growth factor"]\n'
HUMAN_WEALTH = "h := 1/(1 - Γ/R)"
RESOURCES = "    m = R_n*k + 1                   :: [id=market_resources]"
# human wealth by cases, on a declared set that holds the infinity of its
# second branch
BY_CASES = "h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf"
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
EXTREMA = (FLOORED, "h := max(1, 2)^(-1)", "h := min(2, 4)^(-2)", INTEGERS)
# a definition by cases whose two branches are integers, under a negative
# integer power: h is 1/2 where Γ < R and 1/3 otherwise
INTEGER_BRANCHES = "h0 := if Γ < R then 2 else 3\nh := h0^(-1)"
# the same two branches under arithmetic that is exact in integers and rounds
# in floats: (h0^60 + 1) - h0^60 is 1 in integers and 0 in floats, and
# calibration, whose value of h0 is a float, gives h the value 1/(1 - Γ/R)
EXACT_INTEGERS = "h0 := if Γ < R then 2 else 3\nh := (h0^60 + 1) - h0^60 + 1/(1 - Γ/R)"
# the sentence of every refusal of one of the three words written as a name
NO_NAME = (
    "`if`, `then` and `else` are the words of a definition by cases, and none of them is a name"
)


def _perfect_foresight(*lines, changes=()):
    """The perfect-foresight stage of the refusal examples with `lines`
    declared after its growth factor and each pair of `changes` replaced."""
    declared = "".join(line + "\n" for line in lines)
    return stage_from_text(perfect_foresight_text((GROWTH, GROWTH + declared), *changes))


def _body(definition):
    """The right side of the one definition a text writes, with or without a
    declared set."""
    term, _ = parse_with_spans(definition + "\n", "t.bl")
    item = term.items[0]
    return item.declaration.value if hasattr(item, "declaration") else item.core.value


def _declared(declaration):
    """The set the lowering keeps for the one declaration, read from the
    parsed line with no stage built."""
    term, _ = parse_with_spans(declaration + "\n", "t.bl")
    (domain,) = [c for c in term.items[-1].declaration.classifiers if isinstance(c, T.Domain)]
    return domain.space


def _open_memberships(stage):
    """The memberships of values that a calibrated stage leaves undecided,
    each as its explanation."""
    return [
        item.explanation
        for item in stage.obligations()
        if item.condition == MEMBERSHIP and item.status == "required"
    ]


def _refused_calibration(stage, values):
    """The sentence with which `stage` refuses the calibration `values`."""
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(values)
    return str(refused.value)


def _condition_of_the_definition(stage, name):
    """The one condition a stage records for the definition of the derived
    parameter `name`."""
    (owned,) = [
        item
        for item in stage.obligations()
        if item.entries and str(item.entries[0]).endswith(f":derived:{name}")
    ]
    return owned


def _conditions_of_the_line(stage):
    """The conditions a stage records for the law of motion of resources,
    each as its name and its explanation."""
    return sorted(
        (item.condition, item.explanation)
        for item in stage.obligations()
        if "arvl_to_dcsn" in item.explanation
    )


def test_item_1_a_derived_parameter_calls_min_and_max_and_is_defined_by_cases():
    # `min` and `max` of one argument or more, beside `log` and `exp`, in a
    # definition without a set, in one that declares a set and in a bound
    stage = _perfect_foresight(
        "θ_min : (0, 1]",
        "ξ_u : ℝ₊",
        "x := min(ξ_u, θ_min*(1 - ξ_u))",
        "y := max(θ_min, ξ_u, 1/R)",
        "z := -min(ξ_u)*log(exp(2))",
        "q : (0, 3) := max(β, R)",
        "b : ℝ₊₊ @ (0, min(R, 2))",
    )
    assert all(stage.par[name].derived for name in ("x", "y", "z", "q"))
    assert str(stage.par["y"]) == "y := max(θ_min, ξ_u, 1/R), unbound"
    assert str(stage.par["q"]) == "q : (0, 3) := max(β, R), unbound"
    assert str(stage.par["b"]) == "b : ℝ₊₊ @ (0, min(R, 2)), unbound"
    assert not stage.par["b"].derived
    # a definition by cases, with each relation, with nested branches and
    # with an infinity as a whole branch, is printed as it is read, and its
    # printed form is read back as the same term, after `:=` alone and after
    # a declared set
    cases = (
        "if a < 0 then -1 else 1",
        "if a <= b then 1 else 2",
        "if a = b then 1 else 2",
        "if a >= b then 1 else 2",
        "if a > b then 1 else 2",
        "if a < 0 then -1 else if a = 0 then 0 else 1",
        "if p_zero = 0 then θ_min else min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))",
        "if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf",
        "if a >= b then inf else if a + 1 > b^2 then log(a) else exp(-b)",
    )
    for text in cases:
        body = _body(f"x := {text}")
        assert to_source(body) == text
        for declared in ("ℝ̄", "(0, 3) \\/ [5, inf]", "ℝ₊₊ @ (0, R)"):
            assert _body(f"x : {declared} := {to_source(body)}") == body, (declared, text)
    # the second spellings of the relations, of the infinity and of `:=`
    assert _body("x := if a ≤ b then ∞ else 1") == _body("x := if a <= b then inf else 1")
    assert _body("x : ℝ̄ <- if a ≥ b then 1 else 2") == _body("x : ℝ̄ := if a >= b then 1 else 2")
    # a definition by cases that declares a set defines a derived parameter,
    # in a stage file and in a methods file
    typed = _perfect_foresight("q : (0, 3) := if β < R then 1 else 2")
    assert typed.par["q"].derived and to_source(typed.par["q"].domain) == "(0, 3)"
    assert str(typed.par["q"]) == "q : (0, 3) := if β < R then 1 else 2, unbound"
    added = methodized(typed, "κ : (0, 3) \\/ {5} := if q < R then 1 else 5\n")
    assert str(added.par["κ"]) == "κ : (0, 3) \\/ {5} := if q < R then 1 else 5, unbound"
    assert "κ" not in added.settings
    # a definition that declares a set reads a parameter, by cases as
    # otherwise: one that reads none is refused as `ρ : ℝ := 2` is
    with pytest.raises(ConstructionError) as refused:
        _perfect_foresight("q : (0, 3) := if 1 < 2 then 1 else 2")
    assert refused.value.rule == "readable-form"
    # `if`, `then` and `else` are words of the language and no names; a name
    # that begins with one of them is a name
    named = _perfect_foresight("iffy := 3*R", "thenar := 2*R", "elsewhere := thenar + iffy")
    assert str(named.par["elsewhere"]) == "elsewhere := thenar + iffy, unbound"
    for word in ("if", "then", "else"):
        for lines in ((f"{word} := 2*R",), (f"{word} : ℝ₊₊",), (f"x := 1 + {word}",)):
            with pytest.raises(ConstructionError) as refused:
                _perfect_foresight(*lines)
            assert refused.value.rule == "syntax", lines
            assert f"the file writes `{word}` as a name; {NO_NAME}" in refused.value.message, lines


def test_item_2_the_value_is_the_branch_the_test_chooses():
    values = PERFECT_FORESIGHT_CALIBRATION
    stage = _perfect_foresight(changes=((HUMAN_WEALTH, BY_CASES),))
    assert list(stage.par) == ["β", "ρ", "R", "Γ", "h", "R_n"] and stage.par["h"].derived
    # R = 1.04 and Γ = 1.02: the first branch, 52
    assert copy_native(stage).calibrate(values).par["h"].value == pytest.approx(52.0)
    # Γ = R and Γ > R: the second branch, and the division of the first is
    # not made, which without the conditional refuses the calibration
    for growth in (1.04, 1.05):
        bound = copy_native(stage).calibrate({**values, "Γ": growth})
        assert bound.par["h"].value == math.inf and "h" not in bound.bindings.calibration
    with pytest.raises(ConstructionError, match="the divisor `1 - Γ/R` is 0.0"):
        _perfect_foresight().calibrate({**values, "Γ": 1.04})
    # each relation, a nested conditional, each infinity, and `min`, `max`
    # and `log` in a test and in a branch
    for definition, value in (
        ("h := if Γ <= R then 1 else 2", 1.0),
        ("h := if Γ = R then 1 else 2", 2.0),
        ("h := if Γ >= R then 1 else 2", 2.0),
        ("h : ℝ_{-∞} := if Γ > R then 1 else -inf", -math.inf),
        ("h := if R - Γ > 1 then 1 else if R - Γ > 0 then 2 else 3", 2.0),
        ("h := if max(Γ, R) = R then min(Γ, R) else log(R)", 1.02),
    ):
        bound = _perfect_foresight(changes=((HUMAN_WEALTH, definition),)).calibrate(values)
        assert bound.par["h"].value == pytest.approx(value), definition
    # `min` and `max` are the least and the greatest of their arguments;
    # R = 1.04 and Γ = 1.02, so that 1 - Γ/R is 1/52
    low = {"θ_min": 0.3, "ξ_u": 0.1}
    for definition, value in (
        ("x := min(ξ_u, θ_min)", 0.1),
        ("x := max(ξ_u, θ_min)", 0.3),
        ("x := min(θ_min, ξ_u, 1/R)", 0.1),
        ("x := max(θ_min, ξ_u, 1/R)", 1 / 1.04),
        ("x := min(ξ_u)", 0.1),
        ("x := 1/max(1 - Γ/R, 1/2)", 2.0),
        ("x := -min(ξ_u, θ_min)*log(exp(2))", -0.2),
        ("x := max(h, 60) - min(h, 60)", 8.0),
    ):
        bound = _perfect_foresight("θ_min : (0, 1]", "ξ_u : ℝ₊", definition).calibrate(
            {**values, **low}
        )
        assert bound.par["x"].value == pytest.approx(value), definition
        assert "x" not in bound.bindings.calibration
    # every argument of `min` and `max` is evaluated: one without a value
    # refuses the definition, whichever argument is the least
    with pytest.raises(ConstructionError) as refused:
        _perfect_foresight("ξ_u : ℝ₊", "x := min(ξ_u, 1/(R - Γ))").calibrate(
            {**values, "ξ_u": 0.1, "Γ": 1.04}
        )
    assert refused.value.rule == "derived-parameter"
    assert "the divisor `R - Γ` is 0.0" in refused.value.message
    # the chosen branch is evaluated as any definition is, and a zero that
    # floating point rounded from a nonzero result decides no test
    for definition, words in (
        ("h := if Γ < R then 1/(β - β) else 2", "the divisor `β - β` is 0.0"),
        ("h := if exp(-800*R) = 0 then 1 else 2", "decides no comparison"),
    ):
        with pytest.raises(ConstructionError) as refused:
            _perfect_foresight(changes=((HUMAN_WEALTH, definition),)).calibrate(values)
        assert refused.value.rule == "derived-parameter" and words in refused.value.message
    # no arithmetic of infinities is defined: a formula, a call and a test
    # of another definition that read the infinite value have no value
    for definition, finite in (
        ("limit := 1 - h", -51.0),
        ("limit := max(h, 60)", 60.0),
        ("limit := if h > 60 then 1 else 0", 0.0),
    ):
        reads = _perfect_foresight(changes=((HUMAN_WEALTH, f"{BY_CASES}\n{definition}"),))
        assert copy_native(reads).calibrate(values).par["limit"].value == pytest.approx(finite)
        with pytest.raises(ConstructionError) as refused:
            copy_native(reads).calibrate({**values, "Γ": 1.04})
        assert refused.value.rule == "derived-parameter", definition
        assert "the value inf of h is no finite number" in refused.value.message, definition
    # a bound that calls `min` is decided at calibration, and a definition
    # that declares a set, written with `max` or by cases, is held to it
    bounded = _perfect_foresight("b : ℝ₊₊ @ (0, min(R, 2))", "q : (0, 3) := max(β, R)")
    assert _open_memberships(copy_native(bounded).calibrate({**values, "b": 1.0})) == []
    assert "the condition b < min(R, 2) of the declared set at R = 1.04" in _refused_calibration(
        bounded, {**values, "b": 1.5}
    )
    assert "derived parameter 'q'" in _refused_calibration(bounded, {**values, "b": 1.0, "R": 3.5})
    typed = _perfect_foresight(
        "w : (0, 10) := if Γ < R then 1/(1 - Γ/R) else 1", changes=((HUMAN_WEALTH, BY_CASES),)
    )
    assert copy_native(typed).calibrate({**values, "Γ": 1.04}).par["w"].value == 1.0
    sentence = _refused_calibration(typed, values)
    assert "derived parameter 'w'" in sentence
    assert "lies outside the declared set (0, 10) at R = 1.04, Γ = 1.02" in sentence


def test_item_3_an_infinite_branch_needs_a_declared_set_that_holds_it():
    values = PERFECT_FORESIGHT_CALIBRATION
    cases = "if Γ < R then 1/(1 - Γ/R) else inf"
    # a definition whose declared set cannot hold the infinity that a branch
    # writes is refused when the file is read, with the set to write: the
    # set ℝ of a definition that declares none, a real set, an interval that
    # is open or finite at that end, a set that holds the other infinity,
    # and a set of extended reals with a condition that excludes the
    # infinity, written with `@` or as a named set with a bar
    for declared, written in (
        (None, "the set ℝ of a definition that declares none"),
        ("ℝ", "its declared set `ℝ`"),
        ("ℝ₊₊", "its declared set `ℝ₊₊`"),
        ("(0, inf)", "its declared set `(0, inf)`"),
        ("(0, 100]", "its declared set `(0, 100]`"),
        ("ℝ_{-∞}", "its declared set `ℝ_{-∞}`"),
        ("(0, 1) \\/ (2, inf)", "its declared set `(0, 1) \\/ (2, inf)`"),
        ("ℝ̄ @ (0, inf)", "its declared set `ℝ̄ @ (0, inf)`"),
        ("ℝ_{+∞} @ (0, 100]", "its declared set `ℝ_{+∞} @ (0, 100]`"),
        ("Xe", "its declared set `Xe`"),
    ):
        definition = f"h := {cases}" if declared is None else f"h : {declared} := {cases}"
        # the named set is defined on the line before the definition
        named = "Xe := {x : ℝ̄ | x < 100}\n" if declared == "Xe" else ""
        with pytest.raises(ConstructionError) as refused:
            _perfect_foresight(changes=((HUMAN_WEALTH, named + definition),))
        error = refused.value
        assert (error.rule, error.line) == ("derived-parameter", 9 if named else 8), definition
        assert (
            f"the derived parameter h, defined as `{cases}`, writes the branch `inf`, and "
            f"{written} cannot hold inf; "
        ) in error.message, error.message
        assert error.write.startswith(f"Write `h : ℝ_{{+∞}} := {cases}`"), error.write
    # the set to write holds each infinity that the definition writes
    for definition, advised in (
        ("h := if Γ < R then 1 else -inf", "ℝ_{-∞}"),
        ("h : ℝ_{+∞} := if Γ < R then inf else if Γ = R then 0 else -inf", "ℝ̄"),
    ):
        with pytest.raises(ConstructionError) as refused:
            _perfect_foresight(changes=((HUMAN_WEALTH, definition),))
        assert refused.value.rule == "derived-parameter", definition
        assert "writes the branch `-inf`" in refused.value.message, definition
        assert refused.value.write.startswith(f"Write `h : {advised} := "), refused.value.write
    # a declared set that holds the infinity is read: an extended real set
    # that reaches that side, an interval closed at that infinite endpoint, a
    # union with such a member, and a set that a named set defines
    for definition in (
        f"h : ℝ_{{+∞}} := {cases}",
        f"h : ℝ̄ := {cases}",
        f"h : ℝ_{{±∞}} := {cases}",
        f"h : (0, inf] := {cases}",
        f"h : (0, 1) \\/ [2, inf] := {cases}",
        f"Xh := (0, inf]\nh : Xh := {cases}",
        "h : ℝ_{-∞} := if Γ < R then 1 else -inf",
        "h : [-inf, inf] := if Γ < R then inf else if Γ = R then 0 else -inf",
    ):
        assert _perfect_foresight(changes=((HUMAN_WEALTH, definition),)).par["h"].derived
    # a named set that cannot hold the infinity is read through its definition
    with pytest.raises(ConstructionError) as refused:
        _perfect_foresight(changes=((HUMAN_WEALTH, f"Xh := (0, 100]\nh : Xh := {cases}"),))
    assert refused.value.rule == "derived-parameter"
    assert "its declared set `Xh` cannot hold inf" in refused.value.message
    # at a calibration the value, finite or infinite, is held to the declared
    # set, as the value of any derived parameter with a declared set is
    for declared in ("ℝ_{+∞}", "ℝ̄", "(0, inf]", "(0, 1) \\/ [2, inf]"):
        stage = _perfect_foresight(changes=((HUMAN_WEALTH, f"h : {declared} := {cases}"),))
        for growth, value in ((1.02, pytest.approx(52.0)), (1.04, math.inf)):
            bound = copy_native(stage).calibrate({**values, "Γ": growth})
            assert bound.par["h"].value == value, (declared, growth)
            assert _open_memberships(bound) == [], (declared, growth)
    narrow = _perfect_foresight(changes=((HUMAN_WEALTH, f"h : [60, inf] := {cases}"),))
    assert copy_native(narrow).calibrate({**values, "Γ": 1.04}).par["h"].value == math.inf
    sentence = _refused_calibration(narrow, values)
    assert "derived parameter 'h'" in sentence
    assert "lies outside the declared set [60, inf] at R = 1.04, Γ = 1.02" in sentence
    # where the set holds the infinity only at some calibrations, the file is
    # read and calibration judges: with T the upper endpoint, the infinite
    # value lies in (0, T] where T is infinite and outside it where T is 100
    valued = _perfect_foresight("T : ℝ_{+∞}", changes=((HUMAN_WEALTH, f"h : (0, T] := {cases}"),))
    at_infinity = copy_native(valued).calibrate({**values, "Γ": 1.04, "T": math.inf})
    assert at_infinity.par["h"].value == math.inf and _open_memberships(at_infinity) == []
    sentence = _refused_calibration(valued, {**values, "Γ": 1.04, "T": 100.0})
    assert "derived parameter 'h'" in sentence
    assert "the value inf of h" in sentence and "lies outside the declared set (0, T]" in sentence
    # the definition owns one condition, that it has a value in the set of
    # extended reals of the sides that its declared set may hold, here
    # ℝ_{+∞}, which calibration establishes at a finite and at an infinite
    # value
    stage = _perfect_foresight(changes=((HUMAN_WEALTH, BY_CASES),))
    finite = copy_native(stage).calibrate(values)
    infinite = copy_native(stage).calibrate({**values, "Γ": 1.04})
    for version, status in (
        (stage, "required"),
        (finite, "established"),
        (infinite, "established"),
    ):
        owned = _condition_of_the_definition(version, "h")
        assert (owned.condition, owned.status) == ("arithmetic-definedness", status)
        assert owned.explanation == (
            f"The derived parameter h, defined as `{cases}`, must have a value in ℝ_{{+∞}} at "
            "the calibration."
        )
    # the declared set itself is no part of that condition: the check of the
    # value against the declared set judges it. A calibration that the check
    # admits therefore establishes the condition also where an endpoint of
    # the declared set is a name or the set has conditions, for a definition
    # that writes no infinity and for a definition by cases, at a finite and
    # at an infinite value
    for lines, definition, calibrations in (
        (("T : ℝ₊₊",), "h : (0, T] := 1/(1 - Γ/R)", ({"T": 100.0},)),
        (
            ("T : ℝ_{+∞}",),
            f"h : (0, T] := {cases}",
            ({"T": 100.0}, {"Γ": 1.04, "T": math.inf}),
        ),
        ((), f"h : ℝ̄ @ (0, inf] := {cases}", ({}, {"Γ": 1.04})),
    ):
        typed = _perfect_foresight(*lines, changes=((HUMAN_WEALTH, definition),))
        for changed in calibrations:
            bound = copy_native(typed).calibrate({**values, **changed})
            assert _open_memberships(bound) == [], (definition, changed)
            owned = _condition_of_the_definition(bound, "h")
            assert (owned.condition, owned.status) == ("arithmetic-definedness", "established"), (
                definition,
                changed,
            )
        symbolic = _condition_of_the_definition(typed, "h")
        assert (symbolic.condition, symbolic.status) == ("arithmetic-definedness", "required")
        assert symbolic.explanation.endswith("must have a value in ℝ_{+∞} at the calibration.")
    # a definition by cases without an infinite branch owns the condition of
    # a finite real value, as a definition that calls `log` does
    plain = _perfect_foresight(
        changes=((HUMAN_WEALTH, "h := if Γ < R then 1/(1 - Γ/R) else 1000"),)
    )
    for version, status in (
        (plain, "required"),
        (copy_native(plain).calibrate(values), "established"),
    ):
        owned = _condition_of_the_definition(version, "h")
        assert (owned.condition, owned.status) == ("arithmetic-definedness", status)
        assert owned.explanation.endswith("must have a finite real value at the calibration.")
    # the records print the definition with its set, and the infinity
    assert str(stage.par["h"]) == f"{BY_CASES}, unbound"
    assert str(infinite.par["h"]) == f"h = inf : ℝ_{{+∞}} := {cases}"
    (identity,) = [each for each in infinite.definitions if str(each).endswith(":derived:h")]
    card = str(infinite.definitions.denote(identity))
    assert "h  ∈ ℝ_{+∞},  := if Γ < R then 1/(1 − Γ/R) else ∞" in card and "= ∞" in card


def test_item_4_one_reading_of_an_infinite_value(encoding_validator):
    values = PERFECT_FORESIGHT_CALIBRATION
    # debt is bounded by human wealth, and unbounded where human wealth is.
    # One stage defines human wealth by cases, the other declares it on the
    # extended reals, and both ask whether a value of debt lies in [0, ∞)
    derived = _perfect_foresight("debt : ℝ₊ @ [0, h)", changes=((HUMAN_WEALTH, BY_CASES),))
    declared = _perfect_foresight("debt : ℝ₊ @ [0, h)", changes=((HUMAN_WEALTH, "h : ℝ_{+∞}"),))
    finite = copy_native(derived).calibrate({**values, "debt": 10.0})
    infinite = copy_native(derived).calibrate({**values, "Γ": 1.04, "debt": 1e6})
    assert (finite.par["h"].value, infinite.par["h"].value) == (pytest.approx(52.0), math.inf)
    supplied = copy_native(declared).calibrate({**values, "h": math.inf, "debt": 1e6})
    assert _open_memberships(infinite) == _open_memberships(supplied) == []
    for stage, at in ((derived, {"Γ": 1.04}), (declared, {"h": math.inf})):
        assert "parameter 'debt'" in _refused_calibration(stage, {**values, **at, "debt": -1.0})
    sentence = _refused_calibration(derived, {**values, "debt": 60.0})
    assert "parameter 'debt'" in sentence
    assert "the condition debt < h of the declared set at h = 51.99" in sentence
    # the infinity as a lower endpoint leaves no number in the set
    for stage, at in (
        (_perfect_foresight("w : (h, inf)", changes=((HUMAN_WEALTH, BY_CASES),)), {"Γ": 1.04}),
        (_perfect_foresight("T : ℝ̄", "w : (T, inf)"), {"T": math.inf}),
    ):
        assert "the value 1000000.0 lies outside the declared set" in _refused_calibration(
            stage, {**values, **at, "w": 1e6}
        )
    # a parameter declared on the extended reals: a finite number lies in
    # every such set, and an infinity in the sets that reach its side
    for declared_set, inside, outside in (
        ("ℝ̄", (5.0, math.inf, -math.inf), ()),
        ("ℝ_{+∞}", (5.0, math.inf), (-math.inf,)),
        ("ℝ_{-∞}", (5.0, -math.inf), (math.inf,)),
        ("(0, inf]", (5.0, math.inf), (-math.inf, 0.0)),
    ):
        stage = _perfect_foresight(f"T : {declared_set}")
        for value in inside:
            bound = copy_native(stage).calibrate({**values, "T": value})
            assert _open_memberships(bound) == [], (declared_set, value)
        for value in outside:
            assert (
                f"the value {value!r} lies outside the declared set {declared_set}"
            ) in _refused_calibration(stage, {**values, "T": value}), (declared_set, value)
    # the two procedures that judge a membership give one answer for each
    # infinity in every form of a set, and for a finite number in the sets
    # of extended reals: `membership`, which judges a value against its
    # declared set, and `predicate_value`, which judges a condition that a
    # stage records
    sets_of_numbers = _perfect_foresight("T : ℝ̄", "Xe := {x : ℝ̄ | x >= 0}", "Xr := [0, inf)")
    definitions, named = dict(sets_of_numbers.definitions), declared_set_terms(sets_of_numbers)
    at = {**values, "T": math.inf}
    answers = {
        "ℝ": (False, False),
        "ℝ₊₊": (False, False),
        "ℤ": (False, False),
        "ℝ̄": (True, True),
        "ℝ_{+∞}": (True, False),
        "ℝ_{-∞}": (False, True),
        "ℝ_{±∞}": (True, True),
        "(0, inf)": (False, False),
        "(0, inf]": (True, False),
        "[-inf, 0)": (False, True),
        "[-inf, inf]": (True, True),
        "(0, T]": (True, False),
        "(0, T)": (False, False),
        "{1, …, 5}": (False, False),
        "ℝ̄ @ (0, inf)": (False, False),
        "ℝ̄ @ (0, inf]": (True, False),
        "(0, 1) \\/ (1, inf]": (True, False),
        "ℝ̄ \\ (0, inf]": (False, True),
        "ℝ \\ {0}": (False, False),
        "Xe": (True, False),
        "Xr": (False, False),
        "Foo": (None, None),
    }
    for written, held in answers.items():
        setexpr = _declared(f"x : {written}")
        for infinity, answer in zip((math.inf, -math.inf), held):
            judged = membership(sets_of_numbers, definitions, setexpr, infinity, at)[0]
            assert (judged if judged in (True, False) else None) is answer, (written, infinity)
            predicate = Member(T.Sym(T.Constant("w")), setexpr)
            assert predicate_value(predicate, {**at, "w": infinity}, named).value is answer, (
                written,
                infinity,
            )
    for written in ("ℝ̄", "ℝ_{+∞}", "ℝ_{-∞}", "ℝ_{±∞}"):
        setexpr = _declared(f"x : {written}")
        assert membership(sets_of_numbers, definitions, setexpr, 5.0, at)[0] is True
        assert predicate_value(Member(T.Sym(T.Constant("w")), setexpr), {"w": 5.0}).value is True
    # a bound that computes with a name valued at an infinity has no value,
    # and the calibration is refused at that bound, as it is for a bound
    # that divides by zero; the bare name alone is read as the infinity. A
    # bound that computes with the written infinity, `2*inf`, has one answer
    # with it: it has no value, whatever the calibration
    for bound in ("2*h", "h + 1", "h/2", "max(h, 1)", "-h", "2*inf", "max(inf, 1)"):
        low = "-inf" if bound == "-h" else "0"
        sign = "debt : ℝ₊" if bound != "-h" else "debt : ℝ"
        for stage, at_infinity, supplies in (
            (
                _perfect_foresight(
                    f"{sign} @ ({low}, {bound})", changes=((HUMAN_WEALTH, BY_CASES),)
                ),
                {"Γ": 1.04},
                f"h = inf (the derived parameter {BY_CASES.replace('h : ℝ_{+∞} := ', 'h := ')})",
            ),
            (
                _perfect_foresight(
                    f"{sign} @ ({low}, {bound})", changes=((HUMAN_WEALTH, "h : ℝ_{+∞}"),)
                ),
                {"h": math.inf},
                "h = inf",
            ),
        ):
            sentence = _refused_calibration(stage, {**values, **at_infinity, "debt": 1.0})
            assert "parameter 'debt'" in sentence, bound
            reason = (
                "has no value: it computes with `inf`, and no arithmetic of infinities is defined"
                if "inf" in bound
                else f"has no value at {supplies}: the value inf of h is no finite number"
            )
            assert (
                f"the bound `{bound}` of the declared set {sign[7:]} @ ({low}, {bound}) {reason}; "
                "a declared set is defined at the values only where each of its bounds has a "
                "value; "
            ) in sentence, sentence
            if "inf" in bound:
                assert sentence.endswith("; write another bound"), sentence
                # refused at a finite value of h as well
                at_52 = {"h": 52.0} if "h" in at_infinity else {}
                assert reason in _refused_calibration(stage, {**values, **at_52, "debt": 1.0})
    # a setting's set is judged so at configuration
    configured = methodized(
        _perfect_foresight(changes=((HUMAN_WEALTH, BY_CASES),)), "tol : (0, h + 1)\n"
    ).calibrate({**values, "Γ": 1.04})
    with pytest.raises(ConstructionError) as refused:
        copy_native(configured).configure({"tol": 0.5})
    assert refused.value.rule == "setting-outside-set"
    assert "the bound `h + 1` of the declared set (0, h + 1) has no value" in refused.value.message
    # a key `inf` of a calibration source or of a settings source is no name
    # of a stage that declares none, so a bound that computes with the
    # written infinity has no value there either
    stray = _perfect_foresight("debt : ℝ₊ @ (0, 2*inf)")
    assert "it computes with `inf`" in _refused_calibration(
        stray, {**values, "debt": 1.0, "inf": 3.0}
    )
    with_setting = methodized(_perfect_foresight(), "tol : (0, 2*inf)\n").calibrate(values)
    with pytest.raises(ConstructionError) as refused:
        copy_native(with_setting).configure({"tol": 0.5, "inf": 3.0})
    assert "it computes with `inf`" in refused.value.message
    # a line of a block that computes with a derived parameter whose declared
    # set may hold an infinity owns the conditions that a parameter declared
    # on that set gives it; every other derived parameter is read as a real
    # number, as before, whatever set its definition declares
    line = (RESOURCES, "    m = R_n*k + 1 + h - h           :: [id=market_resources]")
    owned = {
        definition: _conditions_of_the_line(
            stage_from_text(perfect_foresight_text((HUMAN_WEALTH, definition), line))
        )
        for definition in (BY_CASES, "h : ℝ_{+∞}", "h : (0, inf] := 1/(1 - Γ/R)", "h : (0, inf]")
        + (HUMAN_WEALTH, "h : (0, 100) := 1/(1 - Γ/R)", "h : ℝ̄ @ (0, 100) := 1/(1 - Γ/R)")
    }
    assert owned[BY_CASES] == owned["h : ℝ_{+∞}"]
    assert owned["h : (0, inf] := 1/(1 - Γ/R)"] == owned["h : (0, inf]"]
    assert owned[HUMAN_WEALTH] == owned["h : (0, 100) := 1/(1 - Γ/R)"] == []
    # a set of extended reals whose conditions exclude both infinities holds
    # none, so the line owns no further condition
    assert owned["h : ℝ̄ @ (0, 100) := 1/(1 - Γ/R)"] == []
    assert (
        "finite-real-arithmetic",
        "The operands of Sub at arvl_to_dcsn.market_resources must be finite real numbers.",
    ) in owned[BY_CASES]
    assert (
        "numeric-domain-compatibility",
        "The set ℝ_{+∞} used in arithmetic at arvl_to_dcsn.market_resources must be numeric.",
    ) in owned[BY_CASES]
    # at the infinite value the line's conditions stay required, as they do
    # for the parameter, and a power of the infinite value is refused with a
    # sentence that is true of it
    computed = stage_from_text(perfect_foresight_text((HUMAN_WEALTH, BY_CASES), line))
    at_infinity = copy_native(computed).calibrate({**values, "Γ": 1.04})
    assert {
        item.status for item in at_infinity.obligations() if "market_resources" in item.explanation
    } == {"required"}
    power = (RESOURCES, "    m = R_n*k + h^(1/2)             :: [id=market_resources]")
    rooted = stage_from_text(perfect_foresight_text((HUMAN_WEALTH, BY_CASES), power))
    assert copy_native(rooted).calibrate(values).par["h"].value == pytest.approx(52.0)
    sentence = _refused_calibration(rooted, {**values, "Γ": 1.04})
    assert "calibration h = inf makes" in sentence and "h > 0 false" not in sentence
    # the encoding of the symbolic stage and of each calibrated stage is
    # strict JSON and a document of the schema; the value at the infinite
    # branch is written {"float": "inf"}, as the encoding's definitions write
    # a parameter calibrated at an infinity
    written = {}
    for name, version in (("symbolic", derived), ("finite", finite), ("infinite", infinite)):
        written[name] = json.dumps(version.encoding(), allow_nan=False, ensure_ascii=False)
        encoding_validator.validate(json.loads(written[name]))
    assert '{"float": "inf"}' in written["infinite"]
    assert '{"float": "inf"}' not in written["finite"]
    # a definition that calls min and max is encoded as before
    encoding_validator.validate(
        _perfect_foresight(changes=((HUMAN_WEALTH, "h := max(min(Γ, R), 1/2)"),)).encoding()
    )


def test_item_5_a_compiled_kernel_selects_between_the_branches():
    values = {**PERFECT_FORESIGHT_CALIBRATION, "N": 2, "M": 4}
    resources = np.array([0.0, 1.0, 10.0])
    # consumption at human wealth h, (1 - (Rβ)^(1/ρ)/R)(m - 1 + h), at Rβ = 1
    consumed = lambda wealth: 0.04 / 1.04 * (resources - 1 + np.asarray(wealth))  # noqa: E731
    symbolic, kernels = {}, {}
    for definition in (BY_CASES, FINITE, UNDEFINED, *EXTREMA, INTEGER_BRANCHES, EXACT_INTEGERS):
        integers = ("N : ℤ", "M : ℤ") if definition == INTEGERS else ()
        symbolic[definition] = _perfect_foresight(*integers, changes=((HUMAN_WEALTH, definition),))
        explicit = {"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"}
        stage = methodized(symbolic[definition], explicit).calibrate({"calibration": values})
        consumption = stage.builder.policy.primitives["consumption:Aggregation"]
        kernel = consumption.kernel()
        held = dict(zip(kernel.parameters, kernel.parameter_values, strict=True))
        kernels[definition] = (kernel, consumption.compile_kernel(), held)
    # the value calibration gives h at one change of the calibration values
    wealth = lambda definition, change: (  # noqa: E731
        copy_native(symbolic[definition]).calibrate({**values, **change}).par["h"].value
    )

    # the kernel's text: the conditional through `by_cases`, `min` and `max`
    # as NumPy writes them, the first argument a float where no argument is
    # surely one, and the declared parameters alone
    written = {definition: kernels[definition][0].python for definition in kernels}
    declared = ("β", "ρ", "R", "Γ")
    assert kernels[BY_CASES][0].parameters == kernels[FLOORED][0].parameters == declared
    assert kernels[INTEGERS][0].parameters == ("β", "ρ", "R", "N", "M")
    assert f"# derived parameter: {BY_CASES}\n" in written[BY_CASES]
    assert "    h = by_cases(Γ < R, lambda: 1/(1 - Γ/R), lambda: np.inf)\n" in written[BY_CASES]
    assert "    h = 1/np.maximum(np.maximum(1 - Γ/R, 1/100), 1/200)\n" in written[FLOORED]
    assert "    h = np.maximum(1.0*N, M)**(-1)\n" in written[INTEGERS]
    assert "    h = np.minimum(1.0*2, 4)**(-2)\n" in written["h := min(2, 4)^(-2)"]
    assert "    h0 = by_cases(Γ < R, lambda: 2, lambda: 3)\n" in written[INTEGER_BRANCHES]
    assert "    h = h0**(-1)\n" in written[INTEGER_BRANCHES]
    growths = (1.02, 1.04, 1.05)
    calibrated = {
        definition: [wealth(definition, {"Γ": growth}) for growth in growths]
        for definition in (BY_CASES, FINITE, INTEGER_BRANCHES)
    }
    assert calibrated[BY_CASES] == pytest.approx([52.0, math.inf, math.inf])
    assert calibrated[FINITE] == pytest.approx([52.0, 1000.0, 1000.0])
    assert calibrated[INTEGER_BRANCHES] == pytest.approx([1 / 2, 1 / 3, 1 / 3])
    undefined = {
        risk: [wealth(UNDEFINED, {"ρ": risk, "Γ": growth}) for growth in (1.02, 1.03, 1.02)]
        for risk in (2.0, 2.5)
    }
    extrema = [wealth(definition, {}) for definition in EXTREMA]
    assert extrema == pytest.approx([52.0, 0.5, 0.25, 0.25])
    assert kernels[INTEGERS][2]["N"] == 2 and kernels[INTEGERS][2]["M"] == 4

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for definition in (BY_CASES, FINITE, INTEGER_BRANCHES):
            kernel, compiled, held = kernels[definition]
            # a scalar test evaluates the chosen branch alone: at Γ = R the
            # first branch, which divides by zero, is not evaluated
            for growth, value in zip(growths, calibrated[definition], strict=True):
                assert np.allclose(compiled(resources, **{**held, "Γ": growth}), consumed(value))
            # an array of growth factors on both sides of R: the first branch
            # divides by zero at Γ = R, where the test chooses the second;
            # two integer branches are selected as floats, so that the
            # negative power of the selected value is that of calibration
            several = compiled(resources, **{**held, "Γ": np.array(growths)})
            assert np.allclose(several, consumed(calibrated[definition])), definition
        # two integer branches at a test that is one truth value: the chosen
        # branch is a float, as calibration's value is, so that arithmetic
        # which is exact in integers gives the kernel what it gives
        # calibration, at one growth factor as at an array of them; h has no
        # value at Γ = R
        kernel, compiled, held = kernels[EXACT_INTEGERS]
        either_side = (1.02, 1.05, 1.02)
        exact = [wealth(EXACT_INTEGERS, {"Γ": growth}) for growth in either_side]
        assert exact == pytest.approx([52.0, -104.0, 52.0])
        for growth, value in zip(either_side, exact, strict=True):
            one = compiled(resources, **{**held, "Γ": growth})
            assert np.allclose(one, consumed(value)), (growth, one, consumed(value))
        several = compiled(resources, **{**held, "Γ": np.array(either_side)})
        assert np.allclose(several, consumed(exact))
        # the test holds at each entry, and the second branch, chosen at none,
        # has no real value at either ρ
        kernel, compiled, held = kernels[UNDEFINED]
        for risk, value in undefined.items():
            for growth, one in zip((1.02, 1.03, 1.02), value, strict=True):
                assert np.allclose(
                    compiled(resources, **{**held, "ρ": risk, "Γ": growth}), consumed(one)
                )
            answer = compiled(resources, **{**held, "ρ": risk, "Γ": np.array([1.02, 1.03, 1.02])})
            assert np.isrealobj(answer) and np.allclose(answer, consumed(value)), risk
        # min and max of floats, and of integers, written as numbers or held
        # by parameters, under a negative integer power, as calibration gives
        # them
        for definition, value in zip(EXTREMA, extrema, strict=True):
            kernel, compiled, held = kernels[definition]
            assert np.allclose(compiled(resources, *kernel.parameter_values), consumed(value))


def test_item_6_the_natural_borrowing_limit_of_the_buffer_stock_model_stated_whole(
    encoding_validator,
):
    probability = 'p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]\n'
    text = derived_buffer_stock_text()
    assert text.count(probability) == 1
    # the lowest transitory income is the employed floor where the
    # unemployment event has probability zero, and otherwise the lower of
    # that floor and the income in unemployment; the natural borrowing limit
    # is the negative of its present value at the lowest permanent shock
    # where Γ*ψ_min < R, and no finite number otherwise, so that its declared
    # set holds -inf
    lines = (
        "θ_min : (0, 1]",
        "ψ_min : (0, 1]",
        "ξ_u : ℝ₊",
        "ξ_min := if p_zero = 0 then θ_min else min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))",
        "a_Nat : ℝ_{-∞} := if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf",
        "a_Art : (-inf, 0] @ (a_Nat, inf)",
    )
    # the unemployment event may be absent in this stage
    absent = probability.replace("(0,1)", "[0,1)")
    stage = stage_from_text(
        text.replace(probability, absent + "".join(line + "\n" for line in lines)),
        "buffer_stock.bl",
    )
    # Γ = R = 1.03 and ψ_min = 0.8: the limit is -4 times the lowest income
    values = {**DERIVED_BUFFER_STOCK_CALIBRATION, "θ_min": 0.3, "ξ_u": 0.1, "ψ_min": 0.8}

    def bound_at(**changed):
        return copy_native(stage).calibrate({**values, **changed})

    def limits(**changed):
        bound = bound_at(**changed)
        assert _open_memberships(bound) == [], changed
        return bound.par["ξ_min"].value, bound.par["a_Nat"].value

    # the event has positive probability: the lower of the unemployment
    # income and the employed floor
    assert limits(a_Art=-0.3) == (pytest.approx(0.1), pytest.approx(-0.4))
    # where the unemployment income exceeds the employed floor, the floor is
    # the lowest income: 0.3*(1 - 0.005*0.5)/0.995
    floor = 0.3 * (1 - 0.005 * 0.5) / 0.995
    assert limits(ξ_u=0.5, a_Art=-1.0) == (pytest.approx(floor), pytest.approx(-4 * floor))
    # the event is absent: the employed floor, whatever the income in it
    for unemployed in (0.1, 0.0):
        assert limits(p_zero=0.0, ξ_u=unemployed, a_Art=-1.0) == (
            pytest.approx(0.3),
            pytest.approx(-1.2),
        )
    # an artificial limit below the natural one is refused
    with pytest.raises(ValueError) as refused:
        bound_at(a_Art=-0.5)
    assert "parameter 'a_Art'" in str(refused.value)
    assert "the condition a_Art > a_Nat of the declared set at a_Nat = -0.4" in str(refused.value)
    with pytest.raises(ValueError, match="parameter 'a_Art'"):
        bound_at(p_zero=0.0, a_Art=-1.3)
    # Γ*ψ_min = R and Γ*ψ_min > R: no finite natural limit, and every
    # artificial limit is admitted
    for changed in ({"ψ_min": 1.0}, {"ψ_min": 1.0, "R": 1.01}):
        assert limits(a_Art=-50.0, **changed)[1] == -math.inf
        assert limits(a_Art=0.0, **changed)[1] == -math.inf
    # the stage is encoded in a valid document of the schema, symbolic and
    # calibrated at a finite and at an infinite natural limit
    for version in (stage, bound_at(a_Art=-0.3), bound_at(a_Art=-50.0, ψ_min=1.0)):
        document = json.dumps(version.encoding(), allow_nan=False, ensure_ascii=False)
        encoding_validator.validate(json.loads(document))
    assert '{"float": "-inf"}' in json.dumps(bound_at(a_Art=-50.0, ψ_min=1.0).encoding())
