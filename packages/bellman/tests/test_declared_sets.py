"""The set that a declaration writes for a name: several sets in one type,
the set kept and printed for them, the sets that parameters of application
stage files keep, the sets refused where they are written,
perch words, empty intervals and differences, the sets that may hold an
infinity, the intersection of the sets of a field, and the observable set
of a policy block.

`test_declared_sets_at_calibration.py` holds the tests of the names that
the set of a parameter, a setting or a derived parameter may read, and of
the membership of a value in its set, which calibration and configuration
decide."""

import functools
import itertools
import math

import pytest
from application_files import COPIED_FILES_FOLDER, PERFECT_FORESIGHT_FILE, ROOT
from stage_builders import (
    construction_refusal,
    declared_set_of,
    stage_from_file,
    stage_from_text,
    two_nodes_stage_with_declared_sets,
    undecided_memberships,
)
from stage_texts import (
    BETA_AND_R_DECLARATIONS,
    TWO_NODES_ARRIVAL_K_DECLARATION,
    corpus_text,
    two_nodes_text_with_joint_normal_law,
    two_nodes_text_with_parameter_sets,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage.stage_answers import fields
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import may_hold_infinity, to_source
from bellman.syntax.terms import Comprehension

# the line that defines the named set Xn, which a declaration of the tests
# may read
DEFINITION_OF_XN = "Xn := [0, 9]\n"


def set_of_beta(declaration):
    """The declared set of β of the two-node stage whose declaration of β is
    `declaration`."""
    return stage_from_text(two_nodes_text_with_parameter_sets(declaration)).par["β"].domain


def kept_set(declaration):
    """The set that the reading of `declaration` keeps, read from the parsed
    line with no stage built, after the line that defines the named set
    Xn."""
    return declared_set_of(DEFINITION_OF_XN + declaration)


def base_and_conditions(declared):
    """The base and the conditions of a kept set, each as printed; a set
    with no condition is its own base."""
    if not isinstance(declared, Comprehension):
        return to_source(declared), []
    return to_source(declared.base), [to_source(condition) for condition in declared.conds]


# the readings of a stage in which a parameter, a setting and a derived
# parameter are declared in the set that each reading is given
READINGS = [
    pytest.param(
        lambda written: two_nodes_stage_with_declared_sets(f"β : {written}"), id="a-parameter"
    ),
    pytest.param(
        lambda written: two_nodes_stage_with_declared_sets("β : ℝ₊₊", f"tol : {written}\n"),
        id="a-setting",
    ),
    pytest.param(
        lambda written: two_nodes_stage_with_declared_sets(f"β : ℝ₊₊\nq : {written} := β*R"),
        id="a-derived-parameter",
    ),
]


def test_a_word_among_several_sets_is_read_as_one_type_with_them():
    """The shock z declared on `(-1, 1) @ !shck @ (-inf, R)` is a shock
    whose declared set is the interval (-1, 1) restricted by the bound R."""
    with_word = stage_from_text(TWO_NODES.replace("z : ℝ\n", "z : (-1, 1) @ !shck @ (-inf, R)\n"))
    assert to_source(fields(with_word)["two_nodes:shck:z"].domain) == "(-1, 1) @ (-1, R)"


def test_a_bound_written_after_a_comma_is_refused_with_its_reason_and_the_type_to_write():
    """The declaration `β : (0,1), < R` is refused under `syntax` at its line,
    with a reason that names the bound and the type that writes it as a
    second set."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : (0,1), < R"))
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    phrases = ("`β < R`", "after a comma", "retired")
    assert [phrase for phrase in phrases if phrase not in error.parts.why] == []
    assert error.write == "write `(0, 1) @ (0, R)`"


# declarations that write a bound after a comma, each with the type that
# its refusal advises and the base and the conditions of that type: the
# declaration's own sets and words and each bound, also over a base that may
# hold an infinity
ADVISED_TYPES = [
    pytest.param(
        "β : ℝ, >= 1, <= 10",
        "ℝ @ [1, 10]",
        "ℝ",
        ["β >= 1", "β <= 10"],
        id="two-bounds-on-the-reals",
    ),
    pytest.param(
        "β : ℝ̄, < 2", "ℝ̄ @ [-inf, 2)", "ℝ̄", ["β < 2"], id="an-upper-bound-on-the-extended-reals"
    ),
    pytest.param(
        "β : (0, inf], > R",
        "(0, inf] @ (R, inf]",
        "(0, inf]",
        ["β > R"],
        id="a-lower-bound-on-an-interval-closed-at-infinity",
    ),
    pytest.param(
        "β : (0,1) @ (0, 2*R), < R",
        "(0, 1) @ (0, 2*R) @ (0, R)",
        "(0, 1)",
        ["β < 2*R", "β < R"],
        id="a-bound-after-two-sets",
    ),
    pytest.param(
        "z : (-1, 1) @ !shck, < R",
        "(-1, 1) @ (-1, R) @ !shck",
        "(-1, 1)",
        ["z < R"],
        id="a-bound-after-a-set-and-a-word",
    ),
]


@pytest.mark.parametrize("comma_line, advised, base, conditions", ADVISED_TYPES)
def test_the_type_that_the_refusal_of_a_comma_advises_keeps_the_base_and_the_bounds(
    comma_line, advised, base, conditions
):
    """The refusal of a bound written after a comma advises a type whose
    reading keeps the base and the bounds of the refused line and nothing
    else."""
    with pytest.raises(ConstructionError) as refused:
        kept_set(comma_line)
    assert refused.value.write == f"write `{advised}`"
    name = comma_line.split(" : ")[0]
    assert base_and_conditions(kept_set(f"{name} : {advised}")) == (base, conditions)


def test_the_refusal_of_a_comma_writes_the_bound_on_a_name_with_its_perch_mark():
    """The refusal of `V[>] : ℝ, < 2` writes the bound on the name with its
    perch mark, `V[>] < 2`."""
    with pytest.raises(ConstructionError) as refused:
        kept_set("V[>] : ℝ, < 2")
    assert "`V[>] < 2`" in refused.value.message


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("β : (0,1),", id="a-comma-with-nothing-after-it"),
        pytest.param("β : (0,1) (0, R)", id="two-sets-with-no-sign-between-them"),
    ],
)
def test_a_declaration_that_the_parser_cannot_read_is_refused_with_no_word_of_a_comparison(text):
    """A declaration that the parser cannot read is refused under `syntax`
    with a reason that offers no comparison after a comma."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets(text))
    assert refused.value.rule == "syntax" and "comparison" not in refused.value.parts.why


# the law of motion of the block dcsn_to_cntn of the two-node stage
LAW_OF_MOTION = "a = k_d*(c*y + (1-c)*R) + z"


def test_a_comparison_after_a_comma_where_no_declaration_ends_is_refused_at_the_comparison():
    """A comparison written after a comma inside a call on a line of a
    block is refused under `syntax` at its column, with the forms that may
    follow the comma."""
    assert TWO_NODES.count(LAW_OF_MOTION) == 1
    text = TWO_NODES.replace(LAW_OF_MOTION, "a = max(k_d, < 2)")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text)
    error = refused.value
    rows = text.split("\n")
    line = next(number for number, row in enumerate(rows, start=1) if "max(k_d" in row)
    column = rows[line - 1].index("<") + 1
    assert (error.rule, error.line, error.column) == ("syntax", line, column)
    phrases = ("`< 2)`", "a name, a number")
    assert [phrase for phrase in phrases if phrase not in error.parts.why] == []


# declarations of β by several sets, each with the base and the conditions
# of the set kept and its printed text
SEVERAL_SETS_OF_BETA = [
    pytest.param(
        "β : (0,1) @ (0, R)",
        "(0, 1)",
        ["β < R"],
        "(0, 1) @ (0, R)",
        id="an-upper-bound-by-a-parameter",
    ),
    pytest.param(
        "β : (0,1) @ (-inf, R)",
        "(0, 1)",
        ["β < R"],
        "(0, 1) @ (0, R)",
        id="an-upper-bound-by-a-parameter-in-an-interval-from-minus-infinity",
    ),
    # on each side the base takes the number, wherever it stands
    pytest.param(
        "β : (0, R) @ (0,1)",
        "(0, 1)",
        ["β < R"],
        "(0, 1) @ (0, R)",
        id="the-interval-of-numbers-written-second",
    ),
    pytest.param(
        "β : (R, 1) @ (0, 2*R)",
        "(0, 1)",
        ["β > R", "β < 2*R"],
        "(0, 1) @ (R, 2*R)",
        id="a-number-and-a-formula-on-each-side",
    ),
    # of several numbers on one side the tightest, and it alone restricts
    pytest.param(
        "β : (0, 5) @ (-inf, 2)", "(0, 2)", [], "(0, 2)", id="the-tightest-number-on-each-side"
    ),
    pytest.param(
        "β : (0, R) @ (1, R)",
        "(1, R)",
        [],
        "(1, R)",
        id="a-tighter-lower-number-and-one-formula-twice",
    ),
    pytest.param(
        "β : ℝ @ (0, 5) @ (1, 2)",
        "ℝ",
        ["β > 1", "β < 2"],
        "ℝ @ (1, 2)",
        id="the-tightest-numbers-of-two-intervals-on-the-reals",
    ),
    # where no number bounds a side, the first formula in the order printed
    pytest.param(
        "β : (0, R) @ (0, 2*R)",
        "(0, 2*R)",
        ["β < R"],
        "(0, 2*R) @ (0, R)",
        id="two-formulas-on-the-upper-side",
    ),
    pytest.param(
        "β : ℝ₊₊ @ [R, inf)",
        "ℝ₊₊",
        ["β >= R"],
        "ℝ₊₊ @ [R, inf)",
        id="a-closed-lower-bound-on-the-positive-reals",
    ),
    pytest.param(
        "β : [R, inf) @ ℝ₊₊",
        "ℝ₊₊",
        ["β >= R"],
        "ℝ₊₊ @ [R, inf)",
        id="a-closed-lower-bound-written-before-the-positive-reals",
    ),
    pytest.param(
        "β : ℤ @ [1, inf)",
        "ℤ",
        ["β >= 1"],
        "ℤ @ [1, inf)",
        id="a-closed-lower-bound-on-the-integers",
    ),
    pytest.param(
        "β : (0,1) @ [R, 2*R]",
        "(0, 1)",
        ["β >= R", "β <= 2*R"],
        "(0, 1) @ [R, 2*R]",
        id="two-closed-bounds-by-formulas",
    ),
    # an endpoint written with both brackets is open, the stricter
    pytest.param(
        "β : [0,1] @ (0, R)",
        "(0, 1]",
        ["β < R"],
        "(0, 1] @ (0, R)",
        id="an-endpoint-closed-in-one-set-and-open-in-the-other",
    ),
    pytest.param(
        "β : [0,1] @ [0, R)",
        "[0, 1]",
        ["β < R"],
        "[0, 1] @ [0, R)",
        id="an-endpoint-closed-in-both-sets",
    ),
    # the lower bounds stand before the upper ones, however grouped
    pytest.param(
        "β : (0,1) @ (R/2, inf) @ (-inf, R)",
        "(0, 1)",
        ["β > R/2", "β < R"],
        "(0, 1) @ (R/2, R)",
        id="a-lower-and-an-upper-bound-in-two-intervals",
    ),
    pytest.param(
        "β : (0,1) @ (0, R) @ (0, R)",
        "(0, 1)",
        ["β < R"],
        "(0, 1) @ (0, R)",
        id="the-same-interval-twice",
    ),
    pytest.param(
        "β : ℝ @ (R, 5) @ (0, 2*R)",
        "ℝ",
        ["β > 0", "β > R", "β < 5", "β < 2*R"],
        "ℝ @ (0, 5) @ (R, 2*R)",
        id="numbers-and-formulas-on-both-sides-on-the-reals",
    ),
    # an open infinite endpoint bounds a base that may hold that infinity
    pytest.param(
        "β : ℝ̄ @ (-inf, inf)",
        "ℝ̄",
        ["β > -inf", "β < inf"],
        "ℝ̄ @ (-inf, inf)",
        id="open-infinite-endpoints-on-the-extended-reals",
    ),
    pytest.param(
        "β : ℝ̄ @ [-inf, inf)",
        "ℝ̄",
        ["β < inf"],
        "ℝ̄ @ [-inf, inf)",
        id="a-closed-and-an-open-infinite-endpoint-on-the-extended-reals",
    ),
    pytest.param(
        "β : ℝ̄ @ (0, inf)",
        "ℝ̄",
        ["β > 0", "β < inf"],
        "ℝ̄ @ (0, inf)",
        id="an-open-upper-infinity-on-the-extended-reals",
    ),
    pytest.param(
        "β : ℝ̄ @ (-inf, R) @ (0, 5)",
        "ℝ̄",
        ["β > 0", "β < 5", "β < R"],
        "ℝ̄ @ (0, 5) @ [-inf, R)",
        id="two-intervals-on-the-extended-reals",
    ),
    # among intervals the base itself excludes the infinity
    pytest.param(
        "β : (0, inf] @ (R, inf)",
        "(0, inf)",
        ["β > R"],
        "(0, inf) @ (R, inf)",
        id="an-interval-closed-at-infinity-and-an-open-one",
    ),
]


@pytest.fixture(scope="module")
def beta_sets():
    """`beta_sets(declaration)`: the declared set of β of the two-node stage
    whose declaration of β is `declaration`, elaborated once for each
    declaration."""
    return functools.cache(set_of_beta)


@pytest.mark.parametrize("declaration, base, conditions, printed", SEVERAL_SETS_OF_BETA)
def test_several_sets_of_one_type_are_kept_as_a_base_restricted_by_conditions(
    beta_sets, declaration, base, conditions, printed
):
    """The set kept for several sets in one type is one base restricted by
    the bounds of the other sets that the base does not already imply."""
    assert base_and_conditions(beta_sets(declaration)) == (base, conditions)


@pytest.mark.parametrize("declaration, base, conditions, printed", SEVERAL_SETS_OF_BETA)
def test_the_set_kept_for_several_sets_prints_as_its_base_and_the_intervals_of_its_conditions(
    beta_sets, declaration, base, conditions, printed
):
    """The set kept for several sets in one type prints as its base followed
    by the intervals that its conditions bound."""
    assert to_source(beta_sets(declaration)) == printed


@pytest.mark.parametrize("declaration, base, conditions, printed", SEVERAL_SETS_OF_BETA)
def test_the_printed_text_of_a_kept_set_is_read_back_as_that_set(
    beta_sets, declaration, base, conditions, printed
):
    """The printed text of the set kept for several sets, declared again in
    a stage of its own, is read as the same set."""
    kept = beta_sets(declaration)
    assert set_of_beta(f"β : {to_source(kept)}") == kept


@pytest.fixture(scope="module")
def perfect_foresight_application(read_only_stage_from_file):
    """The perfect-foresight stage of its file, which declares
    `β : ℝ₊₊ @ (0, R^(ρ-1))`."""
    return read_only_stage_from_file(PERFECT_FORESIGHT_FILE)


@pytest.fixture(scope="module")
def perfect_foresight_on_the_unit_interval():
    """The perfect-foresight stage of its file with its one declaration of β
    replaced by `β : (0,1) @ (0, R^(ρ-1))`, on the base (0, 1) in place of
    the base ℝ₊₊; a file with no such line, or with several, raises
    ValueError."""
    text = (ROOT / PERFECT_FORESIGHT_FILE).read_text(encoding="utf-8")
    (written,) = [row for row in text.split("\n") if row.startswith("β : ")]
    return stage_from_text(
        text.replace(written, "β : (0,1) @ (0, R^(ρ-1))"), PERFECT_FORESIGHT_FILE
    )


@pytest.mark.parametrize(
    "stage, name, base, conditions",
    [
        # the file writes the base ℝ₊₊, a set not written as an interval, so
        # each endpoint of the interval (0, R^(ρ-1)) is a condition
        pytest.param(
            "perfect_foresight_application",
            "β",
            "ℝ₊₊",
            ["β > 0", "β < R^(ρ - 1)"],
            id="beta-of-the-perfect-foresight-stage",
        ),
        pytest.param(
            "perfect_foresight_on_the_unit_interval",
            "β",
            "(0, 1)",
            ["β < R^(ρ - 1)"],
            id="beta-of-the-perfect-foresight-stage-declared-on-the-unit-interval",
        ),
        # the bound of η is weak, so that a calibration with η = γ lies in
        # the declared set
        pytest.param(
            "sa_savings", "η", "(1, inf)", ["η >= γ"], id="eta-of-the-smooth-ambiguity-stage"
        ),
    ],
)
def test_a_parameter_of_an_application_stage_keeps_the_base_and_conditions_of_its_declaration(
    request, stage, name, base, conditions
):
    """The declared set of a parameter of a stage of an application, as its
    file writes it or with its declaration replaced, is kept as its base
    restricted by the conditions that its other sets add."""
    declared = request.getfixturevalue(stage).par[name].domain
    assert to_source(declared.base) == base
    assert [to_source(condition) for condition in declared.conds] == conditions


# the pool of sets that the pairs below are made of: intervals with every
# pair of brackets and with numbers, formulas and infinities at both ends,
# and four sets that are no intervals
POOL_INTERVALS = [
    f"{left}{low}, {high}{right}"
    for low in ("-inf", "0", "1", "R")
    for high in ("1", "2", "R", "2*R", "inf")
    for left in "(["
    for right in ")]"
]


# the four sets of the pool that are no intervals, each with its endpoints
# written as an interval, or None for the named set Xn, whose endpoints the
# reading of a declaration does not know
POOL_OTHERS = {"ℝ": "(-inf, inf)", "ℝ₊₊": "(0, inf)", "ℝ̄": "[-inf, inf]", "Xn": None}


# the endpoints of the pool that are numbers, by their spelling; an
# endpoint that is a formula of R bounds nothing that the reading decides
POOL_NUMBERS = {"-inf": -math.inf, "0": 0.0, "1": 1.0, "2": 2.0, "inf": math.inf}


def pool_pairs():
    """Every pair of two different sets of the pool of which at least one
    is an interval, in the order of the pool."""
    return [
        (first, second)
        for first, second in itertools.combinations(POOL_INTERVALS + list(POOL_OTHERS), 2)
        if first in POOL_INTERVALS or second in POOL_INTERVALS
    ]


def share_a_number(first, second):
    """Whether the endpoints that are numbers of two sets of the pool leave
    a number in common: the greatest lower endpoint lies below the least
    upper endpoint, or equals it with both ends closed; of two equal
    endpoints the open one is the stricter."""
    lower, lower_open, upper, upper_open = -math.inf, False, math.inf, False
    for written in (first, second):
        interval = POOL_OTHERS.get(written, written)
        if interval is None:
            continue
        low, high = interval[1:-1].split(", ")
        opened_low, opened_high = interval[0] == "(", interval[-1] == ")"
        if low in POOL_NUMBERS and (POOL_NUMBERS[low], opened_low) > (lower, lower_open):
            lower, lower_open = POOL_NUMBERS[low], opened_low
        if high in POOL_NUMBERS and (-POOL_NUMBERS[high], opened_high) > (-upper, upper_open):
            upper, upper_open = POOL_NUMBERS[high], opened_high
    return lower < upper or (lower == upper and not lower_open and not upper_open)


@pytest.fixture(scope="module")
def pool_kept_sets():
    """The set kept for each pair of the pool whose endpoints share a
    number, written in the order of the pool, by the pair; the reading
    raises here any refusal of such a pair."""
    return {
        (first, second): kept_set(f"β : {first} @ {second}")
        for first, second in pool_pairs()
        if share_a_number(first, second)
    }


def test_two_sets_of_the_pool_that_share_a_number_keep_one_set_in_either_order(pool_kept_sets):
    """For each pair of the pool whose endpoints share a number, the two
    sets written in the reverse order keep the same set."""
    for (first, second), kept in pool_kept_sets.items():
        written = f"`{first} @ {second}`, kept as `{to_source(kept)}`"
        assert kept_set(f"β : {second} @ {first}") == kept, written


def test_the_set_kept_for_two_sets_of_the_pool_is_read_back_from_its_printed_text(
    pool_kept_sets,
):
    """For each pair of the pool whose endpoints share a number, the printed
    text of the set kept, declared again, keeps the same set."""
    for (first, second), kept in pool_kept_sets.items():
        written = f"`{first} @ {second}`, kept as `{to_source(kept)}`"
        assert kept_set(f"β : {to_source(kept)}") == kept, written


def test_a_third_interval_of_the_outer_endpoints_of_two_intervals_changes_no_kept_set(
    pool_kept_sets,
):
    """For each pair of intervals of the pool that share a number, a third
    interval from the lower endpoint of the first to the upper endpoint of
    the second keeps the same set."""
    intervals = {
        (first, second): kept
        for (first, second), kept in pool_kept_sets.items()
        if first in POOL_INTERVALS and second in POOL_INTERVALS
    }
    for (first, second), kept in intervals.items():
        written = f"`{first} @ {second}`, kept as `{to_source(kept)}`"
        low, high = first.split(", ")[0], second.split(", ")[1]
        regrouped = kept_set(f"β : {first} @ {second} @ {low}, {high}")
        assert regrouped == kept, written


def test_two_sets_of_the_pool_whose_endpoints_leave_no_number_are_refused_in_either_order():
    """Each pair of the pool whose endpoints that are numbers leave no
    number in common is refused as sets with no number in common, in the
    order of the pool and in the reverse order."""
    for first, second in pool_pairs():
        if share_a_number(first, second):
            continue
        with pytest.raises(ConstructionError) as refused:
            kept_set(f"β : {first} @ {second}")
        assert "no number in common" in refused.value.message, f"`{first} @ {second}`"
        with pytest.raises(ConstructionError, match="no number in common"):
            kept_set(f"β : {second} @ {first}")


# a declaration on a listed set that writes an infinity, as a subset of the
# extended reals, with an interval open at that infinity
LISTED_SET_WITH_AN_INFINITY = "β : {0, inf} ⊂ ℝ̄ @ (-1, inf)"


# declarations with an open infinite endpoint, each with the conditions of
# the set kept: the endpoint restricts a base that may hold the infinity
# and no other
OPEN_INFINITE_ENDPOINTS = [
    pytest.param(
        LISTED_SET_WITH_AN_INFINITY,
        ["β > -1", "β < inf"],
        id="a-listed-set-that-writes-an-infinity",
    ),
    pytest.param("β : {0, 1, 2} @ (-1, inf)", ["β > -1"], id="a-list-of-numbers"),
]


@pytest.mark.parametrize("declaration, conditions", OPEN_INFINITE_ENDPOINTS)
def test_an_open_infinite_endpoint_restricts_only_a_base_that_may_hold_that_infinity(
    declaration, conditions
):
    """An interval open at an infinity adds the condition that excludes it
    only where the base, as written, may hold that infinity."""
    assert base_and_conditions(kept_set(declaration))[1] == conditions


def test_a_listed_set_that_holds_an_infinity_is_read_back_from_its_printed_text():
    """The printed text of the set kept for `{0, inf} ⊂ ℝ̄ @ (-1, inf)`,
    declared again, keeps the same set."""
    listed = kept_set(LISTED_SET_WITH_AN_INFINITY)
    assert kept_set(f"β : {to_source(listed)}") == listed


# a declaration of the value V[>], a name with a perch mark, whose second
# set is bounded below by V, the same name at another perch
MARKED_NAME_ABOVE_V = "V[>] : ℝ @ (V, inf)"


def test_the_conditions_of_a_name_with_a_perch_mark_are_written_on_the_marked_name():
    """The conditions of `V[>] : ℝ @ (V, inf)` are written on `V[>]`, so
    that an endpoint may read the name at another perch."""
    assert base_and_conditions(kept_set(MARKED_NAME_ABOVE_V)) == ("ℝ", ["V[>] > V"])


def test_the_set_of_a_name_with_a_perch_mark_prints_its_bound_as_an_interval():
    """The set kept for `V[>] : ℝ @ (V, inf)` prints as `ℝ @ (V, inf)`."""
    assert to_source(kept_set(MARKED_NAME_ABOVE_V)) == "ℝ @ (V, inf)"


def test_an_endpoint_beyond_the_floating_point_numbers_is_compared_by_its_value():
    """The upper endpoint 1e400, which has no floating-point spelling, is
    compared by its value with the upper endpoint 5, which bounds the set."""
    assert to_source(kept_set("β : (0, 1e400) @ (0, 5)")) == "(0, 5)"


@pytest.mark.parametrize(
    "declaration, printed",
    [
        pytest.param("β : (0,1) @ (0,1)", "(0, 1)", id="the-same-interval-twice"),
        pytest.param("β : (0,1) @ (-inf, inf)", "(0, 1)", id="an-interval-and-the-real-line"),
        # of two intervals with number endpoints the open one is the base
        pytest.param(
            "β : (0, inf] @ (0, inf)",
            "(0, inf)",
            id="an-interval-closed-at-infinity-and-the-same-interval-open",
        ),
    ],
)
def test_several_sets_whose_intersection_is_one_of_them_print_as_that_set(declaration, printed):
    """Several sets whose intersection is one of them print as that one set,
    with no condition."""
    assert to_source(set_of_beta(declaration)) == printed


def test_an_open_interval_and_the_closed_interval_of_its_endpoints_keep_the_open_interval():
    """The set kept for `(0,1) @ [0,1]` is the set kept for `(0,1)`."""
    assert set_of_beta("β : (0,1) @ [0,1]") == set_of_beta("β : (0,1)")


def test_two_sets_of_one_type_that_are_no_intervals_are_refused_at_the_declaration():
    """The declaration `β : ℝ₊₊ @ ℤ` is refused under `syntax` at its line,
    with a reason that names the two sets and a type of one interval to
    write."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : ℝ₊₊ @ ℤ"))
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    phrases = ("`ℝ₊₊`", "`ℤ`", "are no intervals")
    assert [phrase for phrase in phrases if phrase not in error.parts.why] == []
    assert "`β : ℝ₊₊ @ (0, 1)`" in error.write


def test_a_set_of_labels_among_several_sets_is_refused_at_the_declaration():
    """The declaration `β : {a, b} @ (0, 1)` is refused under `syntax` at its
    line, with a reason that names the set of labels."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : {a, b} @ (0, 1)"))
    error = refused.value
    assert (error.rule, error.line, error.column) == ("syntax", 2, 1)
    phrases = ("`{a, b}`", "a set of labels")
    assert [phrase for phrase in phrases if phrase not in error.parts.why] == []


def test_several_sets_on_a_declaration_of_several_names_are_refused_at_the_declaration():
    """The declaration `(β, R) : ℝ₊₊ × ℝ₊₊ @ (0, 1)` is refused under
    `syntax` at its line, as a declaration of several names that carries
    several sets."""
    assert TWO_NODES.count(BETA_AND_R_DECLARATIONS) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            TWO_NODES.replace(BETA_AND_R_DECLARATIONS, "(β, R) : ℝ₊₊ × ℝ₊₊ @ (0, 1)\n")
        )
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, 1)
    phrases = ("of (β, R) carries", "declares more than one")
    assert [phrase for phrase in phrases if phrase not in error.parts.why] == []


def test_one_name_typed_inside_its_parentheses_is_refused_as_no_declaration_of_several_names():
    """The declaration `(β : (0,1)) : (0, R) @ (0, 2)` is refused under
    `syntax` at its line for the type inside the parentheses, with the
    advice to write the sets after one colon."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("(β : (0,1)) : (0, R) @ (0, 2)"))
    error = refused.value
    assert (error.rule, error.line, error.column) == ("syntax", 2, 1)
    assert "inside its parentheses" in error.parts.why and "more than one" not in error.parts.why
    assert "after one colon" in error.write


@pytest.mark.parametrize(
    "typed",
    [
        pytest.param("y : ℝ \\ {0}", id="a-difference"),
        pytest.param("y : ℝ₊", id="a-reserved-set"),
    ],
)
def test_a_law_whose_subject_types_a_shock_inside_its_parentheses_is_refused(typed):
    """A `~` line whose subject writes a set for the shock y inside its
    parentheses, a difference or any other set, is refused under `syntax`
    with the advice to write the type of each shock on a line of its own."""
    joint = two_nodes_text_with_joint_normal_law()
    assert joint.count("(y, z) ~") == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(joint.replace("(y, z) ~", f"({typed}, z) ~"))
    error = refused.value
    assert error.rule == "syntax"
    assert (
        "the distribution is declared for (y, z), and its subject types y inside the "
        "parentheses; a `~` line names its shocks"
    ) in error.message
    assert error.write == (
        "write the names alone, `(y, z) ~ …`, and the type of each shock on a line of its "
        "own, as in `y : ℝ`"
    )


def test_several_sets_on_a_name_listed_in_a_header_are_refused_at_the_block():
    """The listing `(k : ℝ @ [0, 1]) : !arvl` is refused under
    `readable-form` at the block arvl_to_dcsn, since several sets are read
    only at the top level."""
    assert TWO_NODES.count(TWO_NODES_ARRIVAL_K_DECLARATION) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            TWO_NODES.replace(TWO_NODES_ARRIVAL_K_DECLARATION, "(k : ℝ @ [0, 1]) : !arvl")
        )
    error = refused.value
    assert (error.rule, error.address) == ("readable-form", "arvl_to_dcsn")
    phrases = ("carries two sets", "at the top level")
    assert [phrase for phrase in phrases if phrase not in error.message] == []


@pytest.fixture(scope="module")
def two_nodes_with_one_perch_word_twice():
    """The two-node stage whose arrival field k is listed as
    `(k : ℝ @ !arvl @ !arvl) : !arvl`; the reading raises here any refusal
    of it."""
    return stage_from_text(
        TWO_NODES.replace(TWO_NODES_ARRIVAL_K_DECLARATION, "(k : ℝ @ !arvl @ !arvl) : !arvl")
    )


@pytest.mark.usefixtures("two_nodes_with_one_perch_word_twice")
@pytest.mark.parametrize(
    "words",
    [
        pytest.param("!arvl @ !dcsn", id="the-arrival-word-first"),
        pytest.param("!dcsn @ !arvl", id="the-decision-word-first"),
    ],
)
def test_two_different_perch_words_in_one_type_are_refused_and_one_word_twice_is_read(words):
    """A listing whose type carries two different perch words is refused
    under `field-perch` with both words named and no advice to replace the
    name, in either order, while one perch word written twice is read."""
    assert TWO_NODES.count(TWO_NODES_ARRIVAL_K_DECLARATION) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            TWO_NODES.replace(TWO_NODES_ARRIVAL_K_DECLARATION, f"(k : ℝ @ {words}) : !arvl")
        )
    assert refused.value.rule == "field-perch"
    phrases = ("`!arvl`", "`!dcsn`")
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert "in place of `k`" not in (refused.value.write or "")


def test_a_top_level_declaration_that_carries_two_perch_words_is_refused():
    """The top-level declaration `β : ℝ₊₊ @ !arvl @ !dcsn` is refused under
    `field-perch`, with a reason that says that β carries two perch
    words."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : ℝ₊₊ @ !arvl @ !dcsn"))
    assert refused.value.rule == "field-perch"
    assert "β at the top level carries two perch words" in refused.value.message


def test_a_perch_word_that_disagrees_with_its_header_is_refused_with_the_advice_to_remove_it():
    """The listing `(k : ℝ @ !dcsn) : !arvl` is refused under `field-perch`
    at the block, with a reason that calls `!dcsn` a perch word and the
    advice to remove it."""
    assert TWO_NODES.count(TWO_NODES_ARRIVAL_K_DECLARATION) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            TWO_NODES.replace(TWO_NODES_ARRIVAL_K_DECLARATION, "(k : ℝ @ !dcsn) : !arvl")
        )
    error = refused.value
    assert (error.rule, error.address) == ("field-perch", "arvl_to_dcsn")
    assert "the perch word `!dcsn` on k" in error.message and "the mark" not in error.message
    assert error.write == "Remove `!dcsn` from the listing of k in block 'arvl_to_dcsn'"


@pytest.fixture(scope="module")
def two_closed_intervals_that_meet_at_one_endpoint():
    """The printed text of the set kept for `β : [0,1] @ [1, 2]`."""
    return to_source(declared_set_of("β : [0,1] @ [1, 2]"))


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("β : (0,1) @ (2,3)", id="intervals-apart"),
        pytest.param("β : (0,1) @ [1, 2]", id="intervals-that-meet-at-an-open-end"),
    ],
)
def test_two_intervals_of_numbers_are_refused_only_where_they_share_no_number(
    two_closed_intervals_that_meet_at_one_endpoint, declaration
):
    """Two intervals of numbers with no number in common are refused under
    `syntax`, while two closed intervals that meet at one endpoint keep that
    number."""
    assert two_closed_intervals_that_meet_at_one_endpoint == "[1, 1]"
    with pytest.raises(ConstructionError) as refused:
        declared_set_of(declaration)
    assert refused.value.rule == "syntax" and "no number in common" in refused.value.message


# several sets whose endpoints written as ratios of two integers leave no
# number, each with the sets and the two endpoints as the refusal quotes
# them, as the file writes them
NO_NUMBER_IN_COMMON = [
    pytest.param(
        "(0,1) @ (1/2, 1/3)",
        "`(0, 1)` and `(1/2, 1/3)`",
        "above 1/2 and below 1/3",
        id="two-sets",
    ),
    pytest.param(
        "(0,1) @ (1/2, 1) @ (0, 1/3)",
        "`(0, 1)`, `(1/2, 1)` and `(0, 1/3)`",
        "above 1/2 and below 1/3",
        id="three-sets",
    ),
    pytest.param(
        "ℝ₊₊ @ [1/2, 1/2)",
        "`ℝ₊₊` and `[1/2, 1/2)`",
        "at least 1/2 and below 1/2",
        id="an-interval-of-one-number-open-at-one-end",
    ),
    # of two spellings of one endpoint, the open one bounds the sets
    pytest.param(
        "[0, 0.5] @ (1/4, 1/2) @ [1/2, 1]",
        "`[0, 0.5]`, `(1/4, 1/2)` and `[1/2, 1]`",
        "at least 1/2 and below 1/2",
        id="a-decimal-and-a-ratio-of-one-upper-endpoint",
    ),
    pytest.param(
        "[0.5, 1] @ (1/2, 3/4) @ [0, 1/2]",
        "`[0.5, 1]`, `(1/2, 3/4)` and `[0, 1/2]`",
        "above 1/2 and at most 1/2",
        id="a-decimal-and-a-ratio-of-one-lower-endpoint",
    ),
]


@pytest.fixture(scope="module")
def printed_ratio_sets_that_leave_a_number():
    """The printed texts of the sets kept for three declarations, in this
    order: ratios that leave a number, `β : (0,1) @ (1/4, 1/2)`; an endpoint
    that reads a parameter, `β : (0,1) @ (1/2, R)`; and a decimal and a
    ratio of one value, which are one number that the two sets have in
    common, `β : [0.1, 1] @ [0, 1/10]`."""
    declarations = ("β : (0,1) @ (1/4, 1/2)", "β : (0,1) @ (1/2, R)", "β : [0.1, 1] @ [0, 1/10]")
    return tuple(to_source(declared_set_of(declaration)) for declaration in declarations)


@pytest.mark.parametrize("written, carried, between", NO_NUMBER_IN_COMMON)
def test_sets_with_ratio_endpoints_are_refused_only_where_they_leave_no_number_quoting_them(
    printed_ratio_sets_that_leave_a_number, written, carried, between
):
    """Several sets whose endpoints written as ratios leave no number are
    refused under `syntax`, quoting the sets and the two endpoints, while
    ratios that leave a number, an endpoint that reads a parameter, and a
    decimal and a ratio of one value are read."""
    assert printed_ratio_sets_that_leave_a_number == (
        "(0, 1) @ (1/4, 1/2)",
        "(0, 1) @ (1/2, R)",
        "[0.1, 1] @ [0.1, 1/10]",
    )
    with pytest.raises(ConstructionError) as refused:
        declared_set_of(f"β : {written}")
    assert refused.value.rule == "syntax"
    assert (
        f"the declaration of β carries the sets {carried}, which have no number in common: "
        f"no number is {between}; "
    ) in refused.value.message


@pytest.mark.parametrize(
    "declaration, printed",
    [
        pytest.param("β : ℝ₊₊ @ ℝ₊₊", "ℝ₊₊", id="two-equal-sets"),
        pytest.param(
            "β : ℝ₊₊ @ (0, R) @ ℝ₊₊", "ℝ₊₊ @ (0, R)", id="two-equal-sets-around-an-interval"
        ),
    ],
)
def test_two_equal_sets_in_one_type_are_one_set(declaration, printed):
    """Two equal sets in the type of one name are kept as one set."""
    assert to_source(declared_set_of(declaration)) == printed


def test_a_declaration_of_several_names_reads_equal_sets_as_one_and_refuses_different_sets():
    """The declaration `(a, b) : ℝ₊₊ @ ℝ₊₊` keeps the one set ℝ₊₊, while
    `(a, b) : ℝ₊₊ @ (0,1)` is refused as declaring more than one set."""
    assert to_source(declared_set_of("(a, b) : ℝ₊₊ @ ℝ₊₊")) == "ℝ₊₊"
    with pytest.raises(ConstructionError, match="declares more than one"):
        declared_set_of("(a, b) : ℝ₊₊ @ (0,1)")


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("β : (0, n)", id="in-an-interval"),
        pytest.param("β : ℝ₊₊ @ (0, n)", id="in-a-second-set-of-the-type"),
        pytest.param("β : (0, E_{y}(n*y^2))", id="under-an-expectation"),
    ],
)
def test_a_declared_set_that_reads_an_undeclared_name_is_refused_where_it_is_written(declaration):
    """A declared set that reads the undeclared name n is refused under
    `name-in-scope` at the declaration, with the names in scope to write."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets(declaration))
    error = refused.value
    assert (error.rule, error.address) == ("name-in-scope", "2")
    assert "reads the name 'n', which the stage does not declare" in error.message
    assert error.write.startswith("Write one of the names in scope here: Γ, β, R, y, z")


# declarations of a name W that the block cntn_to_dcsn writes, each with the
# methods text that declares W where it is a setting, and the phrases of
# the refusal of that line
WRITTEN_NAMES = [
    # a name declared at the top level that no header lists is a parameter
    pytest.param(
        "β : ℝ₊₊\nW : ℝ",
        None,
        ("writes W", "a parameter is written by no line"),
        id="a-parameter",
    ),
    pytest.param(
        "β : ℝ₊₊\nW : ℝ₊₊ := β*R",
        None,
        ("a derived parameter is written by no line",),
        id="a-derived-parameter-with-a-declared-set",
    ),
    pytest.param(
        "β : ℝ₊₊\nW := β*R",
        None,
        ("a derived parameter is written by no line",),
        id="a-derived-parameter",
    ),
    pytest.param("β : ℝ₊₊", "W : ℝ\n", ("a setting is written by no line",), id="a-setting"),
]


@pytest.mark.parametrize("declarations, addition, phrases", WRITTEN_NAMES)
def test_a_line_of_a_block_that_writes_a_parameter_a_derived_parameter_or_a_setting_is_refused(
    declarations, addition, phrases
):
    """The line of the block cntn_to_dcsn that writes W is refused under
    `parameter-or-field` where W is a parameter, a derived parameter or a
    setting."""
    with pytest.raises(ConstructionError) as refused:
        two_nodes_stage_with_declared_sets(declarations, addition)
    error = refused.value
    assert (error.rule, error.address) == ("parameter-or-field", "cntn_to_dcsn.1")
    assert [phrase for phrase in phrases if phrase not in error.message] == []


# the reason of the refusal of an interval whose lower endpoint lies above
# its upper one, and of one whose endpoints are equal and one end open, with
# the two endpoints in its two places
ABOVE = "has the lower endpoint {} above the upper endpoint {}, so it is empty; "


EQUAL = (
    "has the lower endpoint {} equal to the upper endpoint {} and an open end, so it is empty; "
)


# intervals of numbers that hold no number, each with the reason of its
# refusal
EMPTY_INTERVALS = [
    pytest.param("(2, 1)", ABOVE.format(2, 1), id="open-with-the-lower-endpoint-above"),
    pytest.param("[2, 1]", ABOVE.format(2, 1), id="closed-with-the-lower-endpoint-above"),
    pytest.param(
        "(1/2, 1/3)", ABOVE.format("1/2", "1/3"), id="ratios-with-the-lower-endpoint-above"
    ),
    pytest.param("(1, -inf)", ABOVE.format(1, "-inf"), id="an-upper-endpoint-at-minus-infinity"),
    pytest.param("(1, 1)", EQUAL.format(1, 1), id="equal-endpoints-open-at-both-ends"),
    pytest.param("[1, 1)", EQUAL.format(1, 1), id="equal-endpoints-open-at-the-upper-end"),
    pytest.param("(1, 1]", EQUAL.format(1, 1), id="equal-endpoints-open-at-the-lower-end"),
]


@pytest.fixture(scope="module")
def intervals_of_one_number():
    """The two-node stage in which β and the derived parameter q are
    declared on intervals of one number closed at both ends, calibrated at
    those numbers; the reading, the calibration and the configuration of a
    setting declared on such an interval raise any refusal here."""
    copy_native(two_nodes_stage_with_declared_sets("β : ℝ₊₊", "tol : [1, 1]\n")).configure(
        {"tol": 1.0}
    )
    one = stage_from_text(two_nodes_text_with_parameter_sets("β : [1, 1]\nq : [2, 2] := β*R"))
    return copy_native(one).calibrate({"β": 1.0, "R": 2.0})


@pytest.mark.parametrize("read", READINGS)
@pytest.mark.parametrize("interval, fault", EMPTY_INTERVALS)
def test_an_interval_of_numbers_that_holds_no_number_is_refused_and_one_of_one_number_is_read(
    intervals_of_one_number, read, interval, fault
):
    """An interval that holds no number is refused under `readable-form` in
    the set of a parameter, a setting or a derived parameter, with its
    reason and the advice to write the smaller endpoint first, while
    intervals of one number closed at both ends are read and calibrated."""
    assert undecided_memberships(intervals_of_one_number) == []
    error = construction_refusal(lambda: read(interval))
    assert error.rule == "readable-form"
    assert f"the set {interval} {fault}" in error.message
    assert "an interval of numbers holds at least one number" in error.message
    assert error.write.startswith("Write the smaller endpoint first")


@pytest.mark.parametrize(
    "closed",
    [
        pytest.param("[0.1, 1/10]", id="the-decimal-first"),
        pytest.param("[1/10, 0.1]", id="the-ratio-first"),
    ],
)
def test_a_decimal_and_a_ratio_that_write_one_number_are_one_endpoint_of_an_interval(closed):
    """An interval between 0.1 and 1/10 holds that number where both ends
    are closed, and is refused as empty where one end is open."""
    assert (
        stage_from_text(two_nodes_text_with_parameter_sets(f"β : {closed}")).par["β"].domain
        is not None
    )
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets("β : (0.1, 1/10]"))
    )
    assert error.rule == "readable-form"
    assert "the set (0.1, 1/10] " + EQUAL.format("0.1", "1/10") in error.message


def test_a_field_listed_on_a_header_with_an_empty_interval_is_refused():
    """The listing `(k : (2, 1)) : !arvl` is refused under `readable-form`
    as an empty interval."""
    assert TWO_NODES.count(TWO_NODES_ARRIVAL_K_DECLARATION) == 1
    error = construction_refusal(
        lambda: stage_from_text(
            TWO_NODES.replace(TWO_NODES_ARRIVAL_K_DECLARATION, "(k : (2, 1)) : !arvl")
        )
    )
    assert error.rule == "readable-form" and "so it is empty" in error.message


# the top-level declaration of the shock y of the two-node stage
SHOCK_Y = "y : ℝ\n"


def test_a_field_declared_at_the_top_level_with_an_empty_interval_is_refused_at_its_line():
    """The top-level declaration `y : (2, 1)` of a shock is refused under
    `readable-form` at its own line, as an interval whose lower endpoint
    lies above its upper one."""
    assert TWO_NODES.count(SHOCK_Y) == 1
    error = construction_refusal(
        lambda: stage_from_text(TWO_NODES.replace(SHOCK_Y, "y : (2, 1)\n"))
    )
    assert (error.rule, error.address, error.line) == ("readable-form", "4", 4)
    assert "the set (2, 1) has the lower endpoint 2 above the upper endpoint 1" in error.message


# differences whose left side lies within their right side, each with the
# reason of its refusal
EMPTY_DIFFERENCES = [
    pytest.param(
        "ℝ \\ ℝ",
        "the set ℝ \\ ℝ has the left side ℝ within the right side ℝ",
        id="a-set-less-itself",
    ),
    pytest.param(
        "(0,1) \\ ℝ₊",
        "the set (0, 1) \\ ℝ₊ has the left side (0, 1) within the right side ℝ₊",
        id="an-interval-less-a-set-that-holds-it",
    ),
    pytest.param(
        "{1} \\ {1}",
        "the set {1} \\ {1} has the left side {1} within the right side {1}",
        id="a-listed-set-less-itself",
    ),
]


# differences that the rules of inclusion do not decide to be empty, and
# one that is a member of a union, since another member of the union may
# hold a number
READABLE_DIFFERENCES = ("ℝ₊ \\ {1}", "(0, R) \\ (0, 1)", "(0,1) \\ ℝ₊ \\/ (2, 3)")


@pytest.fixture(scope="module")
def stages_with_readable_differences():
    """The two-node stages whose β is declared on each of
    `READABLE_DIFFERENCES`; the reading raises here any refusal of one of
    them."""
    return [
        stage_from_text(two_nodes_text_with_parameter_sets(f"β : {declared}"))
        for declared in READABLE_DIFFERENCES
    ]


@pytest.mark.usefixtures("stages_with_readable_differences")
@pytest.mark.parametrize("read", READINGS)
@pytest.mark.parametrize("difference, fault", EMPTY_DIFFERENCES)
def test_a_difference_is_refused_as_empty_only_where_its_left_side_lies_within_its_right(
    read, difference, fault
):
    """A difference whose left side lies within its right side is refused
    under `readable-form` in the set of a parameter, a setting or a derived
    parameter, while differences that the rules of inclusion do not decide
    to be empty are read."""
    error = construction_refusal(lambda: read(difference))
    assert error.rule == "readable-form"
    assert error.message == (
        f"{fault}, so it is empty; a difference holds at least one number, so its left "
        "side holds a number that its right side does not hold"
    )
    assert error.write == ("Write a left side that holds a number outside the right side")


def test_an_empty_difference_of_a_named_set_is_refused_at_the_declaration():
    """The declaration `β : Xb \\ ℝ₊`, whose named set Xb is [0, 1), is
    refused under `readable-form` at its own line, with Xb read as the set
    that the stage defines."""
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets("Xb := [0, 1)\nβ : Xb \\ ℝ₊"))
    )
    assert (error.rule, error.address, error.line) == ("readable-form", "3", 3)
    assert "the set Xb \\ ℝ₊ has the left side Xb within the right side ℝ₊" in error.message


# sets of one declaration, each with whether its form may hold inf and
# whether it may hold -inf: an interval closed at that side whose endpoint
# is the infinity or the bare name of a parameter, an extended real set
# that holds the infinity, a union with such a member, a difference with
# such a left side, and a set with conditions on such a base, none of whose
# conditions excludes the infinity; an interval open at that side, or
# closed at a number or at a formula that computes, holds none
INFINITY_BY_FORM = [
    pytest.param("(0, inf]", True, False, id="an-interval-closed-at-inf"),
    pytest.param("(0, inf)", False, False, id="an-interval-open-at-inf"),
    pytest.param("[-inf, 0)", False, True, id="an-interval-closed-at-minus-inf"),
    pytest.param("(0, T]", True, False, id="an-interval-closed-at-a-name-above"),
    pytest.param("[T, 5)", False, True, id="an-interval-closed-at-a-name-below"),
    pytest.param("(0, T)", False, False, id="an-interval-open-at-a-name"),
    pytest.param("(0, 5]", False, False, id="an-interval-closed-at-a-number"),
    pytest.param("(0, 2*T]", False, False, id="an-interval-closed-at-a-formula"),
    pytest.param("(0, -T]", False, False, id="an-interval-closed-at-a-negated-name"),
    pytest.param("ℝ", False, False, id="the-reals"),
    pytest.param("ℝ_{+∞}", True, False, id="the-reals-with-inf"),
    pytest.param("ℝ_{-∞}", False, True, id="the-reals-with-minus-inf"),
    pytest.param("ℝ̄", True, True, id="the-extended-reals"),
    pytest.param("{1, …, 5}", False, False, id="a-range-of-integers"),
    pytest.param("(0, 1) \\/ [2, T]", True, False, id="a-union-with-a-member-closed-at-a-name"),
    pytest.param("(0, 1) \\/ (2, 3)", False, False, id="a-union-of-bounded-intervals"),
    pytest.param("ℝ̄ \\ {0}", True, True, id="a-difference-from-the-extended-reals"),
    pytest.param("ℝ \\ {0}", False, False, id="a-difference-from-the-reals"),
    pytest.param("ℝ̄ @ (0, 5)", False, False, id="the-extended-reals-bounded-by-numbers"),
    pytest.param("ℝ̄ @ (0, inf)", False, False, id="the-extended-reals-open-at-inf"),
    pytest.param("ℝ̄ @ (0, inf]", True, False, id="the-extended-reals-closed-at-inf"),
    pytest.param("ℝ̄ @ [-inf, 5)", False, True, id="the-extended-reals-closed-at-minus-inf"),
    pytest.param("ℝ̄ @ (0, 5]", False, False, id="the-extended-reals-closed-at-a-number"),
    pytest.param(
        "ℝ̄ @ [-5, inf]", True, False, id="the-extended-reals-from-a-number-closed-at-inf"
    ),
    pytest.param("ℝ̄ @ (0, T)", False, False, id="the-extended-reals-open-at-a-name"),
    pytest.param("ℝ̄ @ (0, T]", True, False, id="the-extended-reals-closed-at-a-name-above"),
    pytest.param("ℝ̄ @ [T, 5)", False, True, id="the-extended-reals-closed-at-a-name-below"),
    pytest.param("ℝ_{+∞} @ (0, 100]", False, False, id="the-reals-with-inf-closed-at-a-number"),
    pytest.param("ℝ₊₊ @ (0, R)", False, False, id="the-positive-reals-open-at-a-name"),
    pytest.param("(0, 1) @ (0, R)", False, False, id="an-interval-open-at-a-name-above"),
]


@pytest.mark.parametrize("written, above, below", INFINITY_BY_FORM)
def test_the_form_of_a_declared_set_shows_which_infinities_it_may_hold(written, above, below):
    """`may_hold_infinity` answers, from the form of the declared set
    `written`, whether the set may hold inf and whether it may hold -inf."""
    held = declared_set_of(f"β : {written}")
    assert may_hold_infinity(held, negative=False) is above
    assert may_hold_infinity(held, negative=True) is below


# named sets written with a bar, each with whether it may hold inf and
# whether it may hold -inf: a condition excludes inf where it bounds the
# name strictly from above, `x < e` with any `e`, or by a number, `x <= 5`,
# and -inf in mirror image, also where it writes the name on its right
# side; a condition that bounds the name by another name, `x >= T`,
# excludes neither
INFINITY_BY_CONDITIONS = [
    pytest.param("{x : ℝ̄ | x < 100}", False, True, id="a-strict-upper-bound"),
    pytest.param(
        "{x : ℝ̄ | 100 > x}", False, True, id="a-strict-upper-bound-with-the-name-on-the-right"
    ),
    pytest.param(
        "{x : ℝ̄ | 0 <= x}", True, False, id="a-lower-bound-by-a-number-with-the-name-on-the-right"
    ),
    pytest.param("{x : ℝ̄ | x >= T}", True, True, id="a-lower-bound-by-a-name"),
]


@pytest.mark.parametrize("written, above, below", INFINITY_BY_CONDITIONS)
def test_the_conditions_of_a_named_set_with_a_bar_show_which_infinities_it_may_hold(
    written, above, below
):
    """`may_hold_infinity` answers, from the conditions of the named set
    with a bar `written`, whether the set may hold inf and whether it may
    hold -inf."""
    term, _ = parse_with_spans(f"H := {written}\n", "t.bl")
    held = term.items[-1].core.value.set
    assert isinstance(held, Comprehension)
    assert may_hold_infinity(held, negative=False) is above
    assert may_hold_infinity(held, negative=True) is below


def field_sets(text):
    """The declared set of each field of the stage `text`, as printed, or
    None for a field with no declared set, by the field's identity."""
    return {
        identity: None if sort.domain is None else to_source(sort.domain)
        for identity, sort in fields(stage_from_text(text)).items()
    }


# a stage whose arrival fields x, y and z are listed with a set on the
# headers of two blocks; `R++` is the plain spelling of ℝ₊₊, and the named
# set Xa, which the stage defines by a set with a bar, is a form that the
# rules of the intersection do not decide
THREE_FIELDS_LISTED_TWICE = (
    "@stage: t\n"
    "Xa := {q : ℝ | q >= 1}\n"
    "[id=b, (x : ℝ, y : [0, 2), z : Xa) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
    "[id=d, (x : R++, y : (1, 3], z : Xa) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n"
)


# a stage whose arrival field x is listed on the interval [-inf, inf) and
# on the reals
ONE_FIELD_ON_THE_EXTENDED_AND_THE_REAL_LINE = (
    "@stage: t\n"
    "[id=b, (x : [-inf, inf)) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
    "[id=d, (x : ℝ) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n"
)


# a stage whose arrival field x is listed on the named set Xa and on ℝ₊, a
# pair that the rules of the intersection do not intersect
ONE_FIELD_ON_TWO_SETS_NOT_INTERSECTED = (
    "@stage: t\n"
    "Xa := {q : ℝ | q >= 1}\n"
    "[id=b, (x : Xa) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
    "[id=d, (x : ℝ₊) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n"
)


@pytest.mark.parametrize(
    "text, identities, sets",
    [
        pytest.param(
            THREE_FIELDS_LISTED_TWICE,
            ("t:arvl:x", "t:arvl:y", "t:arvl:z"),
            ("ℝ₊₊", "(1, 2)", "Xa"),
            id="three-fields-listed-twice",
        ),
        pytest.param(
            ONE_FIELD_ON_THE_EXTENDED_AND_THE_REAL_LINE,
            ("t:arvl:x",),
            ("ℝ",),
            id="an-interval-of-the-extended-reals-and-the-reals",
        ),
    ],
)
def test_a_field_carries_the_intersection_of_the_sets_of_its_listings(text, identities, sets):
    """The declared set of a field listed on several headers is the
    intersection of the sets of its listings."""
    found = field_sets(text)
    assert tuple(found[identity] for identity in identities) == sets


def test_a_field_whose_sets_the_rules_do_not_intersect_carries_no_set():
    """A field listed on the named set Xa and on ℝ₊, a pair that the rules
    of the intersection do not intersect, carries no declared set."""
    assert field_sets(ONE_FIELD_ON_TWO_SETS_NOT_INTERSECTED)["t:arvl:x"] is None


# a stage file of the corpus whose decision field r, the return, is
# declared on ℝ₊₊ @ [ρ, inf) with the parameter ρ
GENERATION = f"{COPIED_FILES_FOLDER}/benhabib-bisin-zhu-2011/generation.bl"


def test_a_field_may_be_declared_on_a_set_bounded_by_a_parameter():
    """The field r of the corpus stage `generation` is read with the
    declared set ℝ₊₊ @ [ρ, inf), whose lower bound is the parameter ρ."""
    stage = stage_from_file(GENERATION)
    assert to_source(fields(stage)["generation:dcsn:r"].domain) == "ℝ₊₊ @ [ρ, inf)"


def test_the_observable_set_of_the_policy_block_holds_a_bound_that_names_a_parameter():
    """The card of the policy builder of the consumption stage whose
    multiplier μ[>] bounds the saving a below by −θ writes the observable
    set with the condition a ≥ −θ and the product of μ with the slack of
    that condition."""
    text = (
        corpus_text("cons_obs")
        .replace("Xa := ℝ₊", "Xa := ℝ\nθ : ℝ₊")
        .replace("μ[>]   : ℝ₊ ⟂ a >= 0", "μ[>]   : ℝ₊ ⟂ a >= -θ")
    )
    card = str(stage_from_text(text, "cons_obs.bl").builder.policy)
    # the card writes the name of the set Xa in roman type, the coordinates
    # a and μ with no perch mark, listed as a set with a bar lists them, and
    # the slack of a ≥ −θ as a − (−θ)
    assert "A≻,policy = {a, μ ∈ Xa × ℝ₊ | a ≥ −θ ∧ μ · (a − (−θ)) = 0}" in card
