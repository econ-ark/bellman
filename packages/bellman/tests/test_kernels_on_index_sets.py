"""The kernels that select an entry of a collection by a key of a finite
index set, a component by a label or a factor of a product by a position:
the parameters they read, the entry that each key selects, as the Python
function that `compile_kernel` returns and as that function compiled with
Numba, at keys beyond double precision and at the ends of the signed 64-bit
integers, the component of a shock with a component per key, and the
selection by a label of a draw that NumPy cannot convert or that JAX
traces. The index sets themselves and the calibration of the collections on
them are tested in test_index_sets.py."""

import functools
import inspect
import warnings

import numba
import numpy as np
import pytest
from skips import require_package
from stage_builders import stage_from_text
from stage_graphs import DECISION_PULLBACK, aggregation_box, pushforward_box
from stage_texts import (
    ADJACENT_CALIBRATION,
    ADJACENT_MEMBERS_TEXT,
    CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW,
    CHAIN_TEXT,
    JOINT_CHOICE,
    LOCATION_CALIBRATION_J2,
    LOCATION_CALIBRATION_J3,
    LOCATION_TEXT,
    POINTS_TEXT,
    changed,
    points_calibration,
)
from two_sets import one_row_by_default

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage.kernels import compile_kernel, kernel

# the points stage with its two members listed in the other order
POINTS_REORDERED = POINTS_TEXT.replace("S_θ := {0, θ} ⊂ ℤ", "S_θ := {θ, 0} ⊂ ℤ")


# the points stage on the integer range {θ, …, θ+1} of two keys
TWO_KEY_RANGE = POINTS_TEXT.replace("θ   : ℝ₊", "θ   : ℤ").replace("{0, θ} ⊂ ℤ", "{θ, …, θ+1}")


# three points stages whose second member is 2**53 + 1 at θ = 2**53 + 1: the
# members written as numbers, 2**53 and 2**53 + 1; the member written as a
# quotient of numbers; and the member written as a quotient of θ
WRITTEN_MEMBERS = POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{9007199254740992, 9007199254740993} ⊂ ℤ")
WRITTEN_QUOTIENT = POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{0, (9007199254740993/1)} ⊂ ℤ")
PARAMETER_QUOTIENT = POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{0, θ/1} ⊂ ℤ")


# A stage whose law of motion selects a component of a pair by a label, the
# draw of a shock on a declared set of two labels: the resources are
#     m = R·k + θ  where j = emp,   m = R·k + ξ_u  where j = unemp.
LABELLED = """@stage: labelled
Emp := {emp, unemp}
R   : ℝ₊₊
ξ_u : ℝ₊
p   : [0,1)
θ : ℝ₊₊
θ ~ LogNormal(0, 1)
j : Emp
j ~ Bernoulli(p)

[id=arvl_to_dcsn, (k : ℝ₊, θ, j) : !arvl -> (m : ℝ₊₊) : !dcsn] {
    m = R*k + (θ, ξ_u)[j]    :: [id=resources]
}
"""


# A stage whose law of motion selects the second factor of a parameter on a
# product by its position: y = a + x(2).
PAIR = """@stage: pair
x : ℝ × ℝ
[id=arvl_to_dcsn, (a : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = a + x[2]
}
"""


# the rows of the tests that compare the Python function of a kernel with
# that function compiled with Numba: the row python in the default set, and
# the row numba, which compiles for seconds, in the complete set
EVALUATORS = one_row_by_default(("python", "numba"))


class UnconvertibleValue:
    """A value NumPy cannot convert and arithmetic carries, as a value that
    JAX is tracing is: it holds a number or an array and has its shape,
    `np.asarray` of it raises `TypeError`, and its sum or its product with a
    number or an array is another such value."""

    __array_ufunc__ = None

    def __init__(self, held):
        self.held = held

    @property
    def shape(self):
        return np.shape(self.held)

    def __array__(self, dtype=None, copy=None):
        raise TypeError("this value has no array")

    def __add__(self, other):
        return UnconvertibleValue(self.held + getattr(other, "held", other))

    __radd__ = __add__

    def __mul__(self, other):
        return UnconvertibleValue(self.held * getattr(other, "held", other))

    __rmul__ = __mul__


@pytest.fixture(scope="module")
def value_line(location_stage):
    """The kernel of the value line of the symbolic location stage, by
    evaluator: the Python function that `compile_kernel` returns, and that
    function compiled with Numba, which compiles at its first call."""
    function = aggregation_box(location_stage).compile_kernel()
    return {"python": function, "numba": numba.njit(function)}


@pytest.fixture(scope="module")
def value_line_values(location_stage):
    """The parameter values of the value line at the two calibrations of
    copies of the location stage, by the value of J."""
    return {
        calibration["J"]: aggregation_box(copy_native(location_stage).calibrate(calibration))
        .kernel()
        .parameter_values
        for calibration in (LOCATION_CALIBRATION_J2, LOCATION_CALIBRATION_J3)
    }


@pytest.fixture(scope="module")
def law_of_motion(read_only_stage_from_text):
    """`law_of_motion(text, evaluator)`: the kernel of the law of motion of
    the arrival builder of a stage text, compiled on its symbolic stage: the
    Python function that `compile_kernel` returns where `evaluator` is
    "python", and that function compiled with Numba where it is "numba".
    Each function is made once for the module, so that Numba compiles it
    once for each type of its arguments."""

    @functools.cache
    def python_function(text):
        return pushforward_box(read_only_stage_from_text(text)).compile_kernel()

    @functools.cache
    def numba_function(text):
        return numba.njit(python_function(text))

    return lambda text, evaluator: {"python": python_function, "numba": numba_function}[evaluator](
        text
    )


@pytest.fixture(scope="module")
def law_values(read_only_stage_from_text):
    """`law_values(text, calibration)`: the parameter values of the law of
    motion of the arrival builder of a stage text, at a calibration of a copy
    of its symbolic stage."""
    return (
        lambda text, calibration: pushforward_box(
            copy_native(read_only_stage_from_text(text)).calibrate(calibration)
        )
        .kernel()
        .parameter_values
    )


@pytest.fixture(scope="module")
def labelled_law():
    """The law of motion of the labelled stage calibrated at R = 1.02,
    ξ_u = 0.3 and p = 0.05: its kernel record and the Python function that
    `compile_kernel` returns, whose arguments are k, θ and j and then the
    parameters R and ξ_u."""
    stage = stage_from_text(LABELLED, "labelled.bl").calibrate({"R": 1.02, "ξ_u": 0.3, "p": 0.05})
    law = pushforward_box(stage)
    return law.kernel(), law.compile_kernel()


@pytest.fixture(scope="module")
def jax():
    """The module jax, which the package does not require; a test that reads
    it is skipped where JAX is not installed."""
    return require_package("jax")


def test_the_kernel_of_a_value_line_writes_its_selections_from_collections(location_stage):
    """The kernel of the value line of the location stage writes the
    selections `δ[j]` and `dist[j][i_d]` as the stage file writes them."""
    record = aggregation_box(location_stage).kernel()
    assert "δ[j] - m_0 - m_1*dist[j][i_d]" in str(record)


@pytest.mark.parametrize(
    ("text", "box", "parameter"),
    [
        pytest.param(LOCATION_TEXT, aggregation_box, "J", id="the bound of a range"),
        pytest.param(POINTS_TEXT, pushforward_box, "θ", id="a member of a listed set"),
    ],
)
def test_a_kernel_reads_the_parameter_that_defines_the_index_set_of_its_collection(
    read_only_stage_from_text, text, box, parameter
):
    """A kernel that selects from a collection takes among its parameters
    the parameter that defines the collection's index set, although its line
    does not name that parameter."""
    record = box(read_only_stage_from_text(text)).kernel()
    assert parameter in record.parameters, record.parameters


def test_a_kernel_holds_parameter_values_only_on_a_calibrated_version(
    location_stage, value_line_values
):
    """The kernel of the value line holds no parameter values on the symbolic
    location stage, and holds them on each calibrated copy of it."""
    record = aggregation_box(location_stage).kernel()
    values_2, values_3 = value_line_values[2], value_line_values[3]
    assert record.parameter_values is None
    assert values_2 is not None and values_3 is not None


@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_one_kernel_compiled_on_the_symbolic_stage_evaluates_at_two_calibrations(
    value_line, value_line_values, evaluator
):
    """The kernel of the value line, compiled once on the symbolic location
    stage, gives the value at J = 2 and at J = 3 with the parameter values of
    each calibration."""
    function = value_line[evaluator]
    values_2, values_3 = value_line_values[2], value_line_values[3]
    # the arguments are V≻, i_d and j, then the parameters J, β, m_0, m_1, δ
    # and dist: V(1, 2) = δ(2) − m_0 − m_1·dist(2, 1) + β·10
    # = 2 − 0.5 − 2·1.5 + 0.9·10 = 7.5 at J = 2, and
    # V(1, 3) = 3 − 0.5 − 2·4 + 0.9·10 = 3.5 at J = 3
    assert float(function(10.0, 1, 2, *values_2)) == 7.5
    assert float(function(10.0, 1, 3, *values_3)) == 3.5


@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_the_kernel_of_the_value_line_evaluates_arrays_of_keys_entry_by_entry(
    value_line, value_line_values, evaluator
):
    """Given arrays of the keys i_d and j, the kernel of the value line gives
    the value at each pair of keys."""
    function = value_line[evaluator]
    values_2 = value_line_values[2]
    # the arguments are V≻, i_d and j, then the parameters: at J = 2,
    # V(1, 2) = 7.5 and V(2, 1) = 1 − 0.5 − 2·1.5 + 0.9·10 = 6.5
    assert function(10.0, np.array([1, 2]), np.array([2, 1]), *values_2).tolist() == [7.5, 6.5]


@pytest.mark.parametrize(
    "key", [pytest.param(3, id="beyond the range"), pytest.param(1.5, id="no integer")]
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_the_kernel_of_the_value_line_gives_no_value_at_a_key_outside_the_range(
    value_line, value_line_values, evaluator, key
):
    """At J = 2 the kernel of the value line gives a value at the key j = 2
    of the range {1, 2} and none where j lies outside the range."""
    function = value_line[evaluator]
    values_2 = value_line_values[2]
    # the arguments are V≻, i_d and j, then the parameters: V(1, 2) = 7.5
    assert float(function(10.0, 1, 2, *values_2)) == 7.5
    assert np.isnan(function(10.0, 1, key, *values_2))


@pytest.mark.parametrize(
    "member", [pytest.param(2, id="member 2"), pytest.param(5, id="member 5")]
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_a_key_of_a_listed_set_selects_the_entry_of_its_member_not_of_a_position(
    law_of_motion, law_values, evaluator, member
):
    """The key θ of the listed set {0, θ} selects the second entry of q and
    the key 0 the first, although θ = 2 or θ = 5 is no position of the two
    entries."""
    evaluate = law_of_motion(POINTS_TEXT, evaluator)
    values = law_values(POINTS_TEXT, points_calibration(member))
    assert (float(evaluate(member, *values)), float(evaluate(0, *values))) == (20.75, 10.25)


@pytest.mark.parametrize(
    ("text", "calibration", "keys", "entries"),
    [
        pytest.param(
            POINTS_TEXT,
            points_calibration(2),
            np.array([0, 2], dtype=np.int64),
            [10.25, 20.75],
            id="the members 0 and 2",
        ),
        pytest.param(
            POINTS_TEXT,
            points_calibration(5),
            np.array([0, 5], dtype=np.int64),
            [10.25, 20.75],
            id="the members 0 and 5",
        ),
        pytest.param(
            ADJACENT_MEMBERS_TEXT,
            ADJACENT_CALIBRATION,
            np.array([2**53, 2**53 + 1], dtype=np.int64),
            [10.25, 20.75],
            id="64-bit keys beyond double precision",
        ),
        pytest.param(
            ADJACENT_MEMBERS_TEXT,
            ADJACENT_CALIBRATION,
            np.array([2**53 + 1, 2**53], dtype=np.uint64),
            [20.75, 10.25],
            id="unsigned 64-bit keys in the other order",
        ),
        pytest.param(
            ADJACENT_MEMBERS_TEXT,
            ADJACENT_CALIBRATION,
            np.array([float(2**53)]),
            [10.25],
            id="a double that denotes a member",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**53 + 1, (10.0, 20.0)),
            np.array([2**53 + 1, 2**53 + 2], dtype=np.int64),
            [10.0, 20.0],
            id="a range beyond double precision",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**63 - 2),
            np.array([2**63 - 2, 2**63 - 1], dtype=np.int64),
            [10.25, 20.75],
            id="a range at the top of the 64-bit integers",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(-(2**63)),
            np.array([-(2**63), -(2**63) + 1], dtype=np.int64),
            [10.25, 20.75],
            id="a range at the bottom of the 64-bit integers",
        ),
    ],
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_an_array_of_keys_selects_the_entry_of_each_key_exactly(
    law_of_motion, law_values, evaluator, text, calibration, keys, entries
):
    """Given an array of keys, the kernel of a law of motion selects the
    entry of each key, at keys beyond double precision and at the ends of
    the 64-bit integers as at small keys."""
    evaluate = law_of_motion(text, evaluator)
    values = law_values(text, calibration)
    assert evaluate(keys, *values).tolist() == entries


# each row: a stage text and its calibration, a member and the entry that it
# selects, and a key that is no member
@pytest.mark.parametrize(
    ("text", "calibration", "member", "entry", "key"),
    [
        *[
            pytest.param(
                POINTS_TEXT,
                points_calibration(member),
                member,
                20.75,
                key,
                id=f"{name} at member {member}",
            )
            for member in (2, 5)
            for key, name in (
                (1, "an integer that is no member"),
                (1.5, "a number that is no integer"),
                (False, "a boolean"),
                (np.array([False, True]), "an array of booleans"),
            )
        ],
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**53 + 1, (10.0, 20.0)),
            2**53 + 1,
            10.0,
            False,
            id="a boolean on a range",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**53 + 1, (10.0, 20.0)),
            2**53 + 1,
            10.0,
            float(2**53 + 1),
            id="the double 2**53 below a range from 2**53 + 1",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**63 - 2),
            2**63 - 2,
            10.25,
            -(2**63),
            id="the lowest 64-bit integer on a range at the top",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(-(2**63)),
            -(2**63),
            10.25,
            2**63 - 1,
            id="the highest 64-bit integer on a range at the bottom",
        ),
        pytest.param(
            WRITTEN_QUOTIENT,
            points_calibration(2**53 + 1),
            2**53 + 1,
            20.75,
            float(2**53 + 1),
            id="the double 2**53 where a written quotient is 2**53 + 1",
        ),
        pytest.param(
            PARAMETER_QUOTIENT,
            points_calibration(2**53 + 1),
            2**53 + 1,
            20.75,
            float(2**53 + 1),
            id="the double 2**53 where a quotient of theta is 2**53 + 1",
        ),
    ],
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_a_key_that_is_no_member_selects_no_entry_where_a_member_selects_its_entry(
    law_of_motion, law_values, evaluator, text, calibration, member, entry, key
):
    """Where a member of the index set of a collection selects its entry, a
    key that is no member, an integer of no member, a number that is no
    integer, a boolean or the double of a member that is no member itself,
    gives no value, and an array of such keys gives none at each entry."""
    evaluate = law_of_motion(text, evaluator)
    values = law_values(text, calibration)
    assert float(evaluate(member, *values)) == entry
    assert np.isnan(evaluate(key, *values)).all()


@pytest.mark.parametrize(
    ("text", "calibration", "key", "entry"),
    [
        pytest.param(
            ADJACENT_MEMBERS_TEXT,
            ADJACENT_CALIBRATION,
            float(2**53),
            10.25,
            id="the double 2**53 on two members written with theta",
        ),
        pytest.param(
            WRITTEN_MEMBERS,
            points_calibration(2**53 + 1),
            float(2**53 + 1),
            10.25,
            id="the double of 2**53 + 1, which is 2**53, on two written members",
        ),
    ],
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_a_double_selects_the_entry_of_the_integer_that_it_denotes(
    law_of_motion, law_values, evaluator, text, calibration, key, entry
):
    """A key given as a double selects the entry of the integer that the
    double denotes: the double of 2**53 + 1 is 2**53."""
    evaluate = law_of_motion(text, evaluator)
    values = law_values(text, calibration)
    assert float(evaluate(key, *values)) == entry


@pytest.mark.parametrize(
    ("text", "calibration", "keys", "entries"),
    [
        pytest.param(
            ADJACENT_MEMBERS_TEXT,
            ADJACENT_CALIBRATION,
            (2**53, 2**53 + 1),
            (10.25, 20.75),
            id="two members written with theta",
        ),
        pytest.param(
            TWO_KEY_RANGE,
            points_calibration(2**53 + 1, (10.0, 20.0)),
            (2**53 + 1, 2**53 + 2),
            (10.0, 20.0),
            id="a range",
        ),
        pytest.param(
            WRITTEN_MEMBERS,
            points_calibration(2**53 + 1),
            (2**53, 2**53 + 1),
            (10.25, 20.75),
            id="two written members",
        ),
        pytest.param(
            WRITTEN_QUOTIENT,
            points_calibration(2**53 + 1),
            (0, 2**53 + 1),
            (10.25, 20.75),
            id="a member written as a quotient of numbers",
        ),
        pytest.param(
            PARAMETER_QUOTIENT,
            points_calibration(2**53 + 1),
            (0, 2**53 + 1),
            (10.25, 20.75),
            id="a member written as a quotient of theta",
        ),
    ],
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_each_key_beyond_double_precision_selects_its_own_entry(
    law_of_motion, law_values, evaluator, text, calibration, keys, entries
):
    """A key beyond double precision, such as 2**53 + 1, which a double would
    round to 2**53, selects its own entry, whether the index set is a range
    or lists its members with θ, as numbers or as quotients."""
    evaluate = law_of_motion(text, evaluator)
    values = law_values(text, calibration)
    assert (float(evaluate(keys[0], *values)), float(evaluate(keys[1], *values))) == entries


# Numba cannot compile the kernel's conversion of a complex key to a 64-bit
# integer, so this test has no row that compiles with Numba
@pytest.mark.parametrize("key", [pytest.param(0 + 0j, id="0+0j"), pytest.param(2 + 0j, id="2+0j")])
def test_a_complex_key_selects_no_entry_where_the_integer_key_2_selects_one(
    law_of_motion, law_values, key
):
    """At θ = 2 the integer key 2 selects its entry, and a complex key
    selects none, even where its imaginary part is zero and its real part, 0
    or 2, is a member: the kernel gives no value and does not discard the
    imaginary part, which would raise NumPy's warning."""
    function = law_of_motion(POINTS_TEXT, "python")
    values = law_values(POINTS_TEXT, points_calibration(2))
    assert float(function(2, *values)) == 20.75
    with warnings.catch_warnings():
        warnings.simplefilter("error", np.exceptions.ComplexWarning)
        assert np.isnan(function(key, *values))


# each row: the index expression, a value of θ at which the expression lies
# within the signed 64-bit integers and the key it then equals, a value of θ
# at which it lies outside them, and a key to evaluate there, the integer that
# the expression would wrap to in 64-bit arithmetic or the other member 0
@pytest.mark.parametrize(
    ("expression", "safe_parameter", "safe_key", "parameter", "key"),
    [
        pytest.param("θ+1", 1, 2, 2**63 - 1, -(2**63), id="theta+1 at the wrapped key"),
        pytest.param("θ+1", 1, 2, 2**63 - 1, 0, id="theta+1 at the key 0"),
        pytest.param("θ-1", 2, 1, -(2**63), 2**63 - 1, id="theta-1 at the wrapped key"),
        pytest.param("θ-1", 2, 1, -(2**63), 0, id="theta-1 at the key 0"),
        pytest.param("-θ", 1, -1, -(2**63), -(2**63), id="-theta at the wrapped key"),
        pytest.param("-θ", 1, -1, -(2**63), 0, id="-theta at the key 0"),
        pytest.param("θ*2", 2, 4, 2**62, -(2**63), id="theta*2 at the wrapped key"),
        pytest.param("θ*2", 2, 4, 2**62, 0, id="theta*2 at the key 0"),
        pytest.param("θ^2", 2, 4, 2**32, 0, id="theta^2 at the wrapped key 0"),
    ],
)
@pytest.mark.parametrize("evaluator", EVALUATORS)
def test_an_index_expression_selects_its_entry_within_64_bit_arithmetic_and_raises_outside_it(
    law_of_motion, law_values, evaluator, expression, safe_parameter, safe_key, parameter, key
):
    """A listed member written as arithmetic of θ selects its entry where the
    arithmetic stays within the signed 64-bit integers, and the kernel raises
    `ValueError` at every key where it does not, so that no wrapped integer
    is taken for a key."""
    text = POINTS_TEXT.replace("θ   : ℝ₊", "θ   : ℤ").replace(
        "{0, θ} ⊂ ℤ", f"{{{expression}, 0}} ⊂ ℤ"
    )
    evaluate = law_of_motion(text, evaluator)
    safe_values = law_values(text, points_calibration(safe_parameter, (20.75, 10.25)))
    invalid_values = law_values(text, points_calibration(parameter, (20.75, 10.25)))
    assert float(evaluate(safe_key, *safe_values)) == 20.75
    with pytest.raises(ValueError):
        evaluate(key, *invalid_values)


def test_the_law_of_motion_reads_the_component_of_a_vector_shock_at_the_drawn_key(
    read_only_stage_from_text,
):
    """At J = 2 the law of motion of the chain stage reads the component of
    ε at the drawn state e_n."""
    at_2 = copy_native(read_only_stage_from_text(CHAIN_TEXT)).calibrate(
        CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW
    )
    law = pushforward_box(at_2).compile_kernel()
    values = pushforward_box(at_2).kernel().parameter_values
    # the arguments are e_c = 1, e_n = 2 and ε = (0, 1, 2), then the
    # parameters; the first output is x = ε(e_n) = ε(2) = 2
    drawn = law(1, 2, np.array([0.0, 1.0, 2.0]), *values)
    assert float(drawn[0]) == 2.0


def test_reordering_the_members_and_the_entries_together_keeps_the_entry_of_each_key():
    """The listed set {θ, 0}, with the entries of q given in that order,
    selects 20.75 at the key 5 and 10.25 at the key 0, as {0, θ} does with
    the entries in its order."""
    reordered = stage_from_text(POINTS_REORDERED, "points.bl").calibrate(
        {"θ": 5, "β": 0.9, "q": [20.75, 10.25]}
    )
    reordered_box = pushforward_box(reordered)
    reordered_function = reordered_box.compile_kernel()
    values = reordered_box.kernel().parameter_values
    assert (float(reordered_function(5, *values)), float(reordered_function(0, *values))) == (
        20.75,
        10.25,
    )


def test_the_kernel_compiles_theta_over_one_and_refuses_theta_over_two_plus_theta_over_two(
    law_of_motion,
    law_values,
):
    """The kernel of the law of motion compiles the member θ/1, which
    selects its entry, and refuses under `kernel-form` the member
    θ/2 + θ/2, an integer wherever θ is, rather than round a quotient."""
    function = law_of_motion(PARAMETER_QUOTIENT, "python")
    values = law_values(PARAMETER_QUOTIENT, points_calibration(3))
    # the argument is the key θ/1 = 3, then the parameters
    assert float(function(3, *values)) == 20.75
    divided = stage_from_text(
        POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{0, θ/2 + θ/2} ⊂ ℤ"), "divided-index.bl"
    )
    with pytest.raises(ConstructionError) as division:
        pushforward_box(divided).compile_kernel()
    assert division.value.rule == "kernel-form"


def test_a_position_selects_a_factor_of_a_product_and_a_fractional_position_is_refused():
    """In `y = a + x[2]` with `x : ℝ × ℝ` the position 2 selects the second
    factor, and the position 2.5 is refused under `syntax`, with a message
    that names it."""
    second = stage_from_text(PAIR, "pair.bl").calibrate({"x": [1.0, 5.0]})
    law = pushforward_box(second)
    # the argument is a = 1, then the parameter x = (1, 5): y = 1 + 5 = 6
    assert float(law.compile_kernel()(1.0, *law.kernel().parameter_values)) == 6.0
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(PAIR.replace("x[2]", "x[2.5]"), "pair.bl")
    message = refused.value.message
    assert refused.value.rule == "syntax" and "`2.5`, which is no whole number" in message


def test_a_selection_by_the_label_of_a_parameter_compares_the_parameter_with_the_label(
    benhabib_stage,
):
    """The kernel of the law of motion of the decision builder of the stage
    file of the application benhabib-2019, whose wage is selected by the
    label `tau`, compares `tau` with the label `q1`."""
    law = pushforward_box(benhabib_stage, "dcsn_to_cntn")
    assert "np.asarray(tau) == 'q1'" in law.kernel().python


@pytest.mark.parametrize(
    ("text", "written", "present"),
    [
        pytest.param(
            LABELLED,
            "where_label(np.asarray(j) == 'emp', θ, "
            "where_label(np.asarray(j) == 'unemp', ξ_u, np.nan))",
            True,
            id="a selection by the label of a shock",
        ),
        pytest.param(POINTS_TEXT, "where_label", False, id="a selection by an integer key"),
    ],
)
def test_a_selection_by_a_label_is_written_through_where_label_and_one_by_an_integer_key_is_not(
    read_only_stage_from_text, text, written, present
):
    """The kernel of a law of motion writes a selection by a label through
    its inner function `where_label`, once for each label of the set, and
    writes a selection by an integer key without `where_label`, so that
    Numba compiles that kernel."""
    python = pushforward_box(read_only_stage_from_text(text)).kernel().python
    assert (written in python) == present


@pytest.mark.parametrize(
    ("draw", "label", "resources"),
    [
        pytest.param(0.9, "emp", 1.92, id="emp selects the draw"),
        pytest.param(0.9, "unemp", 1.32, id="unemp selects the income"),
        pytest.param(
            UnconvertibleValue(0.9),
            "unemp",
            1.32,
            id="unemp beside a draw that NumPy cannot convert",
        ),
    ],
)
def test_a_label_selects_its_component_of_the_pair(labelled_law, draw, label, resources):
    """The label j selects θ or ξ_u from the pair (θ, ξ_u): with R = 1.02
    and ξ_u = 0.3, m(1, 0.9, emp) = 1.02 + 0.9 = 1.92 and
    m(1, 0.9, unemp) = 1.02 + 0.3 = 1.32."""
    record, function = labelled_law
    values = record.parameter_values
    # the arguments are k, θ and j, then the parameters R and ξ_u
    assert values == (1.02, 0.3)
    assert float(function(1.0, draw, label, *values)) == pytest.approx(resources)


@pytest.mark.parametrize(
    ("draw", "shape"),
    [
        pytest.param(0.9, (), id="a number"),
        pytest.param(UnconvertibleValue(0.9), (), id="a value that NumPy cannot convert"),
        pytest.param(
            UnconvertibleValue(np.array([0.8, 1.0, 1.2])),
            (3,),
            id="three values that NumPy cannot convert",
        ),
    ],
)
def test_a_label_of_neither_name_gives_no_value_where_unemp_gives_the_income(
    labelled_law, draw, shape
):
    """Where the label unemp gives the resources 1.02 + 0.3 = 1.32, a label
    that is neither emp nor unemp gives no value, at the shape of the draw
    of θ."""
    record, function = labelled_law
    values = record.parameter_values
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    assert np.allclose(function(1.0, draw, "unemp", *values), 1.32)
    neither = function(1.0, draw, "neither", *values)
    assert np.shape(neither) == shape and np.isnan(neither).all()


# the stage of `JOINT_CHOICE` with a state z on the declared set
# Z := {low, high} and the parameter `prices` on ℝ × ℝ, whose law of motion
# a = x_d + prices[z_d] + u[1] selects one of the two prices by the label of z
PRICE_BY_LABEL = (
    JOINT_CHOICE.replace(
        "@stage: joint_choice", "@stage: joint_choice\nZ := {low, high}\nprices : ℝ × ℝ"
    )
    .replace("(x : ℝ) : !arvl -> (x_d : ℝ)", "(x : ℝ, z : Z) : !arvl -> (x_d : ℝ, z_d : Z)")
    .replace(" x_d = x", " x_d = x\n z_d = z")
    .replace("(x_d, u :", "(x_d, z_d, u :")
    .replace("x_d + u[1] + u[2]", "x_d + prices[z_d] + u[1]")
)


@pytest.fixture(scope="module")
def stage_selecting_a_price_by_label():
    """The stage of `PRICE_BY_LABEL`, calibrated at prices = (5, 7)."""
    return stage_from_text(PRICE_BY_LABEL).calibrate({"prices": (5, 7)})


def test_a_selection_by_label_compiles_to_a_function_of_the_label_and_of_the_prices(
    stage_selecting_a_price_by_label,
):
    """The compiled law of motion takes the label coordinate z_d among the
    arguments of its kernel, then the parameter `prices` on ℝ × ℝ as one
    argument."""
    law = compile_kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)
    assert str(inspect.signature(law)) == "(x_d, z_d, u, prices)"


def test_the_kernel_of_a_selection_by_label_does_not_list_the_label_as_unused(
    stage_selecting_a_price_by_label,
):
    """The printed kernel of the law of motion does not list the label
    coordinate z_d among the arguments that it does not use."""
    assert "unused z_d" not in kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)


@pytest.mark.parametrize(
    ("arguments", "value"),
    [
        # x_d = [10, 20], z_d = [high, low] and u = [(1, 2), (3, 4)]:
        # 10 + 7 + 1 and 20 + 5 + 3
        pytest.param(
            (np.array([10, 20]), ["high", "low"], [[1, 2], [3, 4]]),
            [18, 28],
            id="declared labels at an array of points",
        ),
        # a label that Z does not declare: the function checks no label, so
        # it selects no price, and NumPy gives NaN
        pytest.param((10, "missing", (1, 2)), np.nan, id="a label outside the declared set"),
    ],
)
def test_a_compiled_selection_by_label_selects_the_price_of_each_label_and_none_for_another_label(
    stage_selecting_a_price_by_label, arguments, value
):
    """The compiled law of motion selects, at each point of an array of
    labels, the price that the label names, at prices = (5, 7), and no
    price, that is NaN, for a label that Z does not declare."""
    law = compile_kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)
    held = kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)
    result = law(*arguments, *held.parameter_values)
    assert np.shape(result) == np.shape(value)
    np.testing.assert_array_equal(result, value)


def test_a_compiled_selection_compares_the_labels_in_the_order_of_their_declared_set(
    stage_selecting_a_price_by_label,
):
    """The Python text of the law of motion compares z_d with `low` before
    `high`, the order in which Z := {low, high} declares them."""
    text = kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK).python
    assert text.index("np.asarray(z_d) == 'low'") < text.index("np.asarray(z_d) == 'high'")


def test_a_new_calibration_passes_new_prices_to_the_compiled_selection(
    stage_selecting_a_price_by_label,
):
    """At prices = (50, 70) the kernel keeps the text that it has at
    prices = (5, 7), and its values, passed to the function compiled at
    the first prices, select a new price."""
    held = kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)
    law = compile_kernel(stage_selecting_a_price_by_label, DECISION_PULLBACK)
    recalibrated = copy_native(stage_selecting_a_price_by_label).calibrate({"prices": (50, 70)})
    again = kernel(recalibrated, DECISION_PULLBACK)
    assert held.parameter_values == ((5, 7),)
    assert again.python == held.python
    # x_d = 10, z_d = high and u = (1, 2): 10 + 70 + 1 at the second prices
    # and 10 + 7 + 1 at the first
    assert (
        float(law(10, "high", (1, 2), *again.parameter_values)),
        float(law(10, "high", (1, 2), *held.parameter_values)),
    ) == (81, 18)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(
            changed(PRICE_BY_LABEL, ("prices : ℝ × ℝ", "Prices := ℝ × ℝ\nprices : Prices")),
            id="prices-on-a-named-set",
        ),
        pytest.param(
            changed(
                changed(
                    PRICE_BY_LABEL,
                    ("prices : ℝ × ℝ", "prices : ℝ × ℝ\nprice(state : Z) := prices[state]"),
                ),
                ("prices[z_d]", "price(z_d)"),
            ),
            id="prices-read-by-a-function-of-the-label",
        ),
    ],
)
def test_a_selection_compiles_where_the_prices_have_a_named_set_or_a_function_reads_them(text):
    """The law of motion compiles to the same selection where the set of
    `prices` is named, and where a function of the label reads them."""
    stage = stage_from_text(text).calibrate({"prices": (5, 7)})
    # x_d = 10, z_d = high, u = (1, 2) and prices = (5, 7): 10 + 7 + 1
    assert float(compile_kernel(stage, DECISION_PULLBACK)(10, "high", (1, 2), (5, 7))) == 18


@pytest.mark.parametrize(
    "draws",
    [
        pytest.param(np.array([0.8, 1.0, 1.2]), id="three numbers"),
        pytest.param(
            UnconvertibleValue(np.array([0.8, 1.0, 1.2])),
            id="three values that NumPy cannot convert",
        ),
    ],
)
def test_the_component_that_a_label_does_not_select_gives_the_result_its_shape(
    labelled_law, draws
):
    """Three draws of θ at the label unemp give an array of three resources
    of 1.02 + 0.3 = 1.32, although the label selects ξ_u and not θ;
    `np.testing.assert_allclose` fails where a resource differs."""
    record, function = labelled_law
    values = record.parameter_values
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    unemployed = function(1.0, draws, "unemp", *values)
    assert isinstance(unemployed, np.ndarray) and unemployed.shape == (3,)
    np.testing.assert_allclose(unemployed, 1.32)


def test_an_array_of_labels_selects_at_each_point(labelled_law):
    """Arrays of k, θ and labels give at each point the component that its
    label selects, (1.02·1 + 0.8, 1.02·2 + 0.3) = (1.82, 2.34);
    `np.testing.assert_allclose` fails where a resource differs."""
    record, function = labelled_law
    values = record.parameter_values
    np.testing.assert_allclose(
        function(np.array([1.0, 2.0]), np.array([0.8, 1.2]), np.array(["emp", "unemp"]), *values),
        [1.82, 2.34],
    )


@pytest.mark.parametrize(
    ("draw", "label", "shape", "resources"),
    [
        pytest.param(UnconvertibleValue(0.9), "emp", (), 1.92, id="one value at one label"),
        pytest.param(
            UnconvertibleValue(np.array([0.8, 1.0, 1.2])),
            "emp",
            (3,),
            [1.82, 2.02, 2.22],
            id="three values at one label",
        ),
        pytest.param(
            UnconvertibleValue(0.9),
            np.array(["emp"]),
            (1,),
            [1.92],
            id="one value at an array of one label",
        ),
    ],
)
def test_a_label_that_selects_a_draw_numpy_cannot_convert_returns_such_a_value(
    labelled_law, draw, label, shape, resources
):
    """Where the label emp selects a draw that NumPy cannot convert, as a
    value that JAX is tracing is, the kernel returns the resources as such a
    value, at the common shape of the operands; `np.testing.assert_allclose`
    fails where a resource differs."""
    record, function = labelled_law
    # the arguments are k = 1, θ and j, then the parameters R = 1.02 and ξ_u:
    # m = 1.02 + 0.9 = 1.92 at the draw 0.9
    carried = function(1.0, draw, label, *record.parameter_values)
    assert isinstance(carried, UnconvertibleValue) and carried.shape == shape
    np.testing.assert_allclose(carried.held, resources)


def test_an_array_of_labels_refuses_a_draw_numpy_cannot_convert_that_one_label_carries(
    labelled_law,
):
    """Where one label carries a draw that NumPy cannot convert, an array of
    two labels converts the operands as `np.where` does, so that the same
    draw raises the `TypeError` of its conversion."""
    record, function = labelled_law
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    carried = function(1.0, UnconvertibleValue(0.9), "emp", *record.parameter_values)
    assert isinstance(carried, UnconvertibleValue)
    with pytest.raises(TypeError, match="no array"):
        function(
            1.0, UnconvertibleValue(0.9), np.array(["emp", "unemp"]), *record.parameter_values
        )


@pytest.mark.parametrize("label", ["emp", "unemp"])
def test_the_kernel_mapped_by_jax_over_draws_gives_the_resources_that_numpy_gives(
    jax, labelled_law, label
):
    """`jax.vmap` of the kernel of the labelled law of motion, with the label
    fixed, over three draws of θ gives the resources that the kernel gives
    for the array of the three draws; `np.testing.assert_allclose` fails
    where a resource differs."""
    record, function = labelled_law
    values = record.parameter_values
    draws = np.array([0.8, 1.0, 1.2])
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    np.testing.assert_allclose(
        jax.vmap(lambda draw: function(1.0, draw, label, *values))(draws),
        function(1.0, draws, label, *values),
        rtol=1e-6,
    )


def test_the_kernel_compiled_by_jax_at_one_label_gives_the_resources_that_numpy_gives(
    jax, labelled_law
):
    """`jax.jit` of the kernel of the labelled law of motion at the label emp
    gives m(1, 0.9, emp) = 1.02 + 0.9 = 1.92."""
    record, function = labelled_law
    values = record.parameter_values
    compiled = jax.jit(lambda k, draw: function(k, draw, "emp", *values))
    assert float(compiled(1.0, 0.9)) == pytest.approx(1.92)


@pytest.mark.parametrize("label", ["emp", "unemp", "neither"])
def test_the_kernel_compiled_by_jax_for_an_array_of_draws_gives_the_array_that_numpy_gives(
    jax, labelled_law, label
):
    """`jax.jit` of the kernel of the labelled law of motion, with the label
    fixed and given the three draws of θ as one array, gives the three
    resources that NumPy gives, or three entries with no value at a label of
    neither name."""
    record, function = labelled_law
    values = record.parameter_values
    draws = np.array([0.8, 1.0, 1.2])
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    traced = jax.jit(lambda draw: function(1.0, draw, label, *values))(draws)
    assert traced.shape == (3,)
    np.testing.assert_allclose(traced, function(1.0, draws, label, *values), rtol=1e-6)


@pytest.mark.parametrize(
    ("label", "derivative"),
    [
        pytest.param("emp", 1.0, id="emp selects the draw"),
        pytest.param("unemp", 0.0, id="unemp selects the income"),
    ],
)
def test_the_derivative_that_jax_takes_in_the_draw_is_one_where_the_label_selects_the_draw(
    jax, labelled_law, label, derivative
):
    """`jax.grad` of the kernel of the labelled law of motion in θ is one at
    the label emp, which selects θ, and zero at unemp, which selects ξ_u."""
    record, function = labelled_law
    values = record.parameter_values
    # the arguments are k = 1, θ and j, then the parameters R and ξ_u
    assert float(jax.grad(lambda draw: function(1.0, draw, label, *values))(0.9)) == derivative
