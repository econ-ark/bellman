"""The declared sets of parameters, settings and derived parameters at
calibration and configuration: the names that such a set may read, so that
calibration can judge a value against it; the membership of a value that
calibration and configuration decide, on two-node stages and on stage
files of the applications; the bounds that have no value at the values;
and the judgment of a recorded condition at an infinite value.

`test_declared_sets.py` holds the tests of how a declaration's sets are
read, kept and printed."""

import math

import pytest
from application_files import (
    CORPUS,
    FIRST_CALIBRATIONS,
    PERFECT_FORESIGHT_CALIBRATION,
    PERFECT_FORESIGHT_FILE,
    PERFECT_FORESIGHT_FOLDER,
    RETURN_IMPATIENCE_FAILING_CALIBRATION,
    ROOT,
    SA_SAVINGS_CALIBRATIONS,
    SECOND_CALIBRATIONS,
)
from stage_builders import (
    calibration_refusal_sentence,
    construction_refusal,
    declared_set_of,
    methodized_copy,
    stage_from_text,
    two_nodes_stage_with_declared_sets,
    undecided_memberships,
)
from stage_texts import BETA_AND_R_DECLARATIONS, corpus_text, two_nodes_text_with_parameter_sets

from bellman.native.hypergraphs import copy_native
from bellman.native.identity import Identity
from bellman.native.predicates import Compare, Member
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage.calibration_requirements import predicate_value
from bellman.syntax import terms
from bellman.syntax.source import to_source

# what the set of each of the three may name, as the refusal of a set that
# reads a field says it
PARAMETER_SET = "a parameter's set names parameters, derived parameters, named sets and numbers"


SETTING_SET = (
    "a setting's set names settings, parameters, derived parameters, named sets and numbers"
)


DERIVED_SET = (
    "a derived parameter's set names parameters, derived parameters, named sets and numbers"
)


# The names that the set of a parameter, a setting or a derived parameter
# may read


# declarations of β whose sets read a parameter, a derived parameter, a
# named set or a shock under an expectation over it, whose value is a number
READABLE_SETS = (
    "β : (0, R)",
    "β : (0, h)\nh := 2*R",
    "Xn := [0, 9]\nβ : Xn",
    "β : (0, E_{y}(y^2))",
    "β : ℝ₊₊ @ (0, E_{y}(y^2))",
    "β : (0, E_{y,z}(y*z))",
    "β : (0, E_{y}(E_{z}(y*z)))",
)


@pytest.fixture(scope="module")
def stages_whose_parameter_sets_read_no_field():
    """The two-node stages whose declaration of β is each of
    `READABLE_SETS`; the reading raises here any refusal of one of them."""
    return [
        stage_from_text(two_nodes_text_with_parameter_sets(declarations))
        for declarations in READABLE_SETS
    ]


# declarations of β whose sets read a field of the two-node stage, each with
# the words of the refusal for the name read and the set that reads it
FIELD_READS = [
    pytest.param(
        "β : (0, k_d)",
        "the name 'k_d', a field of the stage, in the set `(0, k_d)`",
        id="a-state",
    ),
    pytest.param(
        "β : (0, c)", "the name 'c', a field of the stage, in the set `(0, c)`", id="a-control"
    ),
    pytest.param(
        "β : (a, 1)",
        "the name 'a', a field of the stage, in the set `(a, 1)`",
        id="a-continuation-state",
    ),
    pytest.param(
        "β : (0, V)", "the name 'V', a field of the stage, in the set `(0, V)`", id="a-value"
    ),
    pytest.param(
        "β : (0, 2*k_d + 1)",
        "the name 'k_d', a field of the stage, in the set `(0, 2*k_d + 1)`",
        id="a-state-under-arithmetic",
    ),
    pytest.param(
        "β : ℝ₊₊ @ (0, k_d)",
        "the name 'k_d', a field of the stage, in the set `ℝ₊₊ @ (0, k_d)`",
        id="a-state-in-a-second-set-of-the-type",
    ),
    pytest.param(
        "β : (0, E_{y}(k_d*y))",
        "the name 'k_d', a field of the stage, in the set `(0, E_{y}(k_d*y))`",
        id="a-state-under-an-expectation",
    ),
    # an expectation binds a shock, and a state that it names is read
    pytest.param(
        "β : (0, E_{k_d}(k_d^2))",
        "the name 'k_d', a field of the stage, in the set `(0, E_{k_d}(k_d^2))`",
        id="a-state-that-an-expectation-names",
    ),
    # a field written with a perch mark is a field, also where the stage
    # lists none at that perch
    pytest.param(
        "β : (0, V[>])",
        "the field `V[>]` in the set `(0, V[>])`",
        id="a-value-with-a-perch-mark",
    ),
    pytest.param(
        "β : (0, k_d[<])",
        "the field `k_d[<]` in the set `(0, k_d[<])`",
        id="a-state-with-the-mark-of-a-perch-that-lists-none",
    ),
]


@pytest.mark.usefixtures("stages_whose_parameter_sets_read_no_field")
@pytest.mark.parametrize("declaration, read", FIELD_READS)
def test_the_set_of_a_parameter_is_refused_only_where_it_reads_a_field(declaration, read):
    """A set of β that reads a field is refused under `readable-form` at the
    declaration, with the reason and the names to write, while sets that
    read only names that calibration values are read."""
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets(declaration))
    )
    assert (error.rule, error.address) == ("readable-form", "2")
    assert f"the declaration of 'β' reads {read}; {PARAMETER_SET}; " in error.message
    assert error.message.endswith(
        "calibration judges the value of β against that set before any field has a value"
    )
    assert error.write == (
        "Write the set of 'β' from numbers, parameters, derived parameters and named sets"
    )


@pytest.mark.usefixtures("stages_whose_parameter_sets_read_no_field")
@pytest.mark.parametrize(
    "declaration, shock",
    [
        pytest.param("β : (0, y)", "y", id="a-shock"),
        pytest.param(
            "β : (0, E_{y}(y*z))", "z", id="a-shock-that-the-expectation-does-not-integrate"
        ),
        # the subscript of a derivative binds no shock
        pytest.param("β : (0, D_{y}(y^2))", "y", id="a-shock-under-a-derivative"),
    ],
)
def test_a_shock_in_the_set_of_a_parameter_is_refused_only_outside_an_expectation_over_it(
    declaration, shock
):
    """A set of β that reads a shock outside an expectation over it is
    refused under `readable-form`, with the advice to read the shock inside
    an expectation, while a shock under an expectation over it is read."""
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets(declaration))
    )
    assert error.rule == "readable-form"
    assert (
        f"reads the name {shock!r}, a shock of the stage, outside an expectation over it, "
        "in the set `"
    ) in error.message
    assert PARAMETER_SET in error.message
    assert error.write.endswith(f"or read {shock} inside `E_{{{shock}}}(…)`")


def test_a_named_set_that_reads_a_field_is_read_alone_and_refused_in_the_set_of_a_parameter():
    """The declaration `β : Xb` of a named set Xb that reads the field k_d
    is refused under `readable-form` at that declaration, quoting the
    definition of Xb, while the definition of Xb alone, by which a field may
    be typed, is read."""
    stage_from_text(two_nodes_text_with_parameter_sets("Xb := [0, k_d]\nβ : ℝ₊₊"))
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets("Xb := [0, k_d]\nβ : Xb"))
    )
    assert (error.rule, error.address) == ("readable-form", "3")
    assert (
        "the declaration of 'β' reads the name 'k_d', a field of the stage, in the set `Xb`, "
        "which is defined at t.bl:2:1 (term address '2') as `[0, k_d]`; "
    ) in error.message
    assert tuple(error.related[0])[:3] == ("original declaration", "t.bl", 2)


@pytest.mark.parametrize(
    "declarations, addition, quoted",
    [
        pytest.param(
            "Xb := {x : ℝ | x < k_d}\nβ : Xb",
            None,
            "in the set `Xb`, which is defined at t.bl:2:1 (term address '2') as "
            "`{x : ℝ | x < k_d}`; ",
            id="a-set-with-a-bar-in-the-stage-file",
        ),
        pytest.param(
            "β : ℝ₊₊",
            "Xs := [0, k_d]\ntol : Xs\n",
            "in the set `Xs`, which is defined at addition-1.bl:2:1 (term address '14') as "
            "`[0, k_d]`; ",
            id="an-interval-in-a-methods-file",
        ),
    ],
)
def test_the_refusal_of_a_named_set_that_reads_a_field_quotes_it_at_the_file_that_holds_it(
    declarations, addition, quoted
):
    """The refusal of a declaration whose named set reads a field quotes the
    definition of the set as its file writes it, at that file."""
    error = construction_refusal(
        lambda: two_nodes_stage_with_declared_sets(declarations, addition)
    )
    assert quoted in error.message


# the laws of the two shocks y and z of the two-node stage
SHOCK_LAWS = "y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n"


def with_laws(declaration, y, z="N(0,1)"):
    """The two-node stage text with the declaration of β replaced by
    `declaration` and the laws of the shocks y and z by `y` and `z`."""
    return two_nodes_text_with_parameter_sets(declaration).replace(
        SHOCK_LAWS, f"y ~ {y}\nz : ℝ\nz ~ {z}\n"
    )


# declarations of β whose bound reads an expectation, each with a law of y
# that reads a parameter or a shock that the expectation integrates, which
# leaves the bound a number
LAWS_THAT_READ_NO_FIELD = (
    ("β : (0, E_{y}(y^2))", "N(0, R)"),
    ("β : (0, E_{y,z}(y*z))", "N(z, 1)"),
    ("β : (0, E_{z}(E_{y}(y*z)))", "N(z, 1)"),
)


@pytest.fixture(scope="module")
def stages_whose_laws_read_no_field():
    """The two-node stages of `LAWS_THAT_READ_NO_FIELD`; the reading raises
    here any refusal of one of them."""
    return [
        stage_from_text(with_laws(declaration, y)) for declaration, y in LAWS_THAT_READ_NO_FIELD
    ]


@pytest.mark.usefixtures("stages_whose_laws_read_no_field")
@pytest.mark.parametrize(
    "declaration, y, z, read",
    [
        pytest.param(
            "β : (0, E_{y}(y^2))",
            "N(k_d, 1)",
            "N(0,1)",
            "the name 'k_d', a field of the stage, through the law `N(k_d, 1)` of the shock 'y',",
            id="the-law-of-the-integrated-shock-reads-a-state",
        ),
        pytest.param(
            "β : (0, E_{y, z}(y*z))",
            "N(z, 1)",
            "N(k_d, 1)",
            "the name 'k_d', a field of the stage, through the law `N(k_d, 1)` of the shock 'z',",
            id="the-law-of-a-second-integrated-shock-reads-a-state",
        ),
        pytest.param(
            "β : (0, E_{y}(y^2))",
            "N(z, 1)",
            "N(0,1)",
            "the name 'z', a shock of the stage, outside an expectation over it, through the "
            "law `N(z, 1)` of the shock 'y',",
            id="the-law-reads-a-shock-that-no-expectation-integrates",
        ),
    ],
)
def test_a_parameters_set_is_refused_only_where_the_law_of_a_shock_it_integrates_reads_a_field(
    declaration, y, z, read
):
    """An expectation in the set of β reads the law of each shock that it
    integrates, so a field that such a law reads is refused under
    `readable-form`, while laws that read parameters or integrated shocks
    leave the bound a number."""
    assert TWO_NODES.count(SHOCK_LAWS) == 1
    error = construction_refusal(lambda: stage_from_text(with_laws(declaration, y, z)))
    assert error.rule == "readable-form"
    assert (
        f"the declaration of 'β' reads {read} in the set `{declaration[4:]}`; {PARAMETER_SET}; "
    ) in error.message


def test_a_law_that_integrates_its_own_shock_is_refused_under_the_rule_of_distributions():
    """The law `y ~ N(E_{y}(y), 1)`, read once through the bound of β that
    integrates y, is refused under `distribution-dependency`."""
    assert TWO_NODES.count(SHOCK_LAWS) == 1
    error = construction_refusal(
        lambda: stage_from_text(with_laws("β : (0, E_{y}(y^2))", "N(E_{y}(y), 1)"))
    )
    assert error.rule == "distribution-dependency"


@pytest.mark.parametrize(
    "refused, accepted, name, may_name",
    [
        pytest.param(
            ("β : ℝ₊₊", "tol : (0, k_d)\n"),
            ("β : ℝ₊₊\nh := 2*R", "n : ℝ₊₊\ntol : (0, n) @ (0, R) @ (0, h)\n"),
            "tol",
            SETTING_SET,
            id="a-setting",
        ),
        pytest.param(
            ("β : ℝ₊₊\nq : (0, k_d) := β*R", None),
            ("β : ℝ₊₊\nq : (0, E_{y}(y^2)) := β*R", None),
            "q",
            DERIVED_SET,
            id="a-derived-parameter",
        ),
    ],
)
def test_the_set_of_a_setting_or_a_derived_parameter_is_refused_only_where_it_reads_a_field(
    refused, accepted, name, may_name
):
    """The set of a setting or of a derived parameter that reads the field
    k_d is refused under `readable-form`, with what that set may name,
    while a set of the same name that reads a setting, a parameter, a
    derived parameter or a shock under an expectation is read."""
    two_nodes_stage_with_declared_sets(*accepted)
    error = construction_refusal(lambda: two_nodes_stage_with_declared_sets(*refused))
    assert error.rule == "readable-form"
    assert (
        f"the declaration of {name!r} reads the name 'k_d', a field of the stage" in error.message
    )
    assert may_name in error.message


@pytest.mark.parametrize(
    "name", [pytest.param("w", id="an-undeclared-name"), pytest.param("R", id="a-parameter")]
)
def test_an_expectation_in_a_set_over_a_name_with_no_declared_distribution_is_refused(name):
    """An expectation in the set of β over a name with no declared
    distribution is refused under `not-constructed`, with the advice to
    declare the distribution."""
    error = construction_refusal(
        lambda: stage_from_text(
            two_nodes_text_with_parameter_sets(f"β : (0, E_{{{name}}}({name}^2))")
        )
    )
    assert (error.rule, error.address) == ("not-constructed", "2")
    assert error.message == f"the expectation over {name!r} needs a declared distribution"
    assert error.write == (
        f"Declare the distribution of {name}, `{name} ~ …`, or write the set without the "
        f"expectation over {name}"
    )


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("β : (0, argmax_{y}(y))", id="an-argmax"),
        pytest.param("β : (0, solve_{y}(y - R))", id="a-solve"),
    ],
)
def test_an_argmax_or_a_solve_in_a_declared_set_is_refused_by_the_typing_of_the_set(declaration):
    """An argmax or a solve in the set of β is refused under `well-typed`."""
    error = construction_refusal(
        lambda: stage_from_text(two_nodes_text_with_parameter_sets(declaration))
    )
    assert error.rule == "well-typed"


# The membership of a value that calibration and configuration decide


@pytest.fixture(
    scope="module",
    params=[
        pytest.param((), id="no-methods-file"),
        pytest.param(("methods.egm.bl",), id="the-egm-methods-file"),
        pytest.param(("methods.bl",), id="the-methods-file"),
    ],
)
def perfect_foresight_methodized(request, read_only_stage_from_file):
    """The perfect-foresight stage of its file, methodized by none of its
    methods files or by one of them."""
    return methodized_copy(
        read_only_stage_from_file(PERFECT_FORESIGHT_FILE),
        *(ROOT / PERFECT_FORESIGHT_FOLDER / name for name in request.param),
    )


@pytest.mark.parametrize(
    "values",
    [
        pytest.param(PERFECT_FORESIGHT_CALIBRATION, id="the-baseline-calibration"),
        # a return factor below one at which the condition holds: q is
        # (0.85 × 0.9)^(1/2)/0.9, about 0.97
        pytest.param(
            {**RETURN_IMPATIENCE_FAILING_CALIBRATION, "β": 0.85}, id="a-return-factor-below-one"
        ),
    ],
)
def test_calibration_accepts_a_discount_factor_in_both_sets_of_its_type_and_refuses_others(
    perfect_foresight_methodized, values
):
    """Calibration of the perfect-foresight stage accepts a discount factor
    that lies in the base ℝ₊₊ and satisfies the condition β < R^(ρ - 1),
    and refuses one that breaks the condition or lies outside the base."""
    assert undecided_memberships(copy_native(perfect_foresight_methodized).calibrate(values)) == []
    with pytest.raises(ValueError) as refused:
        copy_native(perfect_foresight_methodized).calibrate(RETURN_IMPATIENCE_FAILING_CALIBRATION)
    phrases = ("parameter 'β'", "0.99", "ℝ₊₊ @ (0, R^(ρ - 1))", "β < R^(ρ - 1)", "R = 0.9")
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []
    with pytest.raises(ValueError, match=r"outside the declared set ℝ₊₊"):
        copy_native(perfect_foresight_methodized).calibrate(
            {**PERFECT_FORESIGHT_CALIBRATION, "β": -0.5}
        )


@pytest.mark.parametrize(
    "faulty",
    [
        pytest.param(-1.04, id="negative"),
        pytest.param(0.0, id="zero"),
        pytest.param(math.inf, id="infinite"),
    ],
)
def test_a_faulty_return_factor_is_refused_at_the_return_factor_by_its_own_set(
    perfect_foresight_methodized, faulty
):
    """Calibration refuses a return factor outside ℝ₊₊ at the parameter R,
    naming its set, although the bound of the set of β reads R."""
    with pytest.raises(ValueError) as refused:
        copy_native(perfect_foresight_methodized).calibrate(
            {**PERFECT_FORESIGHT_CALIBRATION, "R": faulty}
        )
    phrases = ("parameter 'R'", "ℝ₊₊")
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


# lines that replace the declarations of β and R, in several orders, each
# with values at which R lies outside its own set and the words of the
# refusal that name the condition or the set that R breaks; in each, the
# set of β reads R
OUTSIDE_THE_SET_OF_R = [
    pytest.param(
        ("β : (0,1) @ (0, R/2)", "R : ℝ₊₊ @ (1, 2)"),
        {"β": 0.4, "R": 0.5},
        "R > 1",
        id="r-breaks-a-bound-of-its-set-after-beta",
    ),
    pytest.param(
        ("R : ℝ₊₊ @ (1, 2)", "β : (0,1) @ (0, R/2)"),
        {"β": 0.4, "R": 0.5},
        "R > 1",
        id="r-breaks-a-bound-of-its-set-before-beta",
    ),
    pytest.param(
        ("β : (0, R) @ (0, 2*R)", "R : ℝ₊₊"),
        {"β": 0.5, "R": -1.04},
        "ℝ₊₊",
        id="r-outside-its-base-after-beta",
    ),
    pytest.param(
        ("R : ℝ₊₊", "β : (0, R) @ (0, 2*R)"),
        {"β": 0.5, "R": -1.04},
        "ℝ₊₊",
        id="r-outside-its-base-before-beta",
    ),
    # the endpoint S of the set of R is declared on the extended reals
    pytest.param(
        ("β : (0,1) @ (0, R)", "R : (0, S)", "S : ℝ̄"),
        {"β": 0.5, "R": -1.0, "S": 2.0},
        "(0, S)",
        id="r-outside-a-set-with-an-extended-real-endpoint-after-beta",
    ),
    pytest.param(
        ("R : (0, S)", "β : (0,1) @ (0, R)", "S : ℝ̄"),
        {"β": 0.5, "R": -1.0, "S": 2.0},
        "(0, S)",
        id="r-outside-a-set-with-an-extended-real-endpoint-before-beta",
    ),
    pytest.param(
        ("S : ℝ̄", "R : (0, S)", "β : (0,1) @ (0, R)"),
        {"β": 0.5, "R": -1.0, "S": 2.0},
        "(0, S)",
        id="r-outside-a-set-with-an-extended-real-endpoint-after-its-endpoint",
    ),
    # the bound 1/(R - 2) of β has no value at R = 2, which lies outside
    # the set of R
    pytest.param(
        ("β : (0, 1/(R-2))", "R : (3, inf)"),
        {"β": 0.2, "R": 2.0},
        "(3, inf)",
        id="r-outside-its-set-where-the-bound-of-beta-has-no-value",
    ),
]


@pytest.mark.parametrize("lines, values, words", OUTSIDE_THE_SET_OF_R)
def test_a_value_outside_its_own_set_is_refused_at_its_own_parameter_wherever_it_stands(
    lines, values, words
):
    """Calibration refuses a value of R outside its own set at the parameter
    R, naming the condition or the set that it breaks, wherever the line of
    R stands among the lines of the parameters whose sets read it."""
    assert TWO_NODES.count(BETA_AND_R_DECLARATIONS) == 1
    stage = stage_from_text(TWO_NODES.replace(BETA_AND_R_DECLARATIONS, "\n".join(lines) + "\n"))
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(values)
    assert "parameter 'R'" in str(refused.value) and words in str(refused.value)


# lines that replace the declarations of β and R, each with values at which
# β and another parameter lie outside their own sets
TWO_VALUES_OUTSIDE = [
    pytest.param(
        ("β : (0,1) @ (0, R)", "R : ℝ₊₊", "S : (0,1)"),
        {"β": 0.9, "R": 0.5, "S": 7.0},
        id="beta-before-s",
    ),
    pytest.param(
        ("R : ℝ₊₊", "β : (0,1) @ (0, R)", "S : (0,1)"),
        {"β": 0.9, "R": 0.5, "S": 7.0},
        id="beta-after-the-r-it-reads-and-before-s",
    ),
    # two bounds that read each other
    pytest.param(
        ("β : (0,1) @ (0, R)", "R : ℝ₊₊ @ (-inf, β)"),
        {"β": 0.5, "R": 0.5},
        id="two-bounds-that-read-each-other",
    ),
]


@pytest.mark.parametrize("lines, values", TWO_VALUES_OUTSIDE)
def test_of_two_values_outside_their_sets_the_refusal_names_the_first_in_the_file(lines, values):
    """Of two values that lie outside their own sets, calibration refuses
    the one whose declaration stands first in the file, β."""
    assert TWO_NODES.count(BETA_AND_R_DECLARATIONS) == 1
    stage = stage_from_text(TWO_NODES.replace(BETA_AND_R_DECLARATIONS, "\n".join(lines) + "\n"))
    with pytest.raises(ValueError, match="parameter 'β'"):
        copy_native(stage).calibrate(values)


def test_configuration_accepts_a_setting_in_its_set_and_refuses_one_that_breaks_a_condition():
    """Configuration of a stage calibrated at R = 0.9 accepts tol = 0.5 in
    the set (0, 1) @ (0, R) and refuses tol = 0.95 under
    `setting-outside-set`, naming the condition tol < R at R = 0.9."""
    bounded = copy_native(
        two_nodes_stage_with_declared_sets("β : ℝ₊₊", "tol : (0, 1) @ (0, R)\n")
    ).calibrate({"β": 0.5, "R": 0.9})
    copy_native(bounded).configure({"tol": 0.5})
    with pytest.raises(ConstructionError) as refused:
        copy_native(bounded).configure({"tol": 0.95})
    assert refused.value.rule == "setting-outside-set"
    assert "the condition tol < R of the declared set at R = 0.9" in refused.value.message


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(("a_min : ℝ₊ @ (1, 2)", "a_max : ℝ₊ @ (a_min, inf)"), id="a-min-first"),
        pytest.param(("a_max : ℝ₊ @ (a_min, inf)", "a_min : ℝ₊ @ (1, 2)"), id="a-max-first"),
    ],
)
def test_a_setting_outside_its_own_set_is_refused_at_that_setting_wherever_it_stands(lines):
    """Configuration refuses a_min = 5, outside its own set (1, 2), at the
    setting a_min, wherever its line stands beside the line of a_max, whose
    set reads a_min."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(
            two_nodes_stage_with_declared_sets("β : ℝ₊₊", "\n".join(lines) + "\n")
        ).configure({"a_min": 5.0, "a_max": 3.0})
    assert "setting 'a_min'" in refused.value.message


@pytest.fixture(scope="module")
def two_nodes_on_a_named_set_with_a_bar():
    """The two-node stage whose β is declared on the named set
    `Xb := {x : (0,1) | x < R, x > R/4}`, whose two conditions read R."""
    return stage_from_text(
        two_nodes_text_with_parameter_sets("Xb := {x : (0,1) | x < R, x > R/4}\nβ : Xb")
    )


@pytest.mark.parametrize(
    "value, words",
    [
        pytest.param(0.95, ("x < R", "R = 0.9"), id="above-r"),
        pytest.param(0.2, ("x > R/4", "R = 0.9"), id="below-a-quarter-of-r"),
        pytest.param(1.5, ("(0, 1)",), id="outside-the-base"),
    ],
)
def test_calibration_decides_the_membership_of_a_value_in_a_named_set_with_a_bar(
    two_nodes_on_a_named_set_with_a_bar, value, words
):
    """Calibration at R = 0.9 accepts β = 0.5 in the named set Xb and
    refuses a value outside it, naming the condition or the base that the
    value breaks."""
    stage = two_nodes_on_a_named_set_with_a_bar
    assert undecided_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate({"β": value, "R": 0.9})
    phrases = ("parameter 'β'", repr(value), *words)
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


def test_an_equality_is_a_condition_of_a_named_set_with_a_bar():
    """Calibration accepts β = R in the named set {x : ℝ | x = R} and
    refuses β = 0.8 at R = 0.9, naming the condition x = R."""
    equal = stage_from_text(two_nodes_text_with_parameter_sets("Xe := {x : ℝ | x = R}\nβ : Xe"))
    assert undecided_memberships(copy_native(equal).calibrate({"β": 0.9, "R": 0.9})) == []
    with pytest.raises(ValueError, match="the condition x = R"):
        copy_native(equal).calibrate({"β": 0.8, "R": 0.9})


def test_calibration_decides_both_conditions_of_a_named_set_bounded_by_an_interval_open_at_inf():
    """The set kept for `β : Xn @ [1, inf)` holds the conditions β >= 1 and
    β < inf, since the reading does not know the members of the named set
    Xn, and calibration accepts β = 2, which decides both, and refuses
    β = 0.5, naming the condition β >= 1."""
    extended = stage_from_text(
        two_nodes_text_with_parameter_sets("Xn := [0, 9]\nβ : Xn @ [1, inf)")
    )
    conditions = [to_source(condition) for condition in extended.par["β"].domain.conds]
    assert conditions == ["β >= 1", "β < inf"]
    assert undecided_memberships(copy_native(extended).calibrate({"β": 2.0, "R": 0.9})) == []
    with pytest.raises(ValueError, match="the condition β >= 1"):
        copy_native(extended).calibrate({"β": 0.5, "R": 0.9})


@pytest.fixture(scope="module")
def two_nodes_on_the_extended_reals_open_at_both_ends():
    """The two-node stage whose β is declared on `ℝ̄ @ (-inf, inf)`."""
    return stage_from_text(two_nodes_text_with_parameter_sets("β : ℝ̄ @ (-inf, inf)"))


@pytest.mark.parametrize(
    "point, condition",
    [
        pytest.param(math.inf, "β < inf", id="inf"),
        pytest.param(-math.inf, "β > -inf", id="minus-inf"),
    ],
)
def test_calibration_refuses_an_infinity_that_an_open_endpoint_excludes(
    two_nodes_on_the_extended_reals_open_at_both_ends, point, condition
):
    """Calibration of β on `ℝ̄ @ (-inf, inf)` refuses an infinite value,
    naming the condition of the open endpoint that excludes it."""
    whole = two_nodes_on_the_extended_reals_open_at_both_ends
    with pytest.raises(ValueError, match=f"the condition {condition}"):
        copy_native(whole).calibrate({"β": point, "R": 0.9})


def test_an_interval_whose_endpoint_reads_a_parameter_is_judged_at_calibration():
    """The set `(R, 1)` of β is read, and calibration refuses β = 0.5 at
    R = 2, where the interval holds no number."""
    late = stage_from_text(two_nodes_text_with_parameter_sets("β : (R, 1)"))
    assert "parameter 'β'" in calibration_refusal_sentence(late, {"β": 0.5, "R": 2.0})


# a declaration of the discount factor of the Epstein–Zin stage whose bound
# reads an expectation over the return Ψ, which no calibration decides
BETA_BOUNDED_BY_AN_EXPECTATION = "β : (0,1) @ (0, E_{Ψ}(Ψ^(1-γ))^((ρ-1)/(1-γ)))"


@pytest.fixture(scope="module")
def two_nodes_bounded_by_an_expectation():
    """The two-node stage whose β is declared on (0, 1) with a bound that
    reads an expectation over the shock y."""
    return stage_from_text(two_nodes_text_with_parameter_sets("β : (0,1) @ (0, E_{y}(y^2))"))


@pytest.fixture(scope="module")
def ez_savings_bounded_by_an_expectation():
    """The Epstein–Zin stage of its file with its one declaration of β
    replaced by `BETA_BOUNDED_BY_AN_EXPECTATION`; a file with no such line,
    or with several, raises ValueError."""
    text = corpus_text("ez_savings")
    (written,) = [row for row in text.split("\n") if row.startswith("β : ")]
    return stage_from_text(
        text.replace(written, BETA_BOUNDED_BY_AN_EXPECTATION), CORPUS["ez_savings"]
    )


@pytest.mark.parametrize(
    "stage, values, conditions, outside",
    [
        pytest.param(
            "two_nodes_bounded_by_an_expectation",
            {"β": 0.5, "R": 1.02},
            ["β < E_{y}(y^2)"],
            r"outside the declared set \(0, 1\)",
            id="the-two-node-stage",
        ),
        pytest.param(
            "ez_savings_bounded_by_an_expectation",
            FIRST_CALIBRATIONS["ez_savings"],
            ["β < E_{Ψ}(Ψ^(1 - γ))^((ρ - 1)/(1 - γ))"],
            r"parameter 'β' .*outside the declared set \(0, 1\)",
            id="the-epstein-zin-stage",
        ),
    ],
)
def test_a_bound_that_reads_an_expectation_stays_required_while_the_base_is_decided(
    request, stage, values, conditions, outside
):
    """The set of β is kept as the base (0, 1) with a condition that reads
    an expectation, so calibration leaves the membership of β required and
    refuses β = 1.5, outside the base."""
    bounded = request.getfixturevalue(stage)
    declared = bounded.par["β"].domain
    assert to_source(declared.base) == "(0, 1)"
    assert [to_source(condition) for condition in declared.conds] == conditions
    assert len(undecided_memberships(copy_native(bounded).calibrate(values))) == 1
    with pytest.raises(ValueError, match=outside):
        copy_native(bounded).calibrate({**values, "β": 1.5})


# The sets that stage files of the applications decide at calibration


@pytest.mark.parametrize(
    "values",
    [
        pytest.param(SA_SAVINGS_CALIBRATIONS[0], id="ambiguity-aversion-above-risk-aversion"),
        pytest.param(SA_SAVINGS_CALIBRATIONS[1], id="ambiguity-aversion-equal-to-risk-aversion"),
    ],
)
def test_the_smooth_ambiguity_stage_accepts_eta_only_where_it_is_at_least_gamma(
    sa_savings, values
):
    """Calibration of the smooth-ambiguity stage leaves no membership
    required at each of the two calibrations of the tests, of the ambiguity
    aversion η = 8 and of η equal to the risk aversion γ = 5, and refuses
    η = 4, below γ."""
    assert undecided_memberships(copy_native(sa_savings).calibrate(values)) == []
    with pytest.raises(ValueError) as refused:
        copy_native(sa_savings).calibrate({**values, "η": 4.0})
    phrases = ("parameter 'η'", "the condition η >= γ")
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


# the two calibrations of the Epstein–Zin stage that the tests use, each
# with the value of its derived parameter q, the return patience factor,
# which the stage file defines as
# (β*exp((1-ρ)*(μ_Ψ + (1-γ)*σ_Ψ^2/2)))^(1/ρ); at β = 0.96, ρ = 2, γ = 5,
# μ_Ψ = 0 and σ_Ψ = 0.1 it is (0.96*exp(0.02))^(1/2), and at β = 0.95 it is
# (0.95*exp(0.02))^(1/2), each inside the declared set (0, 1) of q; at
# β = 0.99 it is (0.99*exp(0.02))^(1/2), about 1.005, outside that set
EZ_CALIBRATIONS_AND_Q = [
    pytest.param(
        FIRST_CALIBRATIONS["ez_savings"],
        0.9896430095876418,
        id="the-first-calibration-of-the-tests",
    ),
    pytest.param(
        SECOND_CALIBRATIONS["ez_savings"],
        0.9844751256509318,
        id="the-second-calibration-of-the-tests",
    ),
]


@pytest.mark.parametrize("calibration, q", EZ_CALIBRATIONS_AND_Q)
def test_calibration_of_the_epstein_zin_stage_decides_the_membership_of_its_derived_q(
    ez_savings, calibration, q
):
    """Calibration of the Epstein–Zin stage computes q inside its set
    (0, 1) at each of the two calibrations of the tests and leaves no
    membership required, and refuses β = 0.99, at which q leaves its set,
    at the derived parameter q."""
    calibrated = copy_native(ez_savings).calibrate(calibration)
    assert calibrated.par["q"].value == pytest.approx(q)
    assert undecided_memberships(calibrated) == []
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        copy_native(ez_savings).calibrate({**calibration, "β": 0.99})


# The bounds of a declared set that have no value at the values


# the reason of the refusal of a division by zero, with the divisor and the
# values in its two places
ZERO = "the divisor `{}` is 0.0 at {}, and a division by zero has no value; "


# the sentence of each refusal of a bound that has no value at the values
DEFINED = "a declared set is defined at the values only where each of its bounds has a value; "


@pytest.fixture(scope="module")
def two_nodes_bounded_by_a_ratio():
    """The two-node stage whose β is declared on `(0, 1/(R-2))`."""
    return stage_from_text(two_nodes_text_with_parameter_sets("β : (0, 1/(R-2))"))


@pytest.mark.parametrize(
    "two", [pytest.param(2.0, id="a-floating-point-value"), pytest.param(2, id="an-integer")]
)
def test_a_bound_refuses_the_calibration_only_at_values_where_it_divides_by_zero(
    two_nodes_bounded_by_a_ratio, two
):
    """The bound 1/(R - 2) of the set of β is valued at R = 3 and refuses
    the calibration at R = 2, written as a floating-point number or as an
    integer, with the reason of a division by zero."""
    divided = two_nodes_bounded_by_a_ratio
    assert undecided_memberships(copy_native(divided).calibrate({"β": 0.2, "R": 3.0})) == []
    assert calibration_refusal_sentence(divided, {"β": 0.2, "R": two}) == (
        "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/(R - 2)` of the "
        f"declared set (0, 1/(R - 2)) has no value at R = {two!r}: "
        + ZERO.format("R - 2", f"R = {two!r}")
        + DEFINED
        + "write values at which `1/(R - 2)` has a value, or another bound"
    )


def test_a_bound_with_a_fractional_power_refuses_the_calibration_only_at_a_negative_base():
    """The bound R^(1/2) of the set of β is valued at R = 4 and refuses the
    calibration at R = -1, where the base of the power is negative."""
    rooted = stage_from_text(
        two_nodes_text_with_parameter_sets("β : (0, R^(1/2))", interest="R : ℝ")
    )
    assert undecided_memberships(copy_native(rooted).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "parameter 'β' (address 't.bl:2'): the bound `R^(1/2)` of the declared set "
        "(0, R^(1/2)) has no value at R = -1.0: the power `R^(1/2)` has the base -1.0 and the "
        "exponent 0.5, which is no integer at R = -1.0; a power with a noninteger exponent "
        "requires a positive base; " + DEFINED
    ) in calibration_refusal_sentence(rooted, {"β": 0.2, "R": -1.0})


@pytest.mark.parametrize(
    "declaration, interest, reason",
    [
        pytest.param(
            "β : (0, 10^R)",
            400.0,
            "the power `10^R` at R = 400.0 exceeds the largest finite floating-point number; ",
            id="a-power-above-the-largest-number",
        ),
        pytest.param(
            "β : (0, 1/R)",
            1e-320,
            "the value of `1/R` at R = 1e-320 is inf, which is no finite real number; ",
            id="a-ratio-whose-value-is-infinite",
        ),
    ],
)
def test_a_bound_whose_value_lies_beyond_the_floating_point_numbers_refuses_the_calibration(
    declaration, interest, reason
):
    """A bound whose value at the values lies beyond the finite
    floating-point numbers refuses the calibration with that reason."""
    sentence = calibration_refusal_sentence(
        stage_from_text(two_nodes_text_with_parameter_sets(declaration)), {"β": 0.2, "R": interest}
    )
    assert f"has no value at R = {interest!r}: {reason}{DEFINED}" in sentence


def test_a_bound_of_written_numbers_alone_that_divides_by_zero_names_no_values():
    """The bound 1/0 of the set of β refuses the calibration with the reason
    of a division by zero, which names no value of a parameter."""
    assert calibration_refusal_sentence(
        stage_from_text(two_nodes_text_with_parameter_sets("β : (0, 1/0)")), {"β": 0.2, "R": 2.0}
    ) == (
        "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/0` of the declared "
        "set (0, 1/0) has no value: the divisor `0` is 0.0, and a division by zero has no "
        "value; " + DEFINED + "write another bound"
    )


def test_a_bound_that_calls_log_is_valued_and_refused_where_log_has_no_value():
    """The bound log(R - 2) of the set of β is valued at R = 4 and refuses
    the calibration at R = 2, where the argument of log is 0."""
    called = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, log(R-2))"))
    assert undecided_memberships(copy_native(called).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "the bound `log(R - 2)` of the declared set (0, log(R - 2)) has no value at R = 2.0: "
        "the argument `R - 2` of log is 0.0 at R = 2.0, and log is defined at positive numbers "
        "alone; " + DEFINED
    ) in calibration_refusal_sentence(called, {"β": 0.2, "R": 2.0})


def test_a_bound_that_calls_exp_is_valued_at_the_calibration():
    """The bound exp(R - 1) of the set of β is valued at R = 1: calibration
    accepts β = 0.2 and refuses β = 1.5, outside (0, exp(R - 1))."""
    closed = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, exp(R-1))"))
    assert undecided_memberships(copy_native(closed).calibrate({"β": 0.2, "R": 1.0})) == []
    outside = calibration_refusal_sentence(closed, {"β": 1.5, "R": 1.0})
    assert "the value 1.5 lies outside the declared set (0, exp(R - 1))" in outside


def test_a_condition_that_reads_the_name_the_set_binds_stays_undecided_where_it_has_no_value():
    """The condition log(x) < R of the named set Xb reads the name that the
    set binds, so it is no bound of the set: at β = -1, where log(β) has no
    value, its membership stays required."""
    barred = stage_from_text(
        two_nodes_text_with_parameter_sets("Xb := {x : ℝ | log(x) < R}\nβ : Xb")
    )
    assert undecided_memberships(copy_native(barred).calibrate({"β": -1.0, "R": 2.0})) == [
        "The value -1.0 of β must belong to Xb."
    ]


@pytest.mark.parametrize(
    "declaration, declared",
    [
        pytest.param("β : (1/(R-2), 5)", "(1/(R - 2), 5)", id="a-lower-endpoint"),
        pytest.param(
            "β : ℝ₊₊ @ (0, 1/(R-2))",
            "ℝ₊₊ @ (0, 1/(R - 2))",
            id="an-upper-endpoint-of-a-second-set-of-the-type",
        ),
    ],
)
def test_a_lower_endpoint_or_an_endpoint_of_a_second_set_without_a_value_refuses_calibration(
    declaration, declared
):
    """A lower endpoint, or an endpoint of a second set of the type, that
    divides by zero at the values refuses the calibration with that
    reason."""
    sentence = calibration_refusal_sentence(
        stage_from_text(two_nodes_text_with_parameter_sets(declaration)), {"β": 0.2, "R": 2.0}
    )
    assert (
        f"the bound `1/(R - 2)` of the declared set {declared} has no value at R = 2.0: "
        + ZERO.format("R - 2", "R = 2.0")
    ) in sentence


def test_a_bound_without_a_value_is_refused_at_its_own_parameter_not_at_one_that_reads_it():
    """Calibration refuses the bound 1/(R - 2) at R = 2 at its own parameter
    β, and not at γ, whose set (0, β) reads β."""
    behind = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, 1/(R-2))\nγ : (0, β)"))
    assert calibration_refusal_sentence(behind, {"β": 0.2, "γ": 0.5, "R": 2.0}).startswith(
        "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/(R - 2)` of"
    )


def test_a_bound_that_reads_a_derived_parameter_is_judged_at_the_derived_values():
    """The bound 1/(q - 1) of the set of β, with q := R/2, is valued at
    R = 4 and refuses the calibration at R = 2, naming the derived value
    q = 1."""
    chained = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, 1/(q-1))\nq := R/2"))
    assert undecided_memberships(copy_native(chained).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "parameter 'β' (address 't.bl:2'): the bound `1/(q - 1)` of the declared set "
        "(0, 1/(q - 1)) has no value at q = 1.0 (the derived parameter q := R/2): "
        + ZERO.format("q - 1", "q = 1.0")
    ) in calibration_refusal_sentence(chained, {"β": 0.2, "R": 2.0})


def test_a_bound_of_the_set_of_a_derived_parameter_is_judged_at_the_calibration():
    """The bound 1/(R - 2) of the set of the derived parameter q is valued
    at R = 3 and refuses the calibration at R = 2 at q."""
    typed = stage_from_text(two_nodes_text_with_parameter_sets("β : ℝ₊₊\nq : (0, 1/(R-2)) := β*R"))
    assert undecided_memberships(copy_native(typed).calibrate({"β": 0.1, "R": 3.0})) == []
    assert (
        "derived parameter 'q' (address 't.bl:3'): the bound `1/(R - 2)` of the declared set "
        "(0, 1/(R - 2)) has no value at R = 2.0: " + ZERO.format("R - 2", "R = 2.0")
    ) in calibration_refusal_sentence(typed, {"β": 0.1, "R": 2.0})


def test_the_required_membership_of_a_bound_that_reads_an_expectation_names_value_and_set():
    """A bound that reads an expectation has no number at a calibration, so
    the membership of β = 0.2 in (0, E_{y}(y^2)) stays required, in those
    words."""
    expected = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, E_{y}(y^2))"))
    assert undecided_memberships(copy_native(expected).calibrate({"β": 0.2, "R": 2.0})) == [
        "The value 0.2 of β must belong to (0, E_{y}(y^2))."
    ]


def test_a_bound_that_names_a_parameter_valued_at_an_infinity_is_read_as_that_infinity():
    """The bound T of the set (0, T), with T declared on the extended reals
    and valued at inf, is read as inf: calibration accepts β = 0.2 and
    refuses β = -1."""
    # an infinite endpoint has one reading, whatever supplies its value: a
    # bound written as inf and a parameter valued at inf decide alike
    extended = stage_from_text(two_nodes_text_with_parameter_sets("β : (0, T)\nT : ℝ̄"))
    infinite = copy_native(extended).calibrate({"β": 0.2, "R": 2.0, "T": math.inf})
    assert undecided_memberships(infinite) == []
    assert "the value -1.0 lies outside the declared set (0, T)" in calibration_refusal_sentence(
        extended, {"β": -1.0, "R": 2.0, "T": math.inf}
    )


@pytest.fixture(scope="module")
def two_nodes_with_tol_bounded_by_n():
    """The two-node stage methodized by a methods text that declares the
    setting n and the setting tol, whose set has the bound 1/(n - 2)."""
    return two_nodes_stage_with_declared_sets("β : ℝ₊₊", "n : ℝ₊₊\ntol : (0, 1/(n-2))\n")


@pytest.fixture
def settings_mapping():
    """The settings n = 2 and tol = 0.5, as a mapping."""
    return {"n": 2.0, "tol": 0.5}


@pytest.fixture
def settings_file(tmp_path):
    """A settings file that writes the settings n = 2 and tol = 0.5."""
    settings = tmp_path / "settings.yml"
    settings.write_text("settings:\n  n: 2.0\n  tol: 0.5\n", encoding="utf-8")
    return settings


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("settings_mapping", id="a-mapping"),
        pytest.param("settings_file", id="a-settings-file"),
    ],
)
def test_a_bound_of_the_set_of_a_setting_refuses_the_configuration_only_where_it_has_no_value(
    request, two_nodes_with_tol_bounded_by_n, source
):
    """The bound 1/(n - 2) of the set of tol is valued at n = 3 and refuses
    the configuration at n = 2, given by a mapping or by a settings file,
    under `setting-outside-set`."""
    bounded = two_nodes_with_tol_bounded_by_n
    copy_native(bounded).configure({"n": 3.0, "tol": 0.5})
    with pytest.raises(ConstructionError) as refused:
        copy_native(bounded).configure(request.getfixturevalue(source))
    error = refused.value
    assert (error.rule, error.address) == ("setting-outside-set", "addition-1.bl:3")
    assert error.message == (
        "stage 'two_nodes', setting 'tol': the bound `1/(n - 2)` of the declared set "
        "(0, 1/(n - 2)) has no value at n = 2.0: "
        + ZERO.format("n - 2", "n = 2.0")
        + DEFINED
        + "write values at which `1/(n - 2)` has a value, or another bound"
    )


def test_the_refusal_of_a_settings_file_names_the_key_of_the_setting_that_the_bound_reads(
    two_nodes_with_tol_bounded_by_n, settings_file
):
    """The refusal of the settings file at n = 2 names, as its related
    place, the key n of that file, which the bound 1/(n - 2) reads."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(two_nodes_with_tol_bounded_by_n).configure(settings_file)
    # the role, the file, the line 2 and the column 3 at which the key n
    # stands under `settings:`, no end of the range, and the key's name
    key = ("rejected setting", str(settings_file), 2, 3, None, None, "n")
    assert tuple(refused.value.related[0]) == key


# The judgment of a recorded condition at an infinite value


# a derived parameter h written as its text, and h referred to by its
# identity
H_BY_TEXT = terms.Sym(terms.Constant("h"))


H_BY_IDENTITY = terms.Sym(terms.Constant(Identity("derived", stage="t", field="h")))


# values of the parameters at which h is infinite
INFINITE_H = {"h": math.inf, "R": 2.0}


@pytest.mark.parametrize(
    "written, answer",
    [
        pytest.param("ℝ_{+∞}", True, id="the-reals-with-inf"),
        pytest.param("ℝ", False, id="the-reals"),
        pytest.param("(0, inf]", True, id="an-interval-closed-at-inf"),
        pytest.param("(0, R]", False, id="an-interval-closed-at-a-parameter"),
        pytest.param("(0, 1/(R - 2)]", None, id="an-interval-whose-bound-has-no-value"),
        pytest.param("Foo", None, id="a-named-set-that-the-values-do-not-define"),
    ],
)
@pytest.mark.parametrize(
    "subject",
    [
        pytest.param(H_BY_TEXT, id="h-as-its-text"),
        pytest.param(H_BY_IDENTITY, id="h-by-its-identity"),
    ],
)
def test_predicate_value_decides_a_name_at_an_infinity_by_its_set_or_leaves_it_undecided(
    subject, written, answer
):
    """`predicate_value` judges the membership of h, valued at inf, in the
    set `written` by whether that set holds inf, decides nothing where a
    bound has no value or the set is not defined, and records that it read
    h."""
    judged = predicate_value(Member(subject, declared_set_of(f"β : {written}")), INFINITE_H)
    assert (judged.value, judged.read) == (answer, frozenset({"h"}))


@pytest.mark.parametrize(
    "predicate",
    [
        pytest.param(
            Member(terms.Add(H_BY_TEXT, terms.Number(1)), declared_set_of("β : ℝ̄")),
            id="a-sum-in-the-extended-reals",
        ),
        pytest.param(
            Compare(terms.Mul(terms.Number(2), H_BY_TEXT), ">", terms.Number(0)),
            id="a-product-compared-with-zero",
        ),
    ],
)
def test_arithmetic_that_reads_an_infinite_value_makes_its_predicate_false(predicate):
    """`predicate_value` judges a predicate whose arithmetic reads h, valued
    at inf, as false."""
    assert predicate_value(predicate, INFINITE_H).value is False
