"""The acceptance file of AMD-GRAM-004, several sets in one type: one test for
each of its acceptance items that the snapshot does not carry, named
`test_item_<n>_<claim>`, each reading the public parameter record
`stage.par[name]`, the source printer and the binding verbs.

1. A declaration reads several sets with `@` between them, and a bound
   written after a comma is no spelling of the language: the lowering refuses
   it with the sets to write, and the parser's refusals are those of the
   language alone.
2. The sets are kept as one set, the base restricted by the bounds of the
   intervals, whatever the order they are written in and however their
   endpoints are grouped into intervals, and the source printer writes it
   back as sets with `@` between them, which are read as the same term.
3. The refusals: two sets that are no intervals, a set that no interval
   restricts, a declaration of more than one name with several sets, a name
   typed inside its parentheses, and a field on a side of a block header with
   two sets.
4. Calibration decides the membership of a value in a set with conditions,
   the several sets of a type and a named set written with a bar, and refuses
   a faulty value at its own parameter, in whatever order the file declares
   the parameters.
5. The stage files that wrote a bound after a comma hold the sets they held,
   and every recorded calibration of them binds. The Epstein–Zin stage file
   has since stated its restriction on a derived parameter, whose value
   calibration computes; the test reads the bound the file held from its
   text with the declaration of β replaced, and binds the file itself at
   its recorded calibrations with no open requirement. The perfect-foresight
   stage file has since declared its discount factor on ℝ₊₊ with the same
   bound; the test reads the set the file held in the same way, and the set
   the file holds now.

Item 6, the views, is carried by the snapshot: the view of a stage prints a
declared set as a declaration writes it.
"""

import itertools
import math

import pytest
from conftest import (
    CORPUS,
    CORPUS_CALIBRATIONS,
    PERFECT_FORESIGHT_CALIBRATION,
    ROOT,
    SA_SAVINGS_CALIBRATIONS,
    SECOND_CALIBRATIONS,
    corpus_text,
    fresh_stage,
    methodized,
    stage_from_text,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source
from bellman.syntax.terms import Comprehension, Domain

PERFECT_FORESIGHT_FOLDER = (
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight"
)
MEMBERSHIP = "calibration-domain-membership"
# the declaration of the discount factor that the Epstein–Zin stage file held
# until 11 November 2026; its bound reads an expectation, which no
# calibration decides
EZ_BOUNDED_DISCOUNT_FACTOR = "β : (0,1) @ (0, E_{Ψ}(Ψ^(1-γ))^((ρ-1)/(1-γ)))"
# the declaration of the discount factor that the perfect-foresight stage
# file held until 11 November 2026; the file now writes the same bound on
# the base ℝ₊₊
PF_BOUNDED_DISCOUNT_FACTOR = "β : (0,1) @ (0, R^(ρ-1))"


def _perfect_foresight_with_the_set_it_held():
    """The perfect-foresight stage of the committed text, the declaration of
    β replaced by `PF_BOUNDED_DISCOUNT_FACTOR`."""
    path = f"{PERFECT_FORESIGHT_FOLDER}/perfect_foresight.bl"
    text = (ROOT / path).read_text(encoding="utf-8")
    (written,) = [row for row in text.split("\n") if row.startswith("β : ")]
    return stage_from_text(text.replace(written, PF_BOUNDED_DISCOUNT_FACTOR), path)


def _ez_savings_with_the_bound_it_held():
    """The Epstein–Zin stage of the committed text, the declaration of β
    replaced by `EZ_BOUNDED_DISCOUNT_FACTOR`."""
    text = corpus_text("ez_savings")
    (written,) = [row for row in text.split("\n") if row.startswith("β : ")]
    return stage_from_text(
        text.replace(written, EZ_BOUNDED_DISCOUNT_FACTOR), CORPUS["ez_savings"]
    )


def _two_nodes(declaration):
    """The two-node stage, the declaration of β replaced by `declaration`."""
    written = "β : ℝ₊₊\n"
    assert TWO_NODES.count(written) == 1
    return TWO_NODES.replace(written, declaration + "\n")


def _declared(declaration):
    """The set the two-node stage holds for β under `declaration`."""
    return stage_from_text(_two_nodes(declaration)).par["β"].domain


def _lowered(declaration):
    """The set the lowering keeps for the one declaration, read from the
    parsed line with no stage built; `Xn` is a set the text defines."""
    term, _ = parse_with_spans(f"Xn := [0, 9]\n{declaration}\n", "t.bl")
    (domain,) = [c for c in term.items[-1].declaration.classifiers if isinstance(c, Domain)]
    return domain.space


def _base_and_conditions(declared):
    """The base and the conditions of a kept set, each as printed; a set
    with no condition is its own base."""
    if not isinstance(declared, Comprehension):
        return to_source(declared), []
    return to_source(declared.base), [to_source(condition) for condition in declared.conds]


def _open_memberships(stage):
    """The memberships of parameter values that a calibrated stage leaves
    undecided, each as its explanation."""
    return [
        item.explanation
        for item in stage.obligations()
        if item.condition == MEMBERSHIP and item.status == "required"
    ]


def test_item_1_a_declaration_reads_several_sets_and_a_bound_after_a_comma_is_no_spelling():
    assert to_source(_declared("β : (0,1) @ (0, R)")) == "(0, 1) @ (0, R)"
    # a word and several sets, in any order, are one type
    with_word = stage_from_text(
        _two_nodes("β : (0,1) @ (0, R)").replace("z : ℝ\n", "z : (-1, 1) @ !shck @ (-inf, R)\n")
    )
    assert to_source(with_word.par["β"].domain) == "(0, 1) @ (0, R)"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : (0,1), < R"))
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    assert all(word in error.parts.why for word in ("`β < R`", "after a comma", "retired"))
    assert error.write == "write `(0, 1) @ (0, R)`"
    # the type the refusal gives declares the set the retired line declared:
    # the declaration's own sets and words, and each bound and nothing else,
    # also over a base that may hold an infinity
    advised = {
        "β : ℝ, >= 1, <= 10": ("ℝ @ [1, 10]", "ℝ", ["β >= 1", "β <= 10"]),
        "β : ℝ̄, < 2": ("ℝ̄ @ [-inf, 2)", "ℝ̄", ["β < 2"]),
        "β : (0, inf], > R": ("(0, inf] @ (R, inf]", "(0, inf]", ["β > R"]),
        "β : (0,1) @ (0, 2*R), < R": (
            "(0, 1) @ (0, 2*R) @ (0, R)",
            "(0, 1)",
            ["β < 2*R", "β < R"],
        ),
    }
    for retired, (written, base, conditions) in advised.items():
        with pytest.raises(ConstructionError) as refused:
            _lowered(retired)
        assert refused.value.write == f"write `{written}`", retired
        assert _base_and_conditions(_lowered(f"β : {written}")) == (base, conditions), retired
    with pytest.raises(ConstructionError) as refused:
        _lowered("z : (-1, 1) @ !shck, < R")
    assert refused.value.write == "write `(-1, 1) @ (-1, R) @ !shck`"
    # a name with a perch mark is written with its mark
    with pytest.raises(ConstructionError) as refused:
        _lowered("V[>] : ℝ, < 2")
    assert "`V[>] < 2`" in refused.value.message
    # a text the parser cannot read is refused by the language alone, which
    # offers no comparison after a comma
    for text in ("β : (0,1),", "β : (0,1) (0, R)"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes(text))
        assert refused.value.rule == "syntax" and "comparison" not in refused.value.parts.why
    # and a comma before a comparison where no declaration ends is refused at
    # the comparison, with the forms that may follow the comma
    law = "a = k_d*(c*y + (1-c)*R) + z"
    assert TWO_NODES.count(law) == 1
    text = TWO_NODES.replace(law, "a = max(k_d, < 2)")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text)
    error = refused.value
    rows = text.split("\n")
    line = next(number for number, row in enumerate(rows, start=1) if "max(k_d" in row)
    column = rows[line - 1].index("<") + 1
    assert (error.rule, error.line, error.column) == ("syntax", line, column)
    assert "`< 2)`" in error.parts.why and "a name, a number" in error.parts.why


@pytest.mark.parametrize(
    "declaration, base, conditions, printed",
    [
        ("β : (0,1) @ (0, R)", "(0, 1)", ["β < R"], "(0, 1) @ (0, R)"),
        ("β : (0,1) @ (-inf, R)", "(0, 1)", ["β < R"], "(0, 1) @ (0, R)"),
        # on each side the base takes the number, wherever it stands
        ("β : (0, R) @ (0,1)", "(0, 1)", ["β < R"], "(0, 1) @ (0, R)"),
        ("β : (R, 1) @ (0, 2*R)", "(0, 1)", ["β > R", "β < 2*R"], "(0, 1) @ (R, 2*R)"),
        # of several numbers on one side the tightest, and it alone restricts
        ("β : (0, 5) @ (-inf, 2)", "(0, 2)", [], "(0, 2)"),
        ("β : (0, R) @ (1, R)", "(1, R)", [], "(1, R)"),
        ("β : ℝ @ (0, 5) @ (1, 2)", "ℝ", ["β > 1", "β < 2"], "ℝ @ (1, 2)"),
        # where no number bounds a side, the first formula in the order printed
        ("β : (0, R) @ (0, 2*R)", "(0, 2*R)", ["β < R"], "(0, 2*R) @ (0, R)"),
        ("β : ℝ₊₊ @ [R, inf)", "ℝ₊₊", ["β >= R"], "ℝ₊₊ @ [R, inf)"),
        ("β : [R, inf) @ ℝ₊₊", "ℝ₊₊", ["β >= R"], "ℝ₊₊ @ [R, inf)"),
        ("β : ℤ @ [1, inf)", "ℤ", ["β >= 1"], "ℤ @ [1, inf)"),
        ("β : (0,1) @ [R, 2*R]", "(0, 1)", ["β >= R", "β <= 2*R"], "(0, 1) @ [R, 2*R]"),
        # an endpoint written with both brackets is open, the stricter
        ("β : [0,1] @ (0, R)", "(0, 1]", ["β < R"], "(0, 1] @ (0, R)"),
        ("β : [0,1] @ [0, R)", "[0, 1]", ["β < R"], "[0, 1] @ [0, R)"),
        # the lower bounds stand before the upper ones, however grouped
        (
            "β : (0,1) @ (R/2, inf) @ (-inf, R)",
            "(0, 1)",
            ["β > R/2", "β < R"],
            "(0, 1) @ (R/2, R)",
        ),
        ("β : (0,1) @ (0, R) @ (0, R)", "(0, 1)", ["β < R"], "(0, 1) @ (0, R)"),
        (
            "β : ℝ @ (R, 5) @ (0, 2*R)",
            "ℝ",
            ["β > 0", "β > R", "β < 5", "β < 2*R"],
            "ℝ @ (0, 5) @ (R, 2*R)",
        ),
        # an open infinite endpoint bounds a base that may hold that infinity
        ("β : ℝ̄ @ (-inf, inf)", "ℝ̄", ["β > -inf", "β < inf"], "ℝ̄ @ (-inf, inf)"),
        ("β : ℝ̄ @ [-inf, inf)", "ℝ̄", ["β < inf"], "ℝ̄ @ [-inf, inf)"),
        ("β : ℝ̄ @ (0, inf)", "ℝ̄", ["β > 0", "β < inf"], "ℝ̄ @ (0, inf)"),
        ("β : ℝ̄ @ (-inf, R) @ (0, 5)", "ℝ̄", ["β > 0", "β < 5", "β < R"], "ℝ̄ @ (0, 5) @ [-inf, R)"),
        # among intervals the base itself excludes the infinity
        ("β : (0, inf] @ (R, inf)", "(0, inf)", ["β > R"], "(0, inf) @ (R, inf)"),
    ],
)
def test_item_2_the_sets_are_one_set_the_base_restricted_by_the_bounds_of_the_intervals(
    declaration, base, conditions, printed
):
    declared = _declared(declaration)
    assert _base_and_conditions(declared) == (base, conditions)
    assert to_source(declared) == printed
    # the printed set is read back as the set it prints
    assert _declared(f"β : {printed}") == declared


def test_item_2_the_kept_set_is_one_in_any_order_and_is_read_back_from_its_printed_text():
    """Every pair of sets from a pool an author would write: every bracket,
    numbers, formulas and infinities at both ends, and four sets that are no
    intervals."""
    lower, upper = ("-inf", "0", "1", "R"), ("1", "2", "R", "2*R", "inf")
    intervals = [
        f"{left}{low}, {high}{right}"
        for low in lower
        for high in upper
        for left in "(["
        for right in ")]"
    ]
    others = ["ℝ", "ℝ₊₊", "ℝ̄", "Xn"]
    for first, second in itertools.combinations(intervals + others, 2):
        if first in others and second in others:
            continue
        try:
            kept = _lowered(f"β : {first} @ {second}")
        except ConstructionError as refused:
            # two sets whose numbers leave no number in common are refused,
            # in either order (AMD-GRAM-005)
            assert "no number in common" in refused.message, f"`{first} @ {second}`"
            with pytest.raises(ConstructionError, match="no number in common"):
                _lowered(f"β : {second} @ {first}")
            continue
        written = f"`{first} @ {second}`, kept as `{to_source(kept)}`"
        assert _lowered(f"β : {second} @ {first}") == kept, written
        assert _lowered(f"β : {to_source(kept)}") == kept, written
        # a third interval's endpoints are read with the others, whatever
        # intervals hold them
        if first in intervals and second in intervals:
            low, high = first.split(", ")[0], second.split(", ")[1]
            regrouped = _lowered(f"β : {first} @ {second} @ {low}, {high}")
            assert regrouped == kept, written


def test_item_2_a_base_whose_members_are_not_known_may_hold_an_infinity():
    # a listed set that writes an infinity may hold it, so the open endpoint
    # restricts it; a list of numbers holds none
    listed = _lowered("β : {0, inf} ⊂ ℝ̄ @ (-1, inf)")
    assert _base_and_conditions(listed)[1] == ["β > -1", "β < inf"]
    assert _lowered(f"β : {to_source(listed)}") == listed
    assert _base_and_conditions(_lowered("β : {0, 1, 2} @ (-1, inf)"))[1] == ["β > -1"]
    # the conditions of a name with a perch mark are written on the name
    # with its mark, so that an endpoint may read the name at another perch
    marked = _lowered("V[>] : ℝ @ (V, inf)")
    assert _base_and_conditions(marked) == ("ℝ", ["V[>] > V"])
    assert to_source(marked) == "ℝ @ (V, inf)"
    # the numbers of a side are compared by value and none is printed, so a
    # number that has no spelling is ordered with the others
    assert to_source(_lowered("β : (0, 1e400) @ (0, 5)")) == "(0, 5)"


def test_item_2_sets_that_restrict_nothing_leave_the_base_as_it_is_written():
    assert to_source(_declared("β : (0,1) @ (0,1)")) == "(0, 1)"
    assert to_source(_declared("β : (0,1) @ (-inf, inf)")) == "(0, 1)"
    assert _declared("β : (0,1) @ [0,1]") == _declared("β : (0,1)")
    # of two intervals with number endpoints the open one is the base
    assert to_source(_declared("β : (0, inf] @ (0, inf)")) == "(0, inf)"


def test_item_3_the_sets_no_rule_reads_as_one_are_refused_where_they_are_written():
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : ℝ₊₊ @ ℤ"))
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    assert all(word in error.parts.why for word in ("`ℝ₊₊`", "`ℤ`", "are no intervals"))
    assert "`β : ℝ₊₊ @ (0, 1)`" in error.write

    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : {a, b} @ (0, 1)"))
    error = refused.value
    assert (error.rule, error.line, error.column) == ("syntax", 2, 1)
    assert all(word in error.parts.why for word in ("`{a, b}`", "a set of labels"))

    both = "β : ℝ₊₊\nR : ℝ₊₊\n"
    assert TWO_NODES.count(both) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(both, "(β, R) : ℝ₊₊ × ℝ₊₊ @ (0, 1)\n"))
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    assert all(word in error.parts.why for word in ("of (β, R) carries", "declares more than one"))
    # one name typed inside its parentheses is no declaration of several names
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("(β : (0,1)) : (0, R) @ (0, 2)"))
    error = refused.value
    assert (error.rule, error.line, error.column) == ("syntax", 2, 1)
    assert "inside its parentheses" in error.parts.why and "more than one" not in error.parts.why
    assert "after one colon" in error.write

    side = "(k : ℝ) : !arvl"
    assert TWO_NODES.count(side) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(side, "(k : ℝ @ [0, 1]) : !arvl"))
    error = refused.value
    assert (error.rule, error.address) == ("readable-form", "arvl_to_dcsn")
    assert all(word in error.message for word in ("carries two sets", "at the top level"))


def test_item_4_calibration_decides_the_membership_of_a_value_in_a_set_with_conditions():
    stage_file = f"{PERFECT_FORESIGHT_FOLDER}/perfect_foresight.bl"
    impatient = {"β": 0.99, "ρ": 2.0, "R": 0.9, "Γ": 0.85}
    for additions in ((), ("methods.egm.bl",), ("methods.bl",)):
        bound = methodized(
            fresh_stage(stage_file),
            *(ROOT / PERFECT_FORESIGHT_FOLDER / name for name in additions),
        )
        # the return impatience condition fails: q = (βR)^(1/ρ)/R is 1.05
        with pytest.raises(ValueError) as refused:
            copy_native(bound).calibrate(impatient)
        words = ("parameter 'β'", "0.99", "ℝ₊₊ @ (0, R^(ρ - 1))", "β < R^(ρ - 1)", "R = 0.9")
        assert all(word in str(refused.value) for word in words), str(refused.value)
        # a value outside the base of the two sets is refused by the base
        with pytest.raises(ValueError, match=r"outside the declared set ℝ₊₊"):
            copy_native(bound).calibrate({**PERFECT_FORESIGHT_CALIBRATION, "β": -0.5})
        # a return factor below one at which the condition holds: q = 0.97
        for values in (PERFECT_FORESIGHT_CALIBRATION, {**impatient, "β": 0.85}):
            assert _open_memberships(copy_native(bound).calibrate(values)) == []
        # a faulty return factor is refused at the return factor, not at the
        # bound of the discount factor that reads it
        for faulty in (-1.04, 0.0, math.inf):
            with pytest.raises(ValueError) as refused:
                copy_native(bound).calibrate({**PERFECT_FORESIGHT_CALIBRATION, "R": faulty})
            assert "parameter 'R'" in str(refused.value) and "ℝ₊₊" in str(refused.value)

    # a value that breaks its own set is refused at its own parameter in
    # whichever order the two lines stand: the bound of β reads R, which
    # breaks a bound of its own set, and the base of β reads a faulty R
    both = "β : ℝ₊₊\nR : ℝ₊₊\n"
    assert TWO_NODES.count(both) == 1
    faulty = (
        (("β : (0,1) @ (0, R/2)", "R : ℝ₊₊ @ (1, 2)"), {"β": 0.4, "R": 0.5}, "R > 1"),
        (("β : (0, R) @ (0, 2*R)", "R : ℝ₊₊"), {"β": 0.5, "R": -1.04}, "ℝ₊₊"),
    )
    for lines, values, word in faulty:
        for ordered in (lines, lines[::-1]):
            stage = stage_from_text(TWO_NODES.replace(both, "\n".join(ordered) + "\n"))
            with pytest.raises(ValueError) as refused:
                copy_native(stage).calibrate(values)
            assert "parameter 'R'" in str(refused.value) and word in str(refused.value), ordered
    # the same where the membership of a parameter that is read is never
    # decided: R is outside its set, whose endpoint S lies on the extended
    # reals, and the bound of β reads R
    three = ("β : (0,1) @ (0, R)", "R : (0, S)", "S : ℝ̄")
    for ordered in (three, (three[1], three[0], three[2]), three[::-1]):
        stage = stage_from_text(TWO_NODES.replace(both, "\n".join(ordered) + "\n"))
        with pytest.raises(ValueError, match="parameter 'R'"):
            copy_native(stage).calibrate({"β": 0.5, "R": -1.0, "S": 2.0})
    # of two values that are each outside their own sets, the first of the
    # file is named, wherever a parameter that one of them reads is declared
    three = ("β : (0,1) @ (0, R)", "R : ℝ₊₊", "S : (0,1)")
    for ordered in (three, (three[1], three[0], three[2])):
        stage = stage_from_text(TWO_NODES.replace(both, "\n".join(ordered) + "\n"))
        with pytest.raises(ValueError, match="parameter 'β'"):
            copy_native(stage).calibrate({"β": 0.9, "R": 0.5, "S": 7.0})
    # two bounds that read each other are judged in the order of the file
    stage = stage_from_text(
        TWO_NODES.replace(both, "β : (0,1) @ (0, R)\nR : ℝ₊₊ @ (-inf, β)\n")
    )
    with pytest.raises(ValueError, match="parameter 'β'"):
        copy_native(stage).calibrate({"β": 0.5, "R": 0.5})

    # a setting is judged in the same way, at the calibration bound
    plain = stage_from_text(TWO_NODES)
    bounded = copy_native(methodized(plain, "tol : (0, 1) @ (0, R)\n")).calibrate(
        {"β": 0.5, "R": 0.9}
    )
    copy_native(bounded).configure({"tol": 0.5})
    with pytest.raises(ConstructionError) as refused:
        copy_native(bounded).configure({"tol": 0.95})
    assert refused.value.rule == "setting-outside-set"
    assert "the condition tol < R of the declared set at R = 0.9" in refused.value.message
    lines = ("a_min : ℝ₊ @ (1, 2)", "a_max : ℝ₊ @ (a_min, inf)")
    for ordered in (lines, lines[::-1]):
        with pytest.raises(ConstructionError) as refused:
            copy_native(methodized(plain, "\n".join(ordered) + "\n")).configure(
                {"a_min": 5.0, "a_max": 3.0}
            )
        assert "setting 'a_min'" in refused.value.message, ordered

    # a named set written with a bar is decided as the several sets are
    named = _two_nodes("Xb := {x : (0,1) | x < R, x > R/4}\nβ : Xb")
    stage = stage_from_text(named)
    assert _open_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    outside = ((0.95, ("x < R", "R = 0.9")), (0.2, ("x > R/4", "R = 0.9")), (1.5, ("(0, 1)",)))
    for value, words in outside:
        with pytest.raises(ValueError) as refused:
            copy_native(stage).calibrate({"β": value, "R": 0.9})
        assert all(word in str(refused.value) for word in ("parameter 'β'", repr(value), *words))
    # an equality is a condition of such a set
    equal = stage_from_text(_two_nodes("Xe := {x : ℝ | x = R}\nβ : Xe"))
    assert _open_memberships(copy_native(equal).calibrate({"β": 0.9, "R": 0.9})) == []
    with pytest.raises(ValueError, match="the condition x = R"):
        copy_native(equal).calibrate({"β": 0.8, "R": 0.9})

    # an open infinite endpoint is a bound that calibration decides
    extended = stage_from_text(_two_nodes("Xn := [0, 9]\nβ : Xn @ [1, inf)"))
    assert [to_source(c) for c in extended.par["β"].domain.conds] == ["β >= 1", "β < inf"]
    assert _open_memberships(copy_native(extended).calibrate({"β": 2.0, "R": 0.9})) == []
    with pytest.raises(ValueError, match="the condition β >= 1"):
        copy_native(extended).calibrate({"β": 0.5, "R": 0.9})
    # the infinite point, which the open endpoint excludes, is refused
    whole = stage_from_text(_two_nodes("β : ℝ̄ @ (-inf, inf)"))
    for point, condition in ((math.inf, "β < inf"), (-math.inf, "β > -inf")):
        with pytest.raises(ValueError, match=f"the condition {condition}"):
            copy_native(whole).calibrate({"β": point, "R": 0.9})

    # a bound that reads a field is not decided, and its base still is
    undecided = stage_from_text(_two_nodes("β : (0,1) @ (0, E_{y}(y^2))"))
    assert len(_open_memberships(copy_native(undecided).calibrate({"β": 0.5, "R": 1.02}))) == 1
    with pytest.raises(ValueError, match=r"outside the declared set \(0, 1\)"):
        copy_native(undecided).calibrate({"β": 1.5, "R": 1.02})


def test_item_5_the_rewritten_stage_files_hold_the_sets_they_held(ez_savings, sa_savings):
    perfect_foresight = fresh_stage(f"{PERFECT_FORESIGHT_FOLDER}/perfect_foresight.bl")
    # the corpus stage that bounds the return r, a field, below by ρ is read
    fresh_stage("packages/bellman/tests/corpus/benhabib-bisin-zhu-2011/generation.bl")
    bounded = _ez_savings_with_the_bound_it_held()
    held = {
        "β of the perfect-foresight stage, as its file declared it": (
            _perfect_foresight_with_the_set_it_held().par["β"].domain,
            "(0, 1)",
            ["β < R^(ρ - 1)"],
        ),
        # the file now writes the base ℝ₊₊, a set not written as an interval,
        # so each endpoint of the interval (0, R^(ρ-1)) is a condition
        "β of the perfect-foresight stage": (
            perfect_foresight.par["β"].domain,
            "ℝ₊₊",
            ["β > 0", "β < R^(ρ - 1)"],
        ),
        "β of the Epstein–Zin stage, as its file bounded it": (
            bounded.par["β"].domain,
            "(0, 1)",
            ["β < E_{Ψ}(Ψ^(1 - γ))^((ρ - 1)/(1 - γ))"],
        ),
        # the bound of η is weak, so that the calibration η = γ of the stage's
        # checks lies in the declared set
        "η of the smooth-ambiguity stage": (sa_savings.par["η"].domain, "(1, inf)", ["η >= γ"]),
    }
    for name, (declared, base, conditions) in held.items():
        assert to_source(declared.base) == base, name
        assert [to_source(condition) for condition in declared.conds] == conditions, name
    for values in SA_SAVINGS_CALIBRATIONS:
        assert _open_memberships(copy_native(sa_savings).calibrate(values)) == []
    # the bound the Epstein–Zin discount factor held reads an expectation, so
    # its membership stays the one open requirement of the calibration, while
    # its base is decided
    values = CORPUS_CALIBRATIONS["ez_savings"]
    assert len(_open_memberships(copy_native(bounded).calibrate(values))) == 1
    with pytest.raises(ValueError, match=r"parameter 'β' .*outside the declared set \(0, 1\)"):
        copy_native(bounded).calibrate({**values, "β": 1.5})
    # the stage file states the same restriction on the derived parameter q,
    # whose value calibration computes: each recorded calibration binds with
    # no open requirement, and a discount factor that violates the
    # restriction is refused at q
    for recorded, q in (
        (CORPUS_CALIBRATIONS["ez_savings"], 0.9896430095876418),
        (SECOND_CALIBRATIONS["ez_savings"], 0.9844751256509318),
    ):
        calibrated = copy_native(ez_savings).calibrate(recorded)
        assert calibrated.par["q"].value == pytest.approx(q)
        assert _open_memberships(calibrated) == []
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        copy_native(ez_savings).calibrate({**values, "β": 0.99})
