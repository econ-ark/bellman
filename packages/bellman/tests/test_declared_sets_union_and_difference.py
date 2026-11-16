"""A union `A \\/ B` and a difference `A \\ B` of sets of numbers in a
declared set: how the lowering reads and prints them, where a stage file may
write them, the conditions that a stage records for them, how calibration
and configuration decide a value's membership, and what the functions of
`bellman.typing.sets` answer for them.

The lowering is the step that turns a parsed declaration into the term of
its set, and `to_source` prints a term as the normalized text of a stage
file. The two-node stage is the small stage `TWO_NODES` of
`bellman.refusal_examples`, with the parameters β and R, the shocks y and z,
the four blocks that join its perches and its policy block; most tests
change one of its lines."""

import functools
import re

import pytest
from stage_builders import declared_set_of, methodized_copy, stage_from_text, undecided_memberships
from stage_texts import (
    BETA_AND_R_DECLARATIONS,
    TWO_NODES_ARRIVAL_K_DECLARATION,
    changed,
    two_nodes_text_with_changes,
    two_nodes_text_with_parameter_sets,
)

# `copy_native` copies a stage: a binding verb such as `calibrate` binds the
# stage that it is called on, so each test binds a copy of a shared stage
from bellman.native.hypergraphs import copy_native
from bellman.native.predicates import Member
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage import to_source
from bellman.stage.calibration_requirements import predicate_value
from bellman.syntax.terms import (
    Comprehension,
    Functions,
    Named,
    Number,
    Product,
    SetDifference,
    SetUnion,
)
from bellman.typing import sets

# the line of the two-node stage that declares β
BETA = "β : ℝ₊₊\n"


def declared_set(written):
    """The term that the lowering keeps for the declaration `β : written`,
    read from the parsed line with no stage built."""
    return declared_set_of(f"β : {written}")


def explanations_of(stage, condition):
    """The explanations of the conditions of the name `condition` that
    `stage.obligations()` answers."""
    return [item.explanation for item in stage.obligations() if item.condition == condition]


def statuses_of(stage, condition):
    """The status of each condition of the name `condition` that
    `stage.obligations()` answers."""
    return [item.status for item in stage.obligations() if item.condition == condition]


def text_dividing_by_beta(declared):
    """The two-node stage text with β declared in `declared`, whose law of
    motion divides by β and whose value line applies 𝑓(x : ℝ₊₊) to β."""
    text = two_nodes_text_with_changes(transition="    a = k_d/β + z\n")
    text = changed(text, (BETA, f"β : {declared}\n𝑓(x : ℝ₊₊) := x^2\n"))
    return changed(text, ("    W = β*V[>]\n", "    W = 𝑓(β)*V[>]\n"))


def text_reading_delta_at_j(declared, declarations=""):
    """The two-node stage text whose law of motion reads the collection δ on
    {1, …, 5} at the key j, a parameter declared in `declared` after the
    lines `declarations`."""
    text = two_nodes_text_with_changes(transition="    a = k_d*δ[j] + z\n")
    return changed(text, (BETA, f"{BETA}{declarations}δ : {{1, …, 5}} → ℝ\nj : {declared}\n"))


@pytest.fixture(scope="module")
def stage_with_beta_in():
    """`stage_with_beta_in(declared)`: the two-node stage with β declared in
    `declared`, elaborated once for each set."""

    @functools.cache
    def stage(declared):
        return stage_from_text(two_nodes_text_with_parameter_sets(f"β : {declared}"))

    return stage


@pytest.fixture(scope="module")
def stage_dividing_by_beta():
    """`stage_dividing_by_beta(declared)`: the stage of
    `text_dividing_by_beta(declared)`, elaborated once for each set."""

    @functools.cache
    def stage(declared):
        return stage_from_text(text_dividing_by_beta(declared))

    return stage


@pytest.fixture(scope="module")
def stage_reading_delta_at_j():
    """`stage_reading_delta_at_j(declared, declarations)`: the stage of
    `text_reading_delta_at_j`, elaborated once for each pair."""

    @functools.cache
    def stage(declared, declarations=""):
        return stage_from_text(text_reading_delta_at_j(declared, declarations))

    return stage


@pytest.fixture(scope="module")
def derived_parameter_in_a_union():
    """The two-node stage with the derived parameter q = β*R declared in
    `(0,1) \\/ (2, 3)`."""
    return stage_from_text(
        changed(
            TWO_NODES,
            (BETA_AND_R_DECLARATIONS, BETA_AND_R_DECLARATIONS + "q : (0,1) \\/ (2, 3) := β*R\n"),
        )
    )


@pytest.fixture(scope="module")
def setting_in_a_union():
    """The two-node stage methodized by an addition that declares the
    setting tol in `(0, 1) \\/ (2, 3)`."""
    return methodized_copy(stage_from_text(TWO_NODES), "tol : (0, 1) \\/ (2, 3)\n")


@pytest.fixture(scope="module")
def text_of_the_two_node_stage():
    """The text of the two-node stage."""
    return TWO_NODES


# The reading and the printed text of a union and a difference


@pytest.mark.parametrize(
    ("written", "kind", "printed"),
    [
        pytest.param("(0,1) \\/ (1, inf)", SetUnion, "(0, 1) \\/ (1, inf)", id="a-union"),
        pytest.param("ℝ₊₊ \\ {1}", SetDifference, "ℝ₊₊ \\ {1}", id="a-difference"),
        pytest.param(
            "ℝ \\ {0} \\/ {5}", SetUnion, "ℝ \\ {0} \\/ {5}", id="a-difference-then-a-union"
        ),
        pytest.param(
            "(2,3) \\/ (0,1) \\ {5}",
            SetDifference,
            "(0, 1) \\/ (2, 3) \\ {5}",
            id="a-union-then-a-difference",
        ),
    ],
)
def test_a_set_expression_is_lowered_to_the_term_of_its_last_sign_printed_in_its_kept_order(
    written, kind, printed
):
    """A set expression is lowered to the union or the difference of the
    sign written last, a term that `to_source` prints with the members of a
    union in the order that the lowering keeps."""
    term = declared_set(written)
    assert isinstance(term, kind)
    assert to_source(term) == printed


@pytest.mark.parametrize(
    ("written", "first_operand", "operand_written"),
    [
        pytest.param(
            "ℝ \\ {0} \\/ {5}",
            lambda union: union.members[0],
            "ℝ \\ {0}",
            id="a-difference-is-the-first-member-of-a-union",
        ),
        pytest.param(
            "(2,3) \\/ (0,1) \\ {5}",
            lambda difference: difference.left,
            "(0,1) \\/ (2,3)",
            id="a-union-is-the-left-side-of-a-difference",
        ),
    ],
)
def test_two_signs_of_a_set_expression_are_read_from_left_to_right(
    written, first_operand, operand_written
):
    """The set expression written before the second sign is lowered to the
    first operand of that sign."""
    assert first_operand(declared_set(written)) == declared_set(operand_written)


@pytest.mark.parametrize(
    ("written", "same"),
    [
        pytest.param("(0,1) ∪ (1, inf)", "(0,1) \\/ (1, inf)", id="the-sign-∪"),
        pytest.param(
            "(1, inf) \\/ (0,1)", "(0,1) \\/ (1, inf)", id="the-members-in-the-other-order"
        ),
        pytest.param(
            "(0,1) \\/ (1, inf) \\/ (0,1)", "(0,1) \\/ (1, inf)", id="a-member-written-twice"
        ),
        pytest.param(
            "(0, 2.0) \\/ (0, 2*R)", "(0, 2) \\/ (0, 2*R)", id="the-number-2-written-2.0"
        ),
        pytest.param("ℝ₊₊ ∖ {1}", "ℝ₊₊ \\ {1}", id="the-sign-∖"),
    ],
)
def test_two_spellings_of_one_union_or_difference_are_lowered_to_one_term(written, same):
    """A second spelling of a sign, another order of the members, a member
    written twice and another spelling of a number change nothing in the
    term that the lowering keeps."""
    assert declared_set(written) == declared_set(same)


@pytest.mark.parametrize(
    ("written", "printed"),
    [
        pytest.param("(0,1) \\/ (0,1)", "(0, 1)", id="one-interval-written-twice"),
        pytest.param("(0, 2) \\/ (0, 2.0)", "(0, 2)", id="one-number-spelled-two-ways"),
    ],
)
def test_a_union_of_two_equal_members_is_printed_as_the_one_member(written, printed):
    """A union whose two members are equal, also where an endpoint is
    spelled `2` in one and `2.0` in the other, is printed as the one
    member."""
    assert to_source(declared_set(written)) == printed


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("(0,1) \\/ (1, inf)", id="a-union"),
        pytest.param("ℝ₊₊ \\ {1}", id="a-difference"),
        pytest.param("ℝ \\ {0} \\/ {5}", id="a-difference-then-a-union"),
        pytest.param("(2,3) \\/ (0,1) \\ {5}", id="a-union-then-a-difference"),
        pytest.param("(0,1) \\/ (1, inf) @ (0, R)", id="a-union-bounded-by-an-interval"),
        pytest.param("(0,1) \\/ (1, inf) @ (0, inf)", id="a-union-of-open-members-below-inf"),
        pytest.param("(0,1) \\/ [1, inf] @ (0, inf)", id="a-union-with-a-member-closed-at-inf"),
        pytest.param("ℝ \\ {0} @ (0, inf)", id="a-difference-from-the-reals-below-inf"),
        pytest.param("ℝ̄ \\ {0} @ (0, inf)", id="a-difference-from-the-extended-reals-below-inf"),
    ],
)
def test_the_printed_text_of_a_union_or_a_difference_is_lowered_to_the_same_term(written):
    """The text that `to_source` prints for a union or a difference,
    declared again, is lowered to the term that it was printed from."""
    term = declared_set(written)
    assert declared_set(to_source(term)) == term


@pytest.mark.parametrize(
    ("unwritten", "words"),
    [
        pytest.param(
            lambda: Product((declared_set("(0,1) \\/ (1, inf)"), Named("ℝ"))),
            "no spelling as a factor",
            id="a-union-as-a-factor-of-a-product",
        ),
        pytest.param(
            lambda: Product((declared_set("ℝ₊₊ \\ {1}"), Named("ℝ"))),
            "no spelling as a factor",
            id="a-difference-as-a-factor-of-a-product",
        ),
        pytest.param(
            lambda: SetDifference(Named("ℝ"), declared_set("(0,1) \\/ (1, inf)")),
            "a later operand",
            id="a-union-as-the-right-side-of-a-difference",
        ),
        pytest.param(
            lambda: SetUnion((Named("ℝ"), declared_set("ℝ₊₊ \\ {1}"))),
            "a later operand",
            id="a-difference-as-the-second-member-of-a-union",
        ),
        pytest.param(
            lambda: SetDifference(Functions(Named("ℤ"), Named("ℝ")), Named("ℝ")),
            "spelling as an operand",
            id="a-set-of-functions-as-an-operand",
        ),
        pytest.param(
            lambda: SetUnion((Named("ℝ"),)),
            "fewer than two members",
            id="a-union-of-one-member",
        ),
        pytest.param(
            lambda: SetUnion((declared_set("(0,1) \\/ (1, inf)"), Named("ℝ"))),
            "with a SetUnion as a member",
            id="a-union-as-a-member-of-a-union",
        ),
    ],
)
def test_to_source_refuses_a_term_that_no_declaration_writes(unwritten, words):
    """`to_source` refuses, naming the reason, a term that no declaration of
    a stage file writes, such as a union as a factor of a product, which no
    parentheses could set apart, or a union of one member."""
    term = unwritten()
    with pytest.raises(NotImplementedError, match=words):
        to_source(term)


def test_the_arrow_of_a_set_of_functions_takes_the_whole_union_as_the_set_of_its_entries():
    """The arrow binds after the union, so `{1, …, 2} → (0,1) \\/ (1, 2)` is
    lowered to the collections whose entries lie in the union, a term that
    `to_source` prints as `{1, …, 2} → (0, 1) \\/ (1, 2)`."""
    functions = declared_set("{1, …, 2} → (0,1) \\/ (1, 2)")
    assert isinstance(functions, Functions) and isinstance(functions.codomain, SetUnion)
    assert to_source(functions) == "{1, …, 2} → (0, 1) \\/ (1, 2)"


def test_a_union_in_one_type_with_an_interval_is_kept_as_the_union_bounded_by_two_conditions():
    """Several sets in one type, a union and the interval `(0, R)`, are kept
    as the union restricted by the two conditions of the interval."""
    kept = declared_set("(0,1) \\/ (1, inf) @ (0, R)")
    assert isinstance(kept, Comprehension) and kept.base == declared_set("(0,1) \\/ (1, inf)")
    assert [to_source(c) for c in kept.conds] == ["β > 0", "β < R"]


@pytest.mark.parametrize(
    ("written", "conditions"),
    [
        pytest.param(
            "(0,1) \\/ (1, inf) @ (0, inf)", ["β > 0"], id="a-union-of-members-open-at-inf"
        ),
        pytest.param(
            "(0,1) \\/ [1, inf] @ (0, inf)",
            ["β > 0", "β < inf"],
            id="a-union-with-a-member-that-holds-inf",
        ),
        pytest.param(
            "(0, 1) \\/ [2, T] @ (0, inf)",
            ["β > 0", "β < inf"],
            id="a-union-with-a-member-closed-at-a-name",
        ),
        pytest.param(
            "(0, 1) \\/ [2, 3] @ (0, inf)", ["β > 0"], id="a-union-of-members-closed-at-numbers"
        ),
        pytest.param("ℝ \\ {0} @ (0, inf)", ["β > 0"], id="a-difference-from-the-reals"),
        pytest.param(
            "ℝ̄ \\ {0} @ (0, inf)",
            ["β > 0", "β < inf"],
            id="a-difference-from-the-extended-reals",
        ),
    ],
)
def test_an_open_infinite_endpoint_bounds_a_union_or_a_difference_only_where_it_may_hold_inf(
    written, conditions
):
    """The interval `(0, inf)` adds the condition `β < inf` to a union only
    where one of its members may hold the infinity, and to a difference only
    where its left side may hold it."""
    assert [to_source(c) for c in declared_set(written).conds] == conditions


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("(0,1) \\/ (2,3) @ ℝ₊₊", id="a-union-and-a-reserved-set"),
        pytest.param("(0,1) \\/ (2,3) @ (4,5) \\/ (6,7)", id="two-unions"),
    ],
)
def test_a_union_counts_as_a_set_that_is_no_interval_among_several_sets_of_one_type(written):
    """A union counts as a set that is no interval, of which several sets in
    one type hold at most one, so that a union beside a reserved set or
    beside a second union is refused."""
    with pytest.raises(ConstructionError, match="are no intervals"):
        declared_set(written)


# The members and the sides that are refused


@pytest.mark.parametrize(
    ("written", "whole", "place", "part", "kind"),
    [
        pytest.param(
            "{a, b} \\/ (0, 1)",
            "union",
            "member",
            "{a, b}",
            "a set of labels",
            id="a-set-of-labels-as-a-member",
        ),
        pytest.param(
            "ℝ × ℝ \\/ (0, 1)", "union", "member", "ℝ × ℝ", "a product", id="a-product-as-a-member"
        ),
        pytest.param(
            "(0, 1) \\ {a, b}",
            "difference",
            "right side",
            "{a, b}",
            "a set of labels",
            id="a-set-of-labels-as-the-right-side",
        ),
        pytest.param(
            "ℝ × ℝ \\ (0, 1)",
            "difference",
            "left side",
            "ℝ × ℝ",
            "a product",
            id="a-product-as-the-left-side",
        ),
    ],
)
def test_a_member_or_a_side_that_is_no_set_of_numbers_is_refused_where_it_is_written(
    written, whole, place, part, kind
):
    """The lowering refuses under `syntax` a member of a union or a side of a
    difference that is a set of labels or a product, which binds before the
    two signs, naming the place of the part and advising a set of numbers
    there."""
    with pytest.raises(ConstructionError) as refused:
        declared_set(written)
    error = refused.value
    phrases = [
        f"the {whole} `{written}` has the {place} `{part}`, which is {kind}; ",
        "formed among sets of numbers",
    ]
    assert error.rule == "syntax"
    assert [phrase for phrase in phrases if phrase not in error.message] == []
    assert error.write.endswith(
        "on each side of the sign: an interval, a reserved set, a list of integers, "
        "`{1, 2}`, or a named set of numbers"
    )


def test_a_list_inside_a_difference_is_refused_where_it_lists_a_number_that_is_no_integer():
    """The list `{0.5}` on the right side of a difference is refused under
    `readable-form`, as every listed set that lists a number other than an
    integer is."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : ℝ₊₊ \\ {0.5}"))
    assert refused.value.rule == "readable-form"
    assert "the set {0.5} lists 0.5, which is no integer" in refused.value.message


@pytest.mark.parametrize(
    ("declaration", "words"),
    [
        pytest.param(
            "β : ℝ₊₊\nw : Xl \\/ (0, 1)",
            "the union `(0, 1) \\/ Xl` has the member `Xl`, ",
            id="a-member-of-the-set-of-a-parameter-that-no-line-reads",
        ),
        pytest.param(
            "β : Xl \\/ (0, 1)",
            "the union `(0, 1) \\/ Xl` has the member `Xl`, ",
            id="a-member-of-the-set-of-a-parameter-that-a-line-reads",
        ),
        pytest.param(
            "β : (0, 1) \\ Xl",
            "the difference `(0, 1) \\ Xl` has the right side `Xl`, ",
            id="the-right-side",
        ),
        pytest.param(
            "β : Xl \\ {1}",
            "the difference `Xl \\ {1}` has the left side `Xl`, ",
            id="the-left-side",
        ),
    ],
)
def test_a_member_or_a_side_that_names_a_set_of_labels_is_refused_where_the_stage_is_typed(
    declaration, words
):
    """A member or a side that names the set of labels `Xl` is refused under
    `readable-form`, the union quoted in the order in which the lowering
    keeps it, whether a line reads the parameter, as `W = β*V[>]` reads β,
    or none does."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("Xl := {low, high}\n" + declaration))
    error = refused.value
    phrases = [
        words + "which the file defines as `{low, high}`, a set of labels; ",
        "formed among sets of numbers",
    ]
    assert error.rule == "readable-form"
    assert [phrase for phrase in phrases if phrase not in error.message] == []
    assert error.write.endswith(
        "on each side of the sign: an interval, a reserved set, a list of integers, "
        "`{1, 2}`, or a named set of numbers"
    )


@pytest.mark.parametrize(
    ("declaration", "words"),
    [
        pytest.param("β : (0, n) \\/ (2, 3)", "reads the name 'n'", id="a-name-in-a-member"),
        pytest.param("β : ℝ₊₊ \\ (0, n)", "reads the name 'n'", id="a-name-in-the-right-side"),
        pytest.param("β : Foo \\/ (2, 3)", "names the set 'Foo'", id="a-set-as-a-member"),
        pytest.param("β : ℝ₊₊ \\ Foo", "names the set 'Foo'", id="a-set-as-the-right-side"),
        pytest.param("β : Foo \\ {1}", "names the set 'Foo'", id="a-set-as-the-left-side"),
    ],
)
def test_an_undeclared_name_or_an_undefined_set_in_a_member_or_a_side_is_refused(
    declaration, words
):
    """An undeclared name or an undefined set inside a member of a union or
    a side of a difference is refused under `name-in-scope`, as in any
    declared set."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets(declaration))
    assert refused.value.rule == "name-in-scope"
    assert words in refused.value.message


@pytest.mark.parametrize(
    ("declaration", "rule", "words"),
    [
        pytest.param(
            "w : (0, 𝑓) \\/ (2, 3)",
            "well-typed",
            "`(0, 𝑓)` reads it as a number",
            id="an-end-of-an-interval-in-a-member",
        ),
        pytest.param(
            "w : ℝ₊₊ \\ (0, 𝑓)",
            "well-typed",
            "`(0, 𝑓)` reads it as a number",
            id="an-end-of-an-interval-in-the-right-side",
        ),
        pytest.param(
            "w : {1, …, 𝑓} \\/ (5, 6)",
            "readable-form",
            "reads 𝑓, which is no number",
            id="a-bound-of-a-range-in-a-member",
        ),
    ],
)
def test_a_function_written_as_an_end_or_a_bound_in_a_member_or_a_side_is_refused(
    declaration, rule, words
):
    """Each member of a union and each side of a difference is typed as a
    set of its own, so a function 𝑓 written as an end of an interval or as
    a bound of a range there is refused."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            two_nodes_text_with_parameter_sets("β : ℝ₊₊\n𝑓(x : ℝ) := x^2\n" + declaration)
        )
    assert refused.value.rule == rule
    assert words in refused.value.message


# The sets in which a union and a difference are read


def test_a_derived_parameter_declared_in_a_union_keeps_the_union_as_its_set(
    derived_parameter_in_a_union,
):
    """The derived parameter q declared in `(0,1) \\/ (2, 3)` keeps that
    union as its declared set."""
    assert to_source(derived_parameter_in_a_union.par["q"].domain) == "(0, 1) \\/ (2, 3)"


def test_a_setting_declared_in_a_union_keeps_the_union_as_its_set(setting_in_a_union):
    """The setting tol that an addition declares in `(0, 1) \\/ (2, 3)`
    keeps that union as its declared set."""
    assert to_source(setting_in_a_union.settings["tol"].domain) == "(0, 1) \\/ (2, 3)"


# a union or a difference written in the set of a field, of a shock, of an
# argument of a function or of a named set: the fixture of the text and
# the line that a row changes, then the subject, the parts held, the
# reason, the address and the advice of the refusal; the address of a
# declaration at the top level is the number of its line: β stands on line
# 2 of the two-node stage, so a line added after it is line 3, and y stands
# on line 4, z on line 6 and Γ on line 8
UNIONS_AND_DIFFERENCES_IN_SETS_OF_FIELDS = [
    pytest.param(
        "text_of_the_two_node_stage",
        TWO_NODES_ARRIVAL_K_DECLARATION,
        "(k : ℝ \\ {0}) : !arvl",
        "k in block 'arvl_to_dcsn' is declared in the set `ℝ \\ {0}`",
        "a difference",
        None,
        "arvl_to_dcsn",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-field-on-a-side-of-a-block",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        "z : ℝ\n",
        "z : ℝ \\ {0} @ !shck\n",
        "z at the top level is declared in the set `ℝ \\ {0}`",
        "a difference",
        "the word `!shck` belongs to a field",
        "6",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-name-with-a-role-word",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        BETA,
        BETA + "w : ℝ \\ {0} @ !dcsn\n",
        "w at the top level is declared in the set `ℝ \\ {0}`",
        "a difference",
        "the word `!dcsn` belongs to a field",
        "3",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-name-with-a-perch-word",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        "y : ℝ\n",
        "y : ℝ \\ {0}\n",
        "y at the top level is declared in the set `ℝ \\ {0}`",
        "a difference",
        "y has a distribution, which makes it a shock, a field of the stage",
        "4",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-shock",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        BETA,
        BETA + "k_d : ℝ \\ {0}\n",
        "k_d at the top level is declared in the set `ℝ \\ {0}`",
        "a difference",
        "a block header lists k_d, which makes it a field",
        "3",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-field-declared-at-the-top-level",
    ),
    pytest.param(
        "cons_obs_file_text",
        "μ[>]   : ℝ₊ ⟂ a >= 0",
        "μ[>]   : ℝ \\ {0} ⟂ a >= 0",
        "the multiplier μ[>] in block 'policy' is declared in the set `ℝ \\ {0}`",
        "a difference",
        "a multiplier is a field of the continuation perch",
        "policy.slackness",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="a-multiplier",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        BETA,
        BETA + "𝑓(x : ℝ \\ {0}) := x^2\n",
        "the argument x of the function 𝑓 is declared in the set `ℝ \\ {0}`",
        "a difference",
        "an argument of a function takes the values of fields",
        "3",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="an-argument-of-a-function",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        "Γ(k : ℝ) := [0,1]",
        "Γ(k : ℝ \\ {0}) := [0,1]",
        "the argument k of the correspondence Γ is declared in the set `ℝ \\ {0}`",
        "a difference",
        "an argument of a correspondence takes the values of fields",
        "8",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="an-argument-of-a-correspondence",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        BETA,
        BETA + "Xq := {1, …, 2} → ℝ \\ {0}\n",
        "the set Xq is defined as `{1, …, 2} → ℝ \\ {0}`",
        "a difference",
        "a named set may type a field",
        "3",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="the-value-of-a-named-set",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        BETA,
        BETA + "H := {i : ℝ \\ {0} | i >= 1}\n",
        "the set H is defined as `{i : ℝ \\ {0} | i >= 1}`",
        "a difference",
        "a named set may type a field",
        "3",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="the-set-of-the-variable-of-a-named-set",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        "Γ(k : ℝ) := [0,1]",
        "Γ(k : ℝ) := {x : ℝ \\ {0} | x <= 1}",
        "the correspondence Γ is defined as `{x : ℝ \\ {0} | x <= 1}`",
        "a difference",
        "a correspondence restricts a control, which is a field",
        "8",
        "Write the left side, `ℝ`, in place of `ℝ \\ {0}`",
        id="the-set-of-the-variable-of-a-correspondence",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        TWO_NODES_ARRIVAL_K_DECLARATION,
        "(k : (0,1) \\/ (2,3)) : !arvl",
        "k in block 'arvl_to_dcsn' is declared in the set `(0, 1) \\/ (2, 3)`",
        "a union",
        None,
        "arvl_to_dcsn",
        "Write one set that holds every member of `(0, 1) \\/ (2, 3)`, an interval or a "
        "listed set, in its place",
        id="a-union-on-a-side-of-a-block",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        TWO_NODES_ARRIVAL_K_DECLARATION,
        "(k : (0,1) \\/ (2,3) \\ {5}) : !arvl",
        "k in block 'arvl_to_dcsn' is declared in the set `(0, 1) \\/ (2, 3) \\ {5}`",
        "a union and a difference",
        None,
        "arvl_to_dcsn",
        "Write one set that holds every member of `(0, 1) \\/ (2, 3)`, an interval or a "
        "listed set, in place of `(0, 1) \\/ (2, 3) \\ {5}`",
        id="a-difference-from-a-union-on-a-side-of-a-block",
    ),
    pytest.param(
        "text_of_the_two_node_stage",
        TWO_NODES_ARRIVAL_K_DECLARATION,
        "(k : ℝ \\ {0} \\ {1}) : !arvl",
        "k in block 'arvl_to_dcsn' is declared in the set `ℝ \\ {0} \\ {1}`",
        "a difference",
        None,
        "arvl_to_dcsn",
        "Write the first set, `ℝ`, in place of `ℝ \\ {0} \\ {1}`",
        id="two-differences-on-a-side-of-a-block",
    ),
]


@pytest.mark.parametrize(
    ("base", "old", "new", "subject", "held", "reason", "address", "write"),
    UNIONS_AND_DIFFERENCES_IN_SETS_OF_FIELDS,
)
def test_a_union_or_a_difference_in_a_set_not_of_a_parameter_or_a_setting_is_refused(
    request, base, old, new, subject, held, reason, address, write
):
    """A union or a difference in any set but that of a parameter, a derived
    parameter or a setting is refused under `readable-form` where the set is
    declared, the sentence saying that the grids and the connections read no
    union and no difference, and the advice naming one set to write."""
    text = request.getfixturevalue(base)
    assert text.count(old) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text.replace(old, new))
    error = refused.value
    why = (
        "; a union and a difference are written in the set of a parameter, of a derived "
        "parameter or of a setting alone, since the set of a field is read by the grids and the "
        "connections, which read no union and no difference"
    )
    assert error.rule == "readable-form"
    assert error.message == f"{subject}, which holds {held}{why}" + (
        f", and {reason}" if reason else ""
    )
    assert error.address == address
    assert error.write == write


def test_a_union_as_the_value_of_a_named_set_is_refused_by_the_parser():
    """The parser reads the value of a named set after `:=` without the
    signs of a union and a difference, so it refuses
    `Xρ := (0,1) \\/ (1, inf)` under `syntax` at the sign `\\/`."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(BETA, BETA + "Xρ := (0,1) \\/ (1, inf)\n"))
    assert refused.value.rule == "syntax"
    assert "the file writes `\\/ (1, inf)` here" in refused.value.parts.why


def test_a_refusal_of_the_parser_where_a_set_may_continue_names_the_two_signs():
    """The refusal of `β : (0,1) (0, R)` under `syntax`, where the set may
    continue, names `\\/` and `\\` among the forms that the language admits
    there."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_parameter_sets("β : (0,1) (0, R)"))
    assert refused.value.rule == "syntax"
    assert "`×`, `\\/`, `\\`, `:=`" in refused.value.parts.why


# The conditions that a stage records for a union and a difference


@pytest.mark.parametrize(
    ("declared", "recorded"),
    [
        pytest.param("ℝ", True, id="the-reals-the-base-of-the-other-rows"),
        pytest.param("ℝ \\ {0}", False, id="a-difference-whose-right-side-removes-zero"),
        pytest.param("ℝ₊₊ \\ {1}", False, id="a-difference-whose-left-side-excludes-zero"),
        pytest.param("(-1, 0) \\/ (0, 1)", False, id="a-union-whose-members-exclude-zero"),
        pytest.param("(-1, 1) \\/ (2, 3)", True, id="a-union-with-a-member-that-holds-zero"),
        pytest.param("ℝ \\ {1}", True, id="a-difference-that-keeps-zero"),
    ],
)
def test_the_condition_that_a_divisor_is_not_zero_is_recorded_unless_its_set_excludes_zero(
    stage_dividing_by_beta, declared, recorded
):
    """The stage whose law of motion divides by β records the condition
    `arithmetic-definedness` unless the set that declares β, a union or a
    difference among them, excludes zero."""
    stage = stage_dividing_by_beta(declared)
    assert bool(explanations_of(stage, "arithmetic-definedness")) == recorded


@pytest.mark.parametrize(
    ("declared", "recorded"),
    [
        pytest.param("ℝ", True, id="the-reals-the-base-of-the-other-rows"),
        pytest.param("ℝ \\ {0}", True, id="a-difference-whose-left-side-is-not-positive"),
        pytest.param("ℝ₊₊ \\ {1}", False, id="a-difference-whose-left-side-is-positive"),
        pytest.param("(0,1) \\/ (1, inf)", False, id="a-union-of-positive-members"),
        pytest.param("(-1, 0) \\/ (0, 1)", True, id="a-union-with-a-member-that-is-not-positive"),
    ],
)
def test_the_condition_on_an_argument_is_recorded_unless_its_set_lies_in_the_declared_one(
    stage_dividing_by_beta, declared, recorded
):
    """The stage whose value line applies 𝑓(x : ℝ₊₊) to β records the
    condition `function-argument-domain-inclusion` unless the set that
    declares β, a union or a difference among them, lies in ℝ₊₊."""
    stage = stage_dividing_by_beta(declared)
    assert bool(explanations_of(stage, "function-argument-domain-inclusion")) == recorded


@pytest.mark.parametrize(
    "declared",
    [
        pytest.param("ℝ", id="the-reals-the-base-of-the-other-rows"),
        pytest.param("ℝ₊₊ \\ {1}", id="a-difference-from-a-reserved-set"),
        pytest.param("(0,1) \\/ (1, inf)", id="a-union-of-intervals"),
    ],
)
def test_no_condition_that_beta_is_a_number_is_recorded_where_its_set_holds_only_numbers(
    stage_dividing_by_beta, declared
):
    """A union or a difference of sets of numbers holds only numbers, as ℝ
    does, so the stage records no condition `numeric-domain-compatibility`
    for β declared in one."""
    stage = stage_dividing_by_beta(declared)
    assert explanations_of(stage, "numeric-domain-compatibility") == []


@pytest.mark.parametrize(
    ("declared", "recorded"),
    [
        pytest.param("{1, 2} \\/ {5}", False, id="a-union-of-members-of-the-index-set"),
        pytest.param("{1, …, 5} \\ {3}", False, id="a-difference-from-the-index-set"),
        pytest.param("{1, …, 9} \\ {6, 7, 8, 9}", True, id="a-difference-from-a-longer-range"),
        pytest.param("{1, 2} \\/ {7} \\ {7}", True, id="a-difference-from-a-union"),
        pytest.param("ℕ \\ (5, inf)", True, id="a-difference-from-the-natural-numbers"),
    ],
)
def test_the_inclusion_of_the_set_of_a_key_is_recorded_only_where_the_terms_leave_it_open(
    stage_reading_delta_at_j, declared, recorded
):
    """The stage records the inclusion of the set of the key j in the index
    set {1, …, 5} of δ as a condition to establish only where j is declared
    in neither a union of members of the index set nor a difference from
    it."""
    explanations = explanations_of(stage_reading_delta_at_j(declared), "set-inclusion")
    start = f"The set {declared} of j must lie within the index set {{1, …, 5}} of δ"
    assert [text.startswith(start) for text in explanations] == ([True] if recorded else [])


@pytest.mark.parametrize(
    "declared",
    [
        pytest.param("{1, 2} \\/ {7}", id="a-union-with-a-member-outside-the-index-set"),
        pytest.param("ℝ", id="the-reals-the-base-of-the-differences-from-them"),
        pytest.param("ℝ \\ {0}", id="the-reals-less-zero"),
        pytest.param("ℕ \\ {9}", id="the-natural-numbers-less-nine"),
        pytest.param("(0, 9) \\ {3}", id="an-interval-less-three"),
    ],
)
def test_a_key_declared_in_a_set_with_members_outside_the_index_set_is_refused(declared):
    """The key j is refused under `family-selection` where its set holds
    members outside the index set {1, …, 5} of δ: a union with such a
    member, or a set of infinitely many numbers with or without the members
    of a finite set removed."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text_reading_delta_at_j(declared))
    assert refused.value.rule == "family-selection"
    assert f"declared in {declared}, which is not within the index set" in refused.value.message


# The membership of a value that calibration and configuration decide


@pytest.mark.parametrize(
    ("declared", "inside", "outside", "printed"),
    [
        pytest.param(
            "(0,1) \\/ (1, inf)",
            0.5,
            1.0,
            "(0, 1) \\/ (1, inf)",
            id="a-union-refuses-the-number-between-its-members",
        ),
        pytest.param(
            "(0,1) \\/ (1, inf)",
            2.0,
            -1.0,
            "(0, 1) \\/ (1, inf)",
            id="a-union-refuses-a-number-below-its-members",
        ),
        pytest.param(
            "ℝ₊₊ \\ {1}",
            2.0,
            1.0,
            "ℝ₊₊ \\ {1}",
            id="a-difference-refuses-the-number-of-its-right-side",
        ),
        pytest.param(
            "ℝ₊₊ \\ {1}",
            2.0,
            -1.0,
            "ℝ₊₊ \\ {1}",
            id="a-difference-refuses-a-number-outside-its-left-side",
        ),
    ],
)
def test_calibration_admits_a_value_of_beta_only_where_it_lies_in_its_union_or_difference(
    stage_with_beta_in, declared, inside, outside, printed
):
    """Calibration decides that a value of β inside the union or the
    difference that declares β belongs to it, leaving no membership open,
    and refuses a value outside it, naming the declared set."""
    stage = stage_with_beta_in(declared)
    assert undecided_memberships(copy_native(stage).calibrate({"β": inside, "R": 0.9})) == []
    with pytest.raises(ValueError, match=re.escape(f"outside the declared set {printed}")):
        copy_native(stage).calibrate({"β": outside, "R": 0.9})


def test_a_union_is_decided_by_a_member_that_holds_and_left_open_where_no_other_member_holds(
    stage_with_beta_in,
):
    """Calibration decides the membership of β in `(0,1) \\/ (2, E_{y}(y^2))`
    at 0.5, which the first member holds, and leaves it open at 1.5, which
    only the member that it cannot decide may hold."""
    stage = stage_with_beta_in("(0,1) \\/ (2, E_{y}(y^2))")
    assert undecided_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    assert undecided_memberships(copy_native(stage).calibrate({"β": 1.5, "R": 0.9})) == [
        "The value 1.5 of β must belong to (0, 1) \\/ (2, E_{y}(y^2))."
    ]


def test_a_difference_is_left_open_where_its_right_side_is_not_decided_and_refused_by_its_left(
    stage_with_beta_in,
):
    """Calibration leaves the membership of β in `(0, 3) \\ (2, E_{y}(y^2))`
    open at 1.0, which the left side holds, and refuses 5.0, which the left
    side does not hold, whatever the right side holds."""
    stage = stage_with_beta_in("(0, 3) \\ (2, E_{y}(y^2))")
    assert len(undecided_memberships(copy_native(stage).calibrate({"β": 1.0, "R": 0.9}))) == 1
    with pytest.raises(ValueError, match=r"outside the declared set \(0, 3\) \\ \(2, E_\{y\}"):
        copy_native(stage).calibrate({"β": 5.0, "R": 0.9})


def test_a_member_of_a_union_that_reads_another_parameter_is_read_at_its_value(
    stage_with_beta_in,
):
    """Calibration reads the members of `(0, R) \\/ (2*R, inf)` at the value
    R = 0.9, so that it admits β = 0.5 and refuses β = 1.0, which lies
    between 0.9 and 1.8."""
    stage = stage_with_beta_in("(0, R) \\/ (2*R, inf)")
    assert undecided_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    with pytest.raises(ValueError, match="parameter 'β'"):
        copy_native(stage).calibrate({"β": 1.0, "R": 0.9})


def test_calibration_names_the_part_of_a_union_bounded_by_an_interval_that_a_value_breaks(
    stage_with_beta_in,
):
    """Calibration holds β to the union and to each bound of
    `(0,1) \\/ (1, inf) @ (0, R)`, and its refusal names the union or the
    condition that the value breaks."""
    stage = stage_with_beta_in("(0,1) \\/ (1, inf) @ (0, R)")
    assert undecided_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    with pytest.raises(ValueError, match=r"outside the declared set \(0, 1\) \\/ \(1, inf\)"):
        copy_native(stage).calibrate({"β": 1.0, "R": 2.0})
    with pytest.raises(ValueError, match="does not satisfy the condition β < R"):
        copy_native(stage).calibrate({"β": 0.95, "R": 0.9})


def test_calibration_holds_each_entry_of_a_collection_to_the_union_of_its_entries():
    """Calibration admits δ = [0.5, 1.5] for `δ : {1, …, 2} → (0,1) \\/ (1, 2)`
    and refuses δ = [0.5, 1.0], naming the key of the entry outside the
    union."""
    stage = stage_from_text(
        two_nodes_text_with_parameter_sets("β : ℝ₊₊\nδ : {1, …, 2} → (0,1) \\/ (1, 2)")
    )
    values = {"β": 1.0, "R": 1.0}
    assert undecided_memberships(copy_native(stage).calibrate({**values, "δ": [0.5, 1.5]})) == []
    with pytest.raises(
        ValueError, match=r"the entry at the key 2 1\.0 lies outside \(0, 1\) \\/ \(1, 2\);"
    ):
        copy_native(stage).calibrate({**values, "δ": [0.5, 1.0]})


@pytest.mark.parametrize(
    "values",
    [
        pytest.param({"β": 0.5, "R": 1.0}, id="q-is-0.5-in-the-first-member"),
        pytest.param({"β": 0.5, "R": 5.0}, id="q-is-2.5-in-the-second-member"),
    ],
)
def test_calibration_holds_the_value_of_a_derived_parameter_to_its_union(
    derived_parameter_in_a_union, values
):
    """Calibration admits values at which q = β*R lies in the union
    `(0,1) \\/ (2, 3)` that declares q, and refuses β = 0.5 with R = 3.0,
    at which q = 1.5, naming q, its set and the values."""
    stage = derived_parameter_in_a_union
    assert undecided_memberships(copy_native(stage).calibrate(values)) == []
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate({"β": 0.5, "R": 3.0})
    phrases = [
        "derived parameter 'q'",
        "lies outside the declared set (0, 1) \\/ (2, 3) at β = 0.5, R = 3.0",
    ]
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


@pytest.mark.parametrize(
    "inside",
    [
        pytest.param(0.5, id="in-the-first-member"),
        pytest.param(2.5, id="in-the-second-member"),
    ],
)
def test_configuration_holds_the_value_of_a_setting_to_its_union(setting_in_a_union, inside):
    """`configure` admits a value of the setting tol inside its union
    `(0, 1) \\/ (2, 3)` and refuses 1.5, which lies between the two
    members, under `setting-outside-set`."""
    copy_native(setting_in_a_union).configure({"tol": inside})
    with pytest.raises(ConstructionError) as refused:
        copy_native(setting_in_a_union).configure({"tol": 1.5})
    assert refused.value.rule == "setting-outside-set"
    assert "the value 1.5 lies outside the declared set (0, 1) \\/ (2, 3)" in refused.value.message


@pytest.mark.parametrize(
    ("declared", "declarations", "at", "status"),
    [
        pytest.param(
            "{1, …, J} \\/ {2}",
            "J : ℕ\n",
            {"J": 4},
            "established",
            id="a-union-with-a-range-to-a-parameter",
        ),
        pytest.param(
            "{1, …, J} \\ (5, inf)",
            "J : ℕ\n",
            {"J": 9},
            "established",
            id="a-range-to-a-parameter-less-the-numbers-above-five",
        ),
        pytest.param(
            "{1, …, 9} \\ {6, 7, 8, 9}",
            "",
            {},
            "established",
            id="a-range-less-the-numbers-above-five",
        ),
        pytest.param(
            "{1, 2} \\/ {7} \\ {7}", "", {}, "established", id="a-union-less-its-member-outside"
        ),
        pytest.param(
            "ℕ \\ (5, inf)", "", {}, "required", id="a-left-side-of-infinitely-many-members"
        ),
        pytest.param(
            "{1, …, 9} \\ (5, K)",
            "K : ℝ\n",
            {"K": 20.0},
            "required",
            id="a-right-side-with-an-end-that-is-a-parameter",
        ),
    ],
)
def test_calibration_establishes_the_inclusion_of_a_keys_set_only_where_its_members_are_known(
    stage_reading_delta_at_j, declared, declarations, at, status
):
    """Calibration establishes the inclusion of the set of the key j in the
    index set {1, …, 5} of δ where the values make the members of a union or
    of a difference known, and leaves it required where the left side has
    infinitely many members or an end of the right side is a parameter."""
    stage = stage_reading_delta_at_j(declared, declarations)
    values = {"β": 0.9, "R": 1.0, "δ": [1, 2, 3, 4, 5], "j": 2}
    bound = copy_native(stage).calibrate({**values, **at})
    assert statuses_of(bound, "set-inclusion") == [status]


@pytest.mark.parametrize(
    ("declared", "declarations", "at", "made_false"),
    [
        pytest.param(
            "{1, …, J} \\/ {2}",
            "J : ℕ\n",
            {"J": 9},
            "J = 9 makes {1, …, J} \\/ {2} ⊆ {1, …, 5} false",
            id="a-range-to-a-parameter-in-a-union",
        ),
        pytest.param(
            "{1, …, 9} \\ {6, 7, 8}",
            "",
            {},
            "(no parameters) makes {1, …, 9} \\ {6, 7, 8} ⊆ {1, …, 5} false",
            id="a-range-less-three-of-its-four-numbers-above-five",
        ),
    ],
)
def test_calibration_refuses_values_at_which_a_member_of_a_keys_set_is_outside_the_index_set(
    stage_reading_delta_at_j, declared, declarations, at, made_false
):
    """Calibration refuses the values at which the set of the key j holds a
    member outside the index set {1, …, 5} of δ, naming the values and the
    inclusion that they make false."""
    stage = stage_reading_delta_at_j(declared, declarations)
    values = {"β": 0.9, "R": 1.0, "δ": [1, 2, 3, 4, 5], "j": 2}
    with pytest.raises(ValueError, match=re.escape(f"calibration {made_false}")):
        copy_native(stage).calibrate({**values, **at})


# The answers of the functions of `bellman.typing.sets` and of
# `predicate_value`; an answer None is one that the terms leave open


@pytest.mark.parametrize(
    ("inner", "outer", "answer"),
    [
        pytest.param(
            "(0,1) \\/ (1, 2)", "(0, 2)", True, id="a-union-whose-members-lie-in-the-set"
        ),
        pytest.param(
            "(0,1) \\/ (1, 3)", "(0, 2)", False, id="a-union-with-a-member-outside-the-set"
        ),
        pytest.param("(0, 1)", "(0, 1] \\/ (1, 2)", True, id="a-set-in-one-member-of-a-union"),
        pytest.param(
            "(0, 2)", "(0, 1] \\/ (1, 2)", None, id="a-set-in-a-union-and-in-no-one-member"
        ),
        pytest.param("ℝ₊₊ \\ {1}", "ℝ₊", True, id="a-difference-whose-left-side-lies-in-the-set"),
        pytest.param(
            "ℝ \\ (-inf, 0]",
            "ℝ₊₊",
            None,
            id="a-difference-whose-left-side-does-not-lie-in-the-set",
        ),
        pytest.param(
            "(0, 2)", "(0, 1) \\ {5}", False, id="a-set-outside-the-left-side-of-a-difference"
        ),
        pytest.param(
            "(0, 1)", "ℝ₊₊ \\ {5}", None, id="a-set-inside-the-left-side-of-a-difference"
        ),
        # the closed interval [n, n] is the set of the one number n
        pytest.param("[0, 0]", "(-1, 0] \\/ (0, 1)", True, id="zero-in-a-member-of-a-union"),
        pytest.param("[0, 0]", "(-1, 0) \\/ (0, 1)", False, id="zero-in-no-member-of-a-union"),
        pytest.param("[2, 2]", "(0, 1) \\/ {2}", True, id="two-in-a-listed-member-of-a-union"),
        pytest.param(
            "[0, 0]", "(0, R) \\/ (2, 3)", None, id="zero-and-a-member-with-an-end-that-is-R"
        ),
        pytest.param("[1, 1]", "ℝ \\ {0}", True, id="one-in-the-reals-less-zero"),
        pytest.param("[0, 0]", "ℝ \\ {0}", False, id="zero-on-the-right-side-of-a-difference"),
        pytest.param(
            "[5, 5]", "(0, 1) \\ {0}", False, id="five-outside-the-left-side-of-a-difference"
        ),
        pytest.param(
            "[1, 1]", "ℝ \\ (0, R)", None, id="one-and-a-right-side-with-an-end-that-is-R"
        ),
    ],
)
def test_within_decides_the_inclusion_of_a_union_or_a_difference_or_leaves_it_open(
    inner, outer, answer
):
    """`sets.within` answers whether one set lies in another where one of
    them is a union or a difference: a union lies in a set where each member
    does, a set lies in a union where it lies in one member, a difference
    lies in a set where its left side does, and a set lies in a difference
    only where it lies in the left side, a number only where the right side
    does not hold it."""
    # the third argument holds the named sets that the two terms read: none
    assert sets.within(declared_set(inner), declared_set(outer), {}) is answer


@pytest.mark.parametrize(
    ("number", "declared", "at", "answer"),
    [
        pytest.param(0.5, "(0, 1) \\/ {1, …, J}", {}, True, id="in-the-interval-of-a-union"),
        pytest.param(5, "(0, 1) \\/ {1, …, J}", {"J": 5}, True, id="in-the-range-where-J-is-5"),
        pytest.param(
            7, "(0, 1) \\/ {1, …, J}", {"J": 5}, False, id="outside-the-union-where-J-is-5"
        ),
        pytest.param(7, "(0, 1) \\/ {1, …, J}", {}, None, id="a-union-with-J-unknown"),
        pytest.param(6, "(0, 9) \\ {1, …, J}", {"J": 5}, True, id="outside-the-right-side"),
        pytest.param(5, "(0, 9) \\ {1, …, J}", {"J": 5}, False, id="on-the-right-side"),
        pytest.param(6, "(0, 9) \\ {1, …, J}", {}, None, id="a-difference-with-J-unknown"),
        pytest.param(10, "(0, 9) \\ {1, …, J}", {}, False, id="outside-the-left-side"),
    ],
)
def test_predicate_value_decides_the_membership_of_a_number_in_a_union_or_a_difference(
    number, declared, at, answer
):
    """`predicate_value` decides the condition that a number belongs to a
    union or a difference at the values `at`, reading a range of integers by
    its members at those values."""
    condition = Member(Number(number), declared_set(declared))
    assert predicate_value(condition, at).value is answer


@pytest.mark.parametrize(
    ("declared", "answer"),
    [
        pytest.param("{1, 2} \\/ {5}", True, id="a-union-of-members-of-the-index-set"),
        pytest.param("{1, 2} \\/ {7}", False, id="a-union-with-a-member-outside"),
        pytest.param("{1, …, 5} \\ {3}", True, id="a-difference-from-the-index-set"),
        pytest.param("ℝ \\ {0}", False, id="the-reals-less-zero"),
        pytest.param("ℕ \\ {9}", False, id="the-natural-numbers-less-nine"),
        pytest.param("(0, 9) \\ {3}", False, id="an-interval-less-three"),
        pytest.param("{1, 2} \\/ {7} \\ {7}", None, id="a-difference-from-a-union"),
        pytest.param("{1, …, 9} \\ {6} \\ {7, 8, 9}", None, id="a-difference-from-a-difference"),
        pytest.param("ℕ \\ (5, inf)", None, id="a-difference-from-the-natural-numbers"),
    ],
)
def test_index_within_decides_whether_the_set_of_a_key_lies_in_an_index_set(declared, answer):
    """`sets.index_within` answers whether the set of a key lies in the index
    set {1, …, 5}: a union where each member does, a difference where its
    left side does, a set of infinitely many numbers less a finite set
    nowhere, and a difference from a union or from a difference is left
    open."""
    # the third argument holds the named sets that the two terms read: none
    assert sets.index_within(declared_set(declared), declared_set("{1, …, 5}"), {}) is answer


@pytest.mark.parametrize(
    ("declared", "answer"),
    [
        pytest.param("(0,1) \\/ (1, inf)", True, id="a-union-of-intervals"),
        pytest.param("ℝ₊₊ \\ {1}", True, id="a-difference-from-a-reserved-set"),
        pytest.param("(2, 3) \\ Xl", True, id="a-difference-whose-right-side-names-labels"),
        pytest.param("Xl \\/ (2, 3)", None, id="a-union-with-a-member-that-names-labels"),
        pytest.param("Xl \\ {1}", None, id="a-difference-whose-left-side-names-labels"),
    ],
)
def test_numeric_answers_whether_the_members_of_a_union_or_a_difference_are_numbers(
    declared, answer
):
    """`sets.numeric` answers that the members of a union are numbers where
    those of every member are, and those of a difference where those of its
    left side are, with no answer False for a part that names the set of
    labels Xl, since such a declaration is refused where the stage is
    typed."""
    labels = {"Xl": declared_set("{low, high}")}
    assert sets.numeric(declared_set(declared), labels) is answer


@pytest.mark.parametrize(
    ("written", "resolved"),
    [
        pytest.param("Xb \\/ (1, inf)", "[0,1) \\/ (1, inf)", id="a-member-of-a-union"),
        pytest.param(
            "Xb \\/ [0,1) \\/ (1, inf)",
            "[0,1) \\/ (1, inf)",
            id="a-member-equal-to-another-once-replaced",
        ),
        pytest.param("ℝ₊₊ \\ Xb", "ℝ₊₊ \\ [0,1)", id="the-right-side-of-a-difference"),
        pytest.param(
            "{1, …, 2} → Xb \\/ (1, 2)",
            "{1, …, 2} → [0,1) \\/ (1, 2)",
            id="a-member-of-the-union-of-the-entries-of-a-collection",
        ),
    ],
)
def test_resolved_replaces_a_named_set_in_a_union_or_a_difference_by_its_definition(
    written, resolved
):
    """`sets.resolved` replaces the named set Xb inside a member or a side
    by the set `[0,1)` that it is defined as, keeping the union in its one
    form, in which a member equal to another is held once."""
    named = {"Xb": declared_set("[0,1)")}
    assert sets.resolved(declared_set(written), named) == declared_set(resolved)
