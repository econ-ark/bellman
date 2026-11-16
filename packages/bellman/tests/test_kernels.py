"""The kernel of an operation and the function compiled from it: what
`kernel()` prints, the arguments and the values of the function that
`compile_kernel()` makes, arrays and products of sets, the kernels
of the policy builder, closed forms of certainty equivalents, and JAX. The
record of a builder's kernels, the operations that compile to no function,
the text of a kernel in another version, Numba and pickle stand in
test_kernel_records_numba_and_pickle.py."""

import functools
import inspect
import math
import types

import numpy
import pytest
from application_files import (
    BUFFER_STOCK_BASELINE_CALIBRATION,
    CONS_METHODS,
    CORPUS,
    FIRST_CALIBRATIONS,
    MARKET_RESOURCES,
    SA_SAVINGS_CALIBRATIONS,
    consumption_at_human_wealth,
)
from skips import require_package
from stage_builders import boxes_inside_bubble, stage_from_text
from stage_graphs import DECISION_PULLBACK
from stage_texts import (
    BUFFER_STOCK_XA_DEFINITION,
    EGM_LINES,
    HUMAN_WEALTH_DEFINITION,
    JOINT_CHOICE,
    Y_IDENTITY,
    buffer_stock_text_with_changes,
    changed,
    cons_text_with_policy_lines,
    corpus_text,
    two_nodes_text_with_changes,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import EXPLICIT_POLICY
from bellman.refusals import ConstructionError
from bellman.stage.boxes import kind_of
from bellman.stage.denotations import card
from bellman.stage.grains import operators_of
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax import terms
from bellman.typing import typed_expressions

# the aggregation of the backward decision builder, which applies the
# aggregator 𝐺; a compiled kernel writes the continuation value V≻ as the
# Python name V_cntn
DECISION_AGGREGATION = "cntn_to_dcsn:Aggregation"


@pytest.fixture(scope="module")
def cons_at_rho_two(cons):
    """A copy of the consumption stage without methods, calibrated at
    ρ = 2."""
    return copy_native(cons).calibrate({"ρ": 2.0})


@pytest.fixture(scope="module")
def cons_at_rho_three(cons):
    """A copy of the consumption stage without methods, calibrated at
    ρ = 3."""
    return copy_native(cons).calibrate({"ρ": 3.0})


@pytest.mark.parametrize(
    ("operation", "printed"),
    [
        pytest.param(DECISION_PULLBACK, "𝑔 of dcsn_to_cntn: 𝑔(m_d, c) = m_d - c", id="pullback"),
        pytest.param(
            DECISION_AGGREGATION,
            "𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻\noutput V; unused m_d",
            id="aggregation",
        ),
    ],
)
def test_the_kernel_of_an_operation_prints_the_function_that_the_operation_applies(
    cons_at_rho_two, operation, printed
):
    """`kernel` prints the function that an operation applies, with its
    arguments: the law of motion of a pullback, the aggregator of an
    aggregation."""
    assert kernel(cons_at_rho_two, operation) == printed


@pytest.mark.parametrize(
    ("operation", "signature", "parameters"),
    [
        pytest.param(DECISION_PULLBACK, "(m_d, c)", (), id="pullback"),
        pytest.param(DECISION_AGGREGATION, "(V_cntn, m_d, c, ρ)", ("ρ",), id="aggregation"),
    ],
)
def test_a_compiled_kernel_takes_the_arguments_of_its_kernel_then_the_parameters_it_reads(
    cons_at_rho_two, operation, signature, parameters
):
    """The function compiled from a kernel takes the arguments of the
    printed kernel, in their order, then the parameters that the kernel
    names under `parameters`."""
    assert str(inspect.signature(compile_kernel(cons_at_rho_two, operation))) == signature
    assert kernel(cons_at_rho_two, operation).parameters == parameters


@pytest.mark.parametrize(
    ("operation", "arguments", "value"),
    [
        # (m_d, c) = (2, 0.5): the saving m_d - c
        pytest.param(DECISION_PULLBACK, (2, 0.5), 1.5, id="pullback"),
        # (V≻, m_d, c, ρ) = (4, 2, 0.5, 2): 𝑢(0.5) + 4 = 0.5^(-1)/(-1) + 4
        pytest.param(DECISION_AGGREGATION, (4, 2, 0.5, 2.0), 2.0, id="aggregation"),
    ],
)
def test_a_compiled_kernel_gives_the_value_of_the_function_that_its_operation_applies(
    cons_at_rho_two, operation, arguments, value
):
    """The function compiled from a kernel gives at a point the value of
    the law of motion of a pullback or of the aggregator of an
    aggregation."""
    assert float(compile_kernel(cons_at_rho_two, operation)(*arguments)) == value


def test_a_compiled_kernel_computes_with_python_integers_by_pythons_own_arithmetic(
    cons_at_rho_two,
):
    """The compiled aggregator computes with Python integers, given as its
    arguments and as the value of ρ, by Python's own arithmetic."""
    # (V≻, m_d, c, ρ) = (4, 2, 1, 2): 𝑢(1) + 4 = 1**(-1)/(-1) + 4; NumPy
    # refuses an integer to a negative integer power, so a function that
    # made arrays of its arguments would raise here
    assert float(compile_kernel(cons_at_rho_two, DECISION_AGGREGATION)(4, 2, 1, 2)) == 3.0


def test_the_comment_lines_of_a_kernels_text_name_its_stage_file_output_sets_and_names(
    cons, cons_at_rho_two
):
    """The comment lines of a kernel's Python text name the stage and the
    operation, the stage file with the digest of its text, the output, the
    declared set of each parameter and the Python name given to each name
    of the file."""
    phrases = [
        "cons, cntn_to_dcsn:Aggregation",
        "cons.bl sha256 " + cons.provenance["sha256"],
        "output V",
        "ρ ∈ [1, inf)",
        "V_cntn is V≻",
        "u is 𝑢",
    ]
    text = kernel(cons_at_rho_two, DECISION_AGGREGATION).python
    assert [phrase for phrase in phrases if phrase not in text] == []


def test_compile_kernel_given_the_box_of_an_operation_compiles_the_kernel_of_that_operation(
    cons_at_rho_two,
):
    """`compile_kernel` given the box of the decision aggregation, in place
    of its name, compiles the aggregator."""
    box = next(box for box in operators_of(cons_at_rho_two) if box.name == DECISION_AGGREGATION)
    # (V≻, m_d, c, ρ) = (4, 2, 0.5, 2): 𝑢(0.5) + 4 = -2 + 4
    assert float(compile_kernel(cons_at_rho_two, box)(4, 2, 0.5, 2.0)) == 2.0


def test_a_changed_law_of_motion_gives_the_pullback_a_new_kernel(cons_at_rho_two):
    """The law of motion written a = (m_d - c)/2 gives the decision
    pullback a new kernel: its print, its Python text and its function
    follow the new law."""
    text = changed(corpus_text("cons"), ("    a = m_d - c\n", "    a = (m_d - c)/2\n"))
    halved = stage_from_text(text, "cons.bl").calibrate({"ρ": 2.0})
    assert kernel(halved, DECISION_PULLBACK) == "𝑔 of dcsn_to_cntn: 𝑔(m_d, c) = (m_d - c)/2"
    assert (
        kernel(halved, DECISION_PULLBACK).python
        != kernel(cons_at_rho_two, DECISION_PULLBACK).python
    )
    # (m_d, c) = (2, 0.5): (2 - 0.5)/2 under the changed law, 2 - 0.5
    # under the law of cons.bl
    assert (
        float(compile_kernel(halved, DECISION_PULLBACK)(2, 0.5)),
        float(compile_kernel(cons_at_rho_two, DECISION_PULLBACK)(2, 0.5)),
    ) == (0.75, 1.5)


def test_a_new_calibration_passes_its_values_to_the_function_already_made(
    cons_at_rho_two, cons_at_rho_three
):
    """At ρ = 3 the aggregation's kernel keeps the text that it has at
    ρ = 2 and holds the new value, which the function made at ρ = 2 takes
    as its last argument."""
    aggregator = compile_kernel(cons_at_rho_two, DECISION_AGGREGATION)
    again = kernel(cons_at_rho_three, DECISION_AGGREGATION)
    assert again.python == kernel(cons_at_rho_two, DECISION_AGGREGATION).python
    assert again.parameter_values == (3.0,)
    # (V≻, m_d, c) = (4, 2, 1): 𝑢(1) + 4 = 1/(1 - ρ) + 4, which is 3.5 at
    # ρ = 3 and 3 at ρ = 2
    assert float(aggregator(4, 2, 1, *again.parameter_values)) == 3.5
    assert float(aggregator(4, 2, 1, 2.0)) == 3.0


def test_a_symbolic_kernel_has_the_text_and_parameters_of_a_calibrated_one_and_no_values(
    cons, cons_at_rho_three
):
    """The aggregation's kernel on the symbolic consumption stage has the
    Python text and the parameters that it has on a calibrated copy, and no
    parameter values."""
    symbolic = kernel(cons, DECISION_AGGREGATION)
    calibrated = kernel(cons_at_rho_three, DECISION_AGGREGATION)
    assert (symbolic.python, symbolic.parameters, symbolic.parameter_values) == (
        calibrated.python,
        ("ρ",),
        None,
    )


def test_a_symbolic_version_compiles_a_function_that_takes_its_parameter_values_from_the_caller(
    cons,
):
    """The symbolic consumption stage compiles its aggregation to a
    function that takes the value of ρ from its caller."""
    # (V≻, m_d, c, ρ) = (4, 2, 1, 3): 𝑢(1) + 4 = 1/(1 - 3) + 4
    assert float(compile_kernel(cons, DECISION_AGGREGATION)(4, 2, 1, 3.0)) == 3.5


def test_a_compiled_kernel_broadcasts_arrays_and_numpy_refuses_shapes_that_do_not_broadcast(
    cons_at_rho_two,
):
    """The compiled aggregator follows NumPy's broadcasting, and NumPy
    itself refuses arrays whose shapes do not broadcast, since the function
    checks no shape."""
    aggregator = compile_kernel(cons_at_rho_two, DECISION_AGGREGATION)
    # (V≻, m_d, c, ρ) = ([4, 5], 2, 0.5, 2): 𝑢(0.5) + V≻ = -2 + V≻
    value = aggregator(numpy.array([4.0, 5.0]), 2.0, 0.5, 2.0)
    assert (numpy.shape(value), value.tolist()) == ((2,), [2.0, 3.0])
    # V≻ at two points and c at three
    with pytest.raises(ValueError, match="could not be broadcast"):
        aggregator(numpy.ones(2), 2.0, numpy.ones(3), 2.0)


def test_a_compiled_kernel_given_numbers_returns_a_number(cons_at_rho_two):
    """The compiled law of motion given two floats returns a float, the
    saving."""
    # (m_d, c) = (2, 0.5): the saving 2 - 0.5
    saved = compile_kernel(cons_at_rho_two, DECISION_PULLBACK)(2.0, 0.5)
    assert isinstance(saved, float) and saved == 1.5


@pytest.fixture(scope="module")
def cons_obs_with_resources_in_its_value():
    """The consumption stage `cons_obs.bl`, whose policy block states the
    borrowing constraint by a multiplier, with its value line written
    V = m_d*𝑢(c) + V[>], which reads the decision state m_d that the header
    of its block does not list, calibrated at ρ = 2."""
    text = changed(
        corpus_text("cons_obs"), ("V        = 𝑢(c) + V[>]", "V        = m_d*𝑢(c) + V[>]")
    )
    return stage_from_text(text, "cons_obs.bl").calibrate({"ρ": 2})


# a stage whose decision value V = m*V[>] reads the decision state m, and
# whose arrival value V[<] = E_{ε}(m*V) reads it through the law of motion
# m = k*b + ε
VALUE_TIMES_STATE = (
    "@stage: target_read\n\nk : ℝ₊₊\n\nε : ℝ\nε ~ N(0, 1)\n\n"
    "[id=arvl_to_dcsn, (b : ℝ, ε) : !arvl -> (m : ℝ) : !dcsn] {\n    m = k*b + ε\n}\n\n"
    "[id=dcsn_to_cntn, (m) : !dcsn -> (m_a : ℝ) : !cntn] {\n    m_a = m\n}\n\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = m*V[>]                   :: [id=value]\n}\n\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
    "    V[<] = E_{ε}(m*V)            :: [id=value]\n}\n"
)


@pytest.fixture(scope="module")
def stage_reading_a_state_in_its_values():
    """The stage of `VALUE_TIMES_STATE`, whose value lines read the
    decision state m, calibrated at k = 2."""
    return stage_from_text(VALUE_TIMES_STATE).calibrate({"k": 2})


@pytest.mark.parametrize(
    ("stage", "arguments", "value"),
    [
        # (V≻, m_d, c) = (4, 2, 1) and ρ = 2: 2*𝑢(1) + 4 = 2*(-1) + 4
        pytest.param(
            "cons_obs_with_resources_in_its_value", (4, 2, 1), 2.0, id="resources-times-utility"
        ),
        # (V≻, m) = (1, 3): 3*1
        pytest.param(
            "stage_reading_a_state_in_its_values", (1.0, 3.0), 3.0, id="state-times-continuation"
        ),
    ],
)
def test_a_backward_aggregation_reads_a_state_of_its_output_perch_as_an_argument_of_its_kernel(
    request, stage, arguments, value
):
    """A value line that reads a state of the decision perch, at which the
    aggregation's output stands, compiles to a function that takes the
    state as an argument: the state is a coordinate of the output and of
    the kernel, and no wire of the block's header."""
    version = request.getfixturevalue(stage)
    aggregator = compile_kernel(version, DECISION_AGGREGATION)
    values = kernel(version, DECISION_AGGREGATION).parameter_values
    assert float(aggregator(*arguments, *values)) == value


def test_an_arrival_aggregation_reads_a_decision_state_through_the_law_of_motion(
    stage_reading_a_state_in_its_values,
):
    """The arrival line V[<] = E_{ε}(m*V) compiles to a function of the
    arrival state b and the shock ε, which reads the decision state m
    through the law m = k*b + ε."""
    operation = "dcsn_to_arvl.value:Aggregation:1"
    values = kernel(stage_reading_a_state_in_its_values, operation).parameter_values
    # (V, b, ε) = (1, 1, 0.5) and k = 2: (2*1 + 0.5)*1
    assert (
        compile_kernel(stage_reading_a_state_in_its_values, operation)(1.0, 1.0, 0.5, *values)
        == 2.5
    )


# a forward block whose second output n = m + b reads its first output
# m = k*b + ε
TWO_OUTPUTS_IN_ORDER = (
    "@stage: g_output_read\n\nk : ℝ₊₊\n\nε : ℝ\nε ~ N(0, 1)\n\n"
    "[id=arvl_to_dcsn, (b : ℝ, ε) : !arvl -> (m : ℝ, n : ℝ) : !dcsn] {\n"
    "    m = k*b + ε                  :: [id=first_output]\n"
    "    n = m + b                    :: [id=second_output]\n}\n\n"
    "[id=dcsn_to_cntn, (m, n) : !dcsn -> (m_a : ℝ, n_a : ℝ) : !cntn] {\n"
    "    m_a = m\n    n_a = n\n}\n\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = V[>]\n}\n\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = E_{ε}(V)\n}\n"
)


def test_a_law_whose_second_output_reads_the_first_compiles_to_both_outputs_in_order():
    """A law of motion whose output n = m + b reads its output m = k*b + ε
    compiles to a function that gives the pair (m, n), m computed first; a
    value that differs fails the test."""
    stage = stage_from_text(TWO_OUTPUTS_IN_ORDER).calibrate({"k": 2})
    # (b, ε, k) = (1, 0.5, 2): m = 2*1 + 0.5 and n = m + 1
    numpy.testing.assert_allclose(
        compile_kernel(stage, "arvl_to_dcsn:Pushforward")(1.0, 0.5, 2), (2.5, 3.5)
    )


# the function 𝑢 of cons.bl, written in closed form
UTILITY = "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)"


@pytest.fixture(scope="module")
def cons_with_utility_as_an_alias():
    """The consumption stage whose 𝑢 is an alias of a function `utility`
    written in closed form, calibrated at ρ = 2."""
    text = changed(
        corpus_text("cons"), (UTILITY, "utility(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n𝑢 := utility")
    )
    return stage_from_text(text, "cons.bl").calibrate({"ρ": 2.0})


@pytest.fixture(scope="module")
def cons_with_utility_as_a_derivative():
    """The consumption stage whose 𝑢 is the derivative D_{c}(utility) of a
    function written in closed form, calibrated at ρ = 2."""
    text = changed(
        corpus_text("cons"), (UTILITY, "utility(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n𝑢 := D_{c}(utility)")
    )
    return stage_from_text(text, "cons.bl").calibrate({"ρ": 2.0})


def test_compile_kernel_compiles_a_function_reached_by_an_alias_and_refuses_a_derivative(
    cons_with_utility_as_an_alias, cons_with_utility_as_a_derivative
):
    """`compile_kernel` compiles the aggregator of a stage whose 𝑢 is an
    alias of a function in closed form, and refuses under `kernel-form`
    that of a stage whose 𝑢 is a derivative, naming that definition."""
    aggregator = compile_kernel(cons_with_utility_as_an_alias, DECISION_AGGREGATION)
    # (V≻, m_d, c, ρ) = (4, 2, 0.5, 2): 𝑢(0.5) + 4 = -2 + 4
    assert float(aggregator(4, 2, 0.5, 2.0)) == 2.0
    with pytest.raises(ConstructionError) as refused:
        compile_kernel(cons_with_utility_as_a_derivative, DECISION_AGGREGATION)
    assert refused.value.rule == "kernel-form" and "𝑢 := D_{c}(utility)" in refused.value.message


def test_a_kernel_text_is_written_for_a_function_reached_by_an_alias_and_not_for_a_derivative(
    cons_with_utility_as_an_alias, cons_with_utility_as_a_derivative
):
    """The Python text of the aggregator of a stage whose 𝑢 is an alias
    names the inner function of 𝑢 by the definition `utility` that the
    alias reaches, and the kernel of a stage whose 𝑢 is a derivative holds
    no Python text."""
    assert "utility is 𝑢" in kernel(cons_with_utility_as_an_alias, DECISION_AGGREGATION).python
    assert kernel(cons_with_utility_as_a_derivative, DECISION_AGGREGATION).python is None


@pytest.fixture(scope="module")
def joint_choice_stage():
    """The stage of `JOINT_CHOICE`, whose control u is declared on ℝ × ℝ
    and whose law of motion is a = x_d + u[1] + u[2], calibrated with no
    parameter."""
    return stage_from_text(JOINT_CHOICE).calibrate({})


@pytest.mark.parametrize(
    ("operation", "signature"),
    [
        pytest.param(DECISION_PULLBACK, "(x_d, u)", id="pullback"),
        pytest.param(DECISION_AGGREGATION, "(V_cntn, x_d, u)", id="aggregation"),
    ],
)
def test_a_control_on_a_product_of_two_sets_is_one_argument_of_a_compiled_kernel(
    joint_choice_stage, operation, signature
):
    """The control u on ℝ × ℝ is one argument of each compiled kernel that
    reads it."""
    assert str(inspect.signature(compile_kernel(joint_choice_stage, operation))) == signature


@pytest.mark.parametrize(
    ("operation", "arguments", "value"),
    [
        # a = x_d + u[1] + u[2] at x_d = [10, 20] and u = [(1, 2), (3, 4)]
        pytest.param(
            DECISION_PULLBACK,
            (numpy.array([10, 20]), [[1, 2], [3, 4]]),
            [13, 27],
            id="pullback-on-arrays",
        ),
        # V = -u[1]^2 - u[2]^2 + V≻ at V≻ = [10, 30], x_d = [10, 20] and the
        # same u
        pytest.param(
            DECISION_AGGREGATION,
            (numpy.array([10, 30]), [10, 20], [[1, 2], [3, 4]]),
            [5, 5],
            id="aggregation-on-arrays",
        ),
        # a = 10 + 1 + 2 at one point, u given as a tuple
        pytest.param(DECISION_PULLBACK, (10, (1, 2)), 13, id="pullback-at-one-point"),
    ],
)
def test_a_compiled_kernel_reads_the_components_of_a_product_control_on_its_last_axis(
    joint_choice_stage, operation, arguments, value
):
    """A compiled kernel reads the two components of the control u on the
    last axis of its argument, and gives one value for each point of an
    array of points and one number at one point."""
    result = compile_kernel(joint_choice_stage, operation)(*arguments)
    assert numpy.shape(result) == numpy.shape(value)
    numpy.testing.assert_array_equal(result, value)


def test_a_compiled_kernel_does_not_check_the_declared_shape_of_a_product_control(
    joint_choice_stage,
):
    """The compiled law of motion reads the two components that ℝ × ℝ
    declares and no third component given beside them."""
    # a = 10 + 1 + 2; the component 3 is not read
    assert float(compile_kernel(joint_choice_stage, DECISION_PULLBACK)(10, (1, 2, 3))) == 13


# the headers and the value lines of the blocks cntn_to_dcsn and dcsn_to_arvl
# of the buffer-stock stage file
DECISION_VALUE_HEADER = "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]"


DECISION_VALUE_LINE = "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"


ARRIVAL_VALUE_HEADER = "(V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl]"


ARRIVAL_VALUE_LINE = "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"


def aggregation_with_a_second_field(line, declarations="b : ℝ\n"):
    """The aggregation of the backward decision builder of the buffer-stock
    stage with a second value field L: `line` writes L in the block
    cntn_to_dcsn, and the block dcsn_to_arvl writes L[<] = E_{ψ,ξ}(L). The
    stage adds `declarations`, the parameter b : ℝ by default, and is
    calibrated at b = -1."""
    text = buffer_stock_text_with_changes(
        (BUFFER_STOCK_XA_DEFINITION, BUFFER_STOCK_XA_DEFINITION + declarations),
        (
            DECISION_VALUE_HEADER,
            "(V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
            " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn]",
        ),
        (DECISION_VALUE_LINE, f"{DECISION_VALUE_LINE}    {line}\n"),
        (ARRIVAL_VALUE_HEADER, "(V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl]"),
        (ARRIVAL_VALUE_LINE, f"{ARRIVAL_VALUE_LINE}    L[<] = E_{{ψ,ξ}}(L)\n"),
    )
    stage = stage_from_text(text, "buffer_stock.bl")
    stage.calibrate({"calibration": {**BUFFER_STOCK_BASELINE_CALIBRATION, "b": -1.0}})
    return stage.builder["cntn", "dcsn"]["Aggregation"]


@pytest.fixture(scope="module")
def aggregation_with_the_greater_of_two():
    """The aggregation of the buffer-stock stage whose second field is
    L = max(L[>], b)."""
    return aggregation_with_a_second_field("L = max(L[>], b)")


@pytest.fixture(scope="module")
def aggregation_with_the_lesser_of_two():
    """The aggregation of the buffer-stock stage whose second field is
    L = min(L[>], b)."""
    return aggregation_with_a_second_field("L = min(L[>], b)")


def values_at_one_point(aggregation, second_field):
    """What the compiled kernel of `aggregation` gives at the continuation
    values 1, 2 and 3 of V and `second_field` of L, resources 2 and
    consumption 0.5, with the calibrated values of its parameters: the
    value V and the second field L, each as a list."""
    function = aggregation.compile_kernel()
    value, second = function(
        numpy.array([1.0, 2.0, 3.0]),
        numpy.array(second_field),
        2.0,
        0.5,
        *aggregation.kernel().parameter_values,
    )
    return value.tolist(), second.tolist()


@pytest.mark.parametrize(
    ("aggregation", "printed"),
    [
        pytest.param(
            "aggregation_with_the_greater_of_two",
            "𝐺 of cntn_to_dcsn: 𝐺(V≻, L≻, m, c) = (𝑢(c) + β*V≻, max(L≻, b))",
            id="max",
        ),
        pytest.param(
            "aggregation_with_the_lesser_of_two",
            "𝐺 of cntn_to_dcsn: 𝐺(V≻, L≻, m, c) = (𝑢(c) + β*V≻, min(L≻, b))",
            id="min",
        ),
    ],
)
def test_the_kernel_of_a_line_that_writes_max_or_min_prints_the_call(
    request, aggregation, printed
):
    """The printed kernel of an aggregation whose line writes `max` or
    `min` holds the call as the line writes it."""
    held = request.getfixturevalue(aggregation).kernel()
    assert str(held).splitlines()[0] == printed


@pytest.mark.parametrize(
    ("aggregation", "second_field"),
    [
        # the greater of L≻ = -2, -1 and 0.5 and b = -1
        pytest.param("aggregation_with_the_greater_of_two", [-1.0, -1.0, 0.5], id="max"),
        # the lesser of the same
        pytest.param("aggregation_with_the_lesser_of_two", [-2.0, -1.0, -1.0], id="min"),
    ],
)
def test_an_aggregation_with_max_or_min_gives_its_value_and_the_greater_or_lesser_argument(
    request, aggregation, second_field
):
    """`max` and `min` on a line compile to the greater and the lesser of
    their arguments at each point, beside the value of the same
    aggregation."""
    piece = request.getfixturevalue(aggregation)
    assert piece.kernel().parameters == ("b", "β", "ρ")
    assert piece.kernel().parameter_values == (-1.0, 0.96, 2.0)
    value, second = values_at_one_point(piece, [-2.0, -1.0, 0.5])
    # 𝑢(0.5) + β*V≻ = -2 + 0.96*V≻ at V≻ = 1, 2 and 3, at ρ = 2
    assert value == pytest.approx([-1.04, -0.08, 0.88])
    assert second == second_field


@pytest.mark.parametrize(
    ("aggregation", "call"),
    [
        pytest.param("aggregation_with_the_greater_of_two", "np.maximum", id="max"),
        pytest.param("aggregation_with_the_lesser_of_two", "np.minimum", id="min"),
    ],
)
def test_max_or_min_on_a_line_is_written_as_numpys_maximum_or_minimum(request, aggregation, call):
    """The Python text of an aggregation whose line writes `max` or `min`
    computes L by NumPy's `maximum` or `minimum` of L≻ and b."""
    text = request.getfixturevalue(aggregation).kernel().python
    assert f"L = {call}(1.0*L_cntn, b)" in text


def test_a_function_named_max_that_the_stage_defines_is_the_function_called():
    """Where the stage defines a function `max`, the line L = max(L[>], b)
    calls that function, and not the greater of two values."""
    piece = aggregation_with_a_second_field(
        "L = max(L[>], b)", "b : ℝ\nmax(x : ℝ, y : ℝ) := x + y\n"
    )
    assert piece.kernel().parameters == ("b", "β", "ρ")
    assert piece.kernel().parameter_values == (-1.0, 0.96, 2.0)
    # max(x, y) := x + y at L≻ = -2, -1 and 0.5 and b = -1
    assert values_at_one_point(piece, [-2.0, -1.0, 0.5])[1] == [-3.0, -2.0, -0.5]


def test_the_decision_pullback_reads_the_law_of_motion_at_the_policy_written_out(cons):
    """The defining expression of the decision pullback is the composition
    m_d ↦ 𝑔≻(m_d, 𝑐(m_d)) written out: it reads the law of motion and the
    policy function by their identities, through no abbreviation, and its
    record holds no `where` definitions."""
    pullback = cons.dcsn.builder.bwd["Pullback"].denote()
    identities = {
        str(identity) for identity in typed_expressions.free_identities(pullback.expression)
    }
    assert {"cons:function:dcsn:c", "cons:g:dcsn_to_cntn"} <= identities
    assert not any(":alias:" in identity for identity in identities)
    assert pullback.where == ()


@pytest.mark.parametrize(
    ("operation", "reads"),
    [
        pytest.param("Aggregation", True, id="aggregation-reads-it"),
        pytest.param("Evaluation", False, id="evaluation-does-not"),
    ],
)
def test_the_decision_aggregation_reads_the_policy_function_and_the_evaluation_does_not(
    cons, operation, reads
):
    """The defining expression of the decision aggregation reads the policy
    function directly, and that of the evaluation does not read it."""
    expression = cons.dcsn.builder.bwd[operation].denote().expression
    identities = {str(identity) for identity in typed_expressions.free_identities(expression)}
    assert ("cons:function:dcsn:c" in identities) == reads


@pytest.fixture(scope="module")
def two_nodes_with_a_shock_law_of_the_control():
    """The small stage `two_nodes` of the tests, whose shock y has here
    the law N(c, 1), which reads the control c, and whose policy maximizes
    -c^2."""
    text = two_nodes_text_with_changes(
        declarations="y ~ N(c,1)\nz : ℝ\nz ~ N(0,1)\n",
        header="(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
    )
    return stage_from_text(
        changed(
            text,
            (
                "argmax_{c : Γ(k_d)}(E_{y,z}(β*V[>]) + E_{y,z}(β*V[>]))",
                "argmax_{c : Γ(k_d)}(-c^2)",
            ),
        )
    )


def records_of_kind(graph, kind):
    """The record that `denote()` answers for each operation of kind `kind`
    of a builders graph at the primitive grain."""
    return [graph[name].denote() for name in graph.list() if kind_of(graph[name].box) == kind]


def test_an_expectation_by_a_law_of_the_control_holds_its_law_by_reference_not_at_the_policy(
    two_nodes_with_a_shock_law_of_the_control,
):
    """Each expectation of the backward decision builder over the shock y,
    whose law N(c, 1) reads the control, is held as the file writes it, an
    operator E, with the law of y among its definitions and no read of the
    policy function: no measure is constructed at the policy."""
    builder = two_nodes_with_a_shock_law_of_the_control.dcsn.builder.bwd.primitives
    records = records_of_kind(builder, "Expectation")
    assert records
    for record in records:
        held = record.outputs[0].expression.body
        identities = typed_expressions.free_identities(record.expression)
        assert isinstance(held, terms.Operator) and held.head == "E"
        assert Y_IDENTITY in {str(item.identity) for item in record.definitions}
        assert "two_nodes:function:dcsn:c" not in {str(identity) for identity in identities}


def test_the_forward_extension_by_a_law_of_the_control_reads_the_control_through_the_policy(
    two_nodes_with_a_shock_law_of_the_control,
):
    """The distribution extensions of the forward decision builder read the
    control of the law N(c, 1) of y through the policy function, and none
    reads the control as a field of the decision perch."""
    builder = two_nodes_with_a_shock_law_of_the_control.dcsn.builder.fwd.primitives
    records = records_of_kind(builder, "DistributionExtension")
    assert records
    identities = [
        {str(identity) for identity in typed_expressions.free_identities(record.expression)}
        for record in records
    ]
    assert any("two_nodes:function:dcsn:c" in found for found in identities)
    assert all("two_nodes:dcsn:c" not in found for found in identities)


# the candidate line of `EGM_LINES` with its clause, and as an equality
INVERSE_EULER_WITH_CLAUSE = "c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0"


INVERSE_EULER_AS_EQUALITY = "c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])"


# the operation that the candidate line and the grid line of the policy
# block form together
ENDOGENOUS_GRID = "policy.endoggrid:Aggregation"


@pytest.fixture(scope="module")
def interior_cons_text():
    """The consumption stage with the policy lines of `EGM_LINES`, its
    candidate line written as an equality without the clause ⟂ a >= 0: the
    implicit policy relation of the public page on field equations."""
    return changed(
        cons_text_with_policy_lines("cons", EGM_LINES),
        (INVERSE_EULER_WITH_CLAUSE, INVERSE_EULER_AS_EQUALITY),
    )


@pytest.fixture(scope="module")
def interior_cons(interior_cons_text):
    """The stage of `interior_cons_text`, calibrated at ρ = 2."""
    return stage_from_text(interior_cons_text).calibrate({"ρ": 2.0})


def test_the_candidate_line_and_the_grid_line_form_one_aggregation_of_the_policy_builder(
    interior_cons,
):
    """The candidate line c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) and the grid line
    m_d[>] = a + c[>] print one kernel 𝐺 of the marginal value at the
    saving and of the saving, whose outputs are the two candidates."""
    assert kernel(interior_cons, ENDOGENOUS_GRID).splitlines() == [
        "𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(V≻, a, D_{a}(V≻)) = "
        "(𝑑𝑢𝑖𝑛𝑣(D_{a}(V≻)), a + 𝑑𝑢𝑖𝑛𝑣(D_{a}(V≻)))",
        "outputs (c≻, m_d≻); unused V≻; c≻ reads D_{a}(V≻); m_d≻ reads a, D_{a}(V≻)",
    ]


def test_the_aggregation_of_the_two_lines_compiles_to_consumption_and_resources(interior_cons):
    """The compiled kernel of the two lines takes the marginal value as its
    third argument and gives the consumption 𝑑𝑢𝑖𝑛𝑣(D_{a}V≻) and the
    resources a + c, whatever the continuation value, which it does not
    use."""
    aggregator = compile_kernel(interior_cons, ENDOGENOUS_GRID)
    assert str(inspect.signature(aggregator)) == "(V_cntn, a, argument, ρ)"
    # (V≻, a, D_{a}V≻, ρ) = (0, 3, 4, 2): c = 4^(-1/2) and m_d = 3 + c
    assert tuple(map(float, aggregator(0.0, 3.0, 4.0, 2.0))) == (0.5, 3.5)
    assert tuple(map(float, aggregator(17.0, 3.0, 4.0, 2.0))) == (0.5, 3.5)


def test_the_card_of_the_aggregation_of_the_two_lines_quotes_both_lines(interior_cons):
    """The card of the aggregation that the candidate line and the grid
    line form quotes both lines."""
    face = card(interior_cons, ENDOGENOUS_GRID)
    assert "c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])" in face and "m_d[>] = a + c[>]" in face


def test_the_aggregation_of_the_two_lines_types_its_wires_by_the_declared_sets_of_their_fields(
    interior_cons,
):
    """The record of the aggregation that the two lines form types its
    input, the continuation value, and its outputs, the two candidates, as
    functions of the saving into the declared sets of their fields."""
    answer = interior_cons.builder.bwd["policy", "endoggrid:Aggregation"].denote()
    assert [(wire.name, wire.type) for wire in answer.inputs] == [("𝑉≻", "Xa → [−∞, ∞)")]
    assert [(wire.name, wire.type) for wire in answer.outputs] == [
        ("𝑐≻", "Xa → ℝ₊₊"),
        ("𝑚_d≻", "Xa → Xm"),
    ]


def test_compile_kernel_refuses_the_identification_of_the_policy_block_as_a_relation(
    interior_cons,
):
    """`compile_kernel` refuses under `kernel-target` the identification
    c = c[>], the policy on resources read through the coordinate function
    m_d[>], a relation of which no side is an explicit function of the
    row's inputs, while the candidate lines beside it compile."""
    # the candidate lines compile; a refusal here fails the test
    compile_kernel(interior_cons, ENDOGENOUS_GRID)
    relation = interior_cons.builder.bwd["policy", "cons_choice:Pullback"].box
    with pytest.raises(ConstructionError) as refused:
        compile_kernel(interior_cons, relation)
    assert refused.value.rule == "kernel-target"


def test_the_maximization_stands_as_the_condition_on_the_output_of_the_policy_builder(
    interior_cons,
):
    """The maximization that the policy block marks `!doc` stands in the
    record of the policy builder as the one condition on its output."""
    [declared] = interior_cons.builder.bwd["policy"].denote().doc
    assert typed_expressions.format_expression(declared.statement, width=None) == (
        "c(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V≻(𝑔(m_d, cp))]"
    )


def test_a_candidate_computed_from_the_saving_alone_reads_no_value_input(interior_cons_text):
    """The kernel of a candidate line c[>] = a/2, which reads the saving
    alone, printed and compiled, takes the saving as its one argument."""
    text = changed(interior_cons_text, (INVERSE_EULER_AS_EQUALITY, "c[>]   = a/2"))
    rule = stage_from_text(text).calibrate({"ρ": 2.0})
    assert kernel(rule, ENDOGENOUS_GRID).splitlines() == [
        "𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(a) = (a/2, a + a/2)",
        "outputs (c≻, m_d≻)",
    ]
    aggregator = compile_kernel(rule, ENDOGENOUS_GRID)
    assert str(inspect.signature(aggregator)) == "(a)"
    # a = 3: c = 3/2 and m_d = 3 + c
    assert tuple(map(float, aggregator(3.0))) == (1.5, 4.5)


def inverse_euler_line(text):
    """The line of `text` whose id is InvEuler."""
    return next(line for line in text.splitlines() if "[id=InvEuler]" in line)


def test_a_local_name_of_the_policy_block_is_folded_into_the_kernel_of_the_line_that_reads_it(
    interior_cons_text,
):
    """A local name x = 2*D_{a}V[>], read by the candidate line, is folded
    into the candidate's kernel on the saving, and its line stands among
    the statements of that kernel."""
    line = inverse_euler_line(interior_cons_text)
    assert interior_cons_text.count(line) == 1
    scaled_line = line.replace("𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])", "𝑑𝑢𝑖𝑛𝑣(x)    ")
    text = interior_cons_text.replace(
        line, "    x      = 2*D_{a}V[>]                 :: [id=scale]\n" + scaled_line
    )
    scaled = stage_from_text(text).calibrate({"ρ": 2.0})
    assert kernel(scaled, ENDOGENOUS_GRID).splitlines()[0] == (
        "𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(V≻, a, D_{a}(V≻)) = "
        "(𝑑𝑢𝑖𝑛𝑣(2*D_{a}(V≻)), a + 𝑑𝑢𝑖𝑛𝑣(2*D_{a}(V≻)))"
    )
    answer = scaled.builder.bwd["policy", "endoggrid:Aggregation"].denote()
    assert [
        (str(statement.address), statement.text)
        for statement in answer.kernel.statements
        if str(statement.address) == "policy.scale"
    ] == [("policy.scale", "x      = 2*D_{a}V[>]                 :: [id=scale]")]
    # (V≻, a, D_{a}V≻, ρ) = (0, 3, 2, 2): x = 2*2, c = 4^(-1/2) and
    # m_d = 3 + c
    aggregator = compile_kernel(scaled, ENDOGENOUS_GRID)
    assert tuple(map(float, aggregator(0.0, 3.0, 2.0, 2.0))) == (0.5, 3.5)


def test_a_candidate_of_the_policy_block_is_accepted_for_a_control_and_refused_for_another_name(
    interior_cons, interior_cons_text
):
    """The policy block accepts the candidate c[>] of its control c, whose
    line forms the aggregation of the two lines, and refuses under
    `candidate-coordinate`, at the candidate line, a candidate cc[>] of a
    name that is neither a control nor a state of the decision perch."""
    accepted = {str(key) for key in interior_cons.builder.bwd.primitives.list()}
    assert ENDOGENOUS_GRID in accepted
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(interior_cons_text.replace("c[>]", "cc[>]"))
    assert (refused.value.rule, refused.value.address) == (
        "candidate-coordinate",
        "policy.InvEuler",
    )


def test_the_policy_block_refuses_a_value_input_read_on_the_grid_of_another_perch(
    interior_cons_text,
):
    """The policy block refuses as not constructed a line x[<] = D_{a}V[>]
    that reads a value input of the savings grid on the grid of the
    arrival perch, and the refusal says that V[>] is a function of a."""
    line = inverse_euler_line(interior_cons_text)
    assert interior_cons_text.count(line) == 1
    text = interior_cons_text.replace(
        line, line + "\n    x[<]   = D_{a}V[>]                   :: [id=arrival_read]"
    )
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text)
    assert (refused.value.rule, refused.value.address) == (
        "not-constructed",
        "policy.arrival_read",
    )
    assert "reads V[>], a function of (a)" in refused.value.message


def test_the_policy_block_refuses_a_field_that_two_of_its_lines_define(interior_cons_text):
    """The policy block refuses under `defined-once`, at the second line,
    a field m_d[>] that two of its lines define."""
    grid_line = "    m_d[>] = a + c[>]                :: [id=endoggrid]"
    assert interior_cons_text.count(grid_line) == 1
    text = interior_cons_text.replace(
        grid_line, grid_line + "\n    m_d[>] = a + 1                   :: [id=again]"
    )
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text)
    assert (refused.value.rule, refused.value.address) == ("defined-once", "policy.again")


# the clause of the candidate line of the methods file of the consumption
# stage
INVERSE_EULER_CLAUSE = " ⟂ a >= 0"


@pytest.mark.parametrize(
    "clause", [INVERSE_EULER_CLAUSE, ""], ids=["with-the-clause", "without-the-clause"]
)
def test_the_candidate_line_compiles_its_explicit_side_with_or_without_its_clause(clause):
    """The candidate line c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) of the methods file
    compiles to its explicit side 𝑑𝑢𝑖𝑛𝑣(D_{a}V≻) = (D_{a}V≻)^(-1/ρ), with
    the clause ⟂ a >= 0 on its line and without it."""
    addition = CONS_METHODS.read_text()
    assert addition.count(INVERSE_EULER_CLAUSE) == 1
    stage = stage_from_text(corpus_text("cons"), CORPUS["cons"]).methodize(
        {"text": addition.replace(INVERSE_EULER_CLAUSE, clause), "origin": str(CONS_METHODS)}
    )
    row = stage.calibrate(FIRST_CALIBRATIONS["cons"]).builder.policy["InvEuler:Aggregation"]
    marginal, saving = numpy.array([2.0, 0.25, 0.8]), numpy.array([0.5, 1.0, 4.0])
    # (V≻, a, D_{a}V≻) = (0, saving, marginal) and ρ = 6
    candidate = row.compile_kernel()(
        numpy.zeros_like(saving), saving, marginal, *row.kernel().parameter_values
    )
    numpy.testing.assert_allclose(candidate, marginal ** (-1 / 6.0))


@pytest.fixture(scope="module")
def interior_cons_with_a_node_at_the_candidate(interior_cons_text):
    """The stage of `interior_cons_text` with its candidate line marked
    `!node`, calibrated at ρ = 2."""
    text = changed(interior_cons_text, (":: [id=InvEuler]", ":: [id=InvEuler, !node]"))
    return stage_from_text(text).calibrate({"ρ": 2.0})


def test_a_node_at_the_candidate_line_gives_the_candidate_its_own_kernel(
    interior_cons_with_a_node_at_the_candidate,
):
    """With its line marked `!node`, the candidate is an aggregation of its
    own at the grain of the sub-builders, which compiles to the
    consumption 𝑑𝑢𝑖𝑛𝑣(D_{a}V≻)."""
    policy = interior_cons_with_a_node_at_the_candidate.builder.policy
    candidate = policy["InvEuler", "Aggregation"].compile_kernel()
    # (V≻, a, D_{a}V≻, ρ) = (0, 3, 4, 2): c = 4^(-1/2)
    assert float(candidate(0.0, 3.0, 4.0, 2.0)) == 0.5


def test_a_node_at_the_candidate_line_leaves_the_grid_line_a_kernel_of_the_candidate(
    interior_cons_with_a_node_at_the_candidate,
):
    """With the candidate line marked `!node`, the kernel of the grid line
    reads the candidate c as an argument beside the saving."""
    grid = interior_cons_with_a_node_at_the_candidate.builder.policy["endoggrid:Aggregation"]
    assert grid.kernel().splitlines() == [
        "𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(c, a) = a + c",
        "output m_d≻",
    ]


def test_the_primitive_grain_composes_the_grid_line_with_the_candidate_of_its_own_node(
    interior_cons_with_a_node_at_the_candidate,
):
    """At the primitive grain the grid line's kernel, given the value of
    the candidate's own kernel, gives the resources a + c."""
    stage = interior_cons_with_a_node_at_the_candidate
    candidate = stage.builder.policy["InvEuler", "Aggregation"].compile_kernel()
    resources = stage.builder.bwd.primitives[ENDOGENOUS_GRID].compile_kernel()
    # (V≻, a, D_{a}V≻, ρ) = (0, 3, 4, 2): c = 0.5, then (c, a) = (0.5, 3)
    assert float(resources(candidate(0.0, 3.0, 4.0, 2.0), 3.0)) == 3.5


# relative tolerance of the comparisons with closed forms: every value is a
# few elementary operations from its formula
RELATIVE = 1e-12


@pytest.fixture(scope="module")
def smooth_ambiguity_kernels(sa_savings):
    """`smooth_ambiguity_kernels(index)`: the compiled kernels of the
    smooth-ambiguity savings stage at the calibration
    `SA_SAVINGS_CALIBRATIONS[index]`, each given the calibration's values
    after its arguments, by name, made once for each calibration."""

    @functools.cache
    def made(index):
        stage = copy_native(sa_savings).calibrate(SA_SAVINGS_CALIBRATIONS[index])
        sub_builders = stage.builder.bwd.sub_builders
        risk = boxes_inside_bubble(sub_builders, "cntn_to_dcsn.risk_ce")
        ambiguity = boxes_inside_bubble(sub_builders, "cntn_to_dcsn.ambiguity_ce")
        primitive = {box.name: box for box in stage.builder.bwd.primitives.graph.boxes}
        boxes = {
            "law of motion": risk["cntn_to_dcsn.risk_ce:Pullback"],
            "risk power": risk["cntn_to_dcsn.risk_ce:Aggregation:1"],
            "risk root": risk["cntn_to_dcsn.risk_ce:Aggregation"],
            "ambiguity power": ambiguity["cntn_to_dcsn.ambiguity_ce:Aggregation:1"],
            "ambiguity root": ambiguity["cntn_to_dcsn.ambiguity_ce:Aggregation"],
            "value": next(
                box for box in sub_builders.graph.boxes if box.name == "cntn_to_dcsn:Aggregation"
            ),
            "primitive ambiguity power": primitive["cntn_to_dcsn.ambiguity_ce:Aggregation:1"],
            "primitive value": primitive["cntn_to_dcsn:Aggregation"],
        }
        return {name: at_the_calibration(stage, box) for name, box in boxes.items()}

    return made


def at_the_calibration(stage, box):
    """The function compiled from the kernel of `box`, given the values
    that the calibration of `stage` binds to its parameters after its own
    arguments."""
    function, bound = compile_kernel(stage, box), kernel(stage, box).parameter_values
    return lambda *arguments: function(*arguments, *bound)


def comparison_points(values):
    """The points of the comparisons at the calibration `values`, as arrays
    that broadcast together: resources m_d of 0.5, 1 and 2 on the first
    axis; consumption c, a share of 0.2, 0.5 and 0.8 of resources, and the
    saving s = m_d - c on the second; the mean ν of the log return at
    κ_1 - σ_ν, κ_1 and κ_1 + σ_ν on the third; and the return
    Ψ = exp(ν + σ_Ψ*z) at z = -1, 0 and 1 on the fourth."""
    resources = numpy.array([0.5, 1.0, 2.0]).reshape(3, 1, 1, 1)
    consumption = numpy.array([0.2, 0.5, 0.8]).reshape(1, 3, 1, 1) * resources
    mean = values["κ_1"] + values["σ_ν"] * numpy.array([-1.0, 0.0, 1.0]).reshape(1, 1, 3, 1)
    shock = numpy.array([-1.0, 0.0, 1.0]).reshape(1, 1, 1, 3)
    return types.SimpleNamespace(
        m_d=resources,
        c=consumption,
        s=resources - consumption,
        ν=mean,
        Ψ=numpy.exp(mean + values["σ_Ψ"] * shock),
    )


def risk_moment(points, values):
    """The closed form of E_Ψ[(s*Ψ)^(1-γ)] at the mean ν of the log return,
    s^(1-γ)*exp((1-γ)*ν + (1-γ)^2*σ_Ψ^2/2)."""
    γ, σ_Ψ = values["γ"], values["σ_Ψ"]
    return points.s ** (1 - γ) * numpy.exp((1 - γ) * points.ν + (1 - γ) ** 2 * σ_Ψ**2 / 2)


def ambiguity_moment(points, values):
    """The closed form of E_ν[CE^(1-η)], with CE the risk certainty
    equivalent, s^(1-η)*exp((1-η)*(κ_1 + (1-γ)*σ_Ψ^2/2) + (1-η)^2*σ_ν^2/2)."""
    γ, η, κ, σ_ν, σ_Ψ = (values[name] for name in ("γ", "η", "κ_1", "σ_ν", "σ_Ψ"))
    return points.s ** (1 - η) * numpy.exp(
        (1 - η) * (κ + (1 - γ) * σ_Ψ**2 / 2) + (1 - η) ** 2 * σ_ν**2 / 2
    )


def ambiguity_equivalent(points, values):
    """The closed form of the ambiguity certainty equivalent,
    s*exp(κ_1 + (1-η)*σ_ν^2/2 + (1-γ)*σ_Ψ^2/2)."""
    γ, η, κ, σ_ν, σ_Ψ = (values[name] for name in ("γ", "η", "κ_1", "σ_ν", "σ_Ψ"))
    return points.s * numpy.exp(κ + (1 - η) * σ_ν**2 / 2 + (1 - γ) * σ_Ψ**2 / 2)


# the two calibrations of the smooth-ambiguity stage, by their index in
# SA_SAVINGS_CALIBRATIONS: ambiguity aversion η = 8 above risk aversion
# γ = 5, and η = γ = 5
CALIBRATIONS = [
    pytest.param(0, id="ambiguity-aversion-above-risk-aversion"),
    pytest.param(1, id="equal-aversions"),
]


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_law_of_motion_of_the_smooth_ambiguity_stage_gives_the_saving_times_the_return(
    smooth_ambiguity_kernels, index
):
    """The compiled law of motion of the risk certainty equivalent gives
    the saving s times the return Ψ."""
    points = comparison_points(SA_SAVINGS_CALIBRATIONS[index])
    law = smooth_ambiguity_kernels(index)["law of motion"]
    assert law(points.m_d, points.c, points.Ψ) == pytest.approx(
        points.s * points.Ψ, rel=RELATIVE, abs=0
    )


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_kernels_of_the_risk_certainty_equivalent_give_its_closed_form(
    smooth_ambiguity_kernels, index
):
    """The two aggregations of the risk certainty equivalent give the
    power (s*Ψ)^(1-γ) and, at the closed form of its expectation over Ψ,
    the root s*exp(ν + (1-γ)*σ_Ψ^2/2)."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    γ, σ_Ψ = values["γ"], values["σ_Ψ"]
    saved = points.s * points.Ψ
    assert made["risk power"](saved, points.m_d, points.c, points.Ψ) == pytest.approx(
        saved ** (1 - γ), rel=RELATIVE, abs=0
    )
    root = made["risk root"](risk_moment(points, values), points.m_d, points.c, points.ν)
    assert root == pytest.approx(
        points.s * numpy.exp(points.ν + (1 - γ) * σ_Ψ**2 / 2), rel=RELATIVE, abs=0
    )


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_kernels_of_the_ambiguity_certainty_equivalent_give_its_closed_form(
    smooth_ambiguity_kernels, index
):
    """The two aggregations of the ambiguity certainty equivalent give the
    power CE^(1-η) of the risk certainty equivalent CE and, at the closed
    form of its expectation over ν, the root
    s*exp(κ_1 + (1-η)*σ_ν^2/2 + (1-γ)*σ_Ψ^2/2)."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    η = values["η"]
    equivalent = made["risk root"](risk_moment(points, values), points.m_d, points.c, points.ν)
    power = equivalent ** (1 - η)
    # the reference power is computed from a kernel's output: the assert
    # checks that it is finite and positive, so that agreement to a relative
    # tolerance shows that the compared value is finite and positive too
    assert numpy.isfinite(power).all() and (power > 0).all()
    assert made["ambiguity power"](equivalent, points.m_d, points.c, points.ν) == pytest.approx(
        power, rel=RELATIVE, abs=0
    )
    root = made["ambiguity root"](ambiguity_moment(points, values), points.m_d, points.c)
    assert root == pytest.approx(ambiguity_equivalent(points, values), rel=RELATIVE, abs=0)


@pytest.mark.parametrize(
    ("index", "ratio"),
    [
        # exp((5 - 8)*0.05^2/2)
        pytest.param(0, 0.996257022469171, id="ambiguity-aversion-above-risk-aversion"),
        pytest.param(1, 1.0, id="equal-aversions"),
    ],
)
def test_the_ambiguity_equivalent_is_the_predictive_equivalent_times_its_closed_form_factor(
    smooth_ambiguity_kernels, index, ratio
):
    """The compiled ambiguity certainty equivalent is the certainty
    equivalent under the predictive distribution of the return,
    s*exp(κ_1 + (1-γ)*(σ_ν^2 + σ_Ψ^2)/2), times exp((γ-η)*σ_ν^2/2)."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    γ, η, κ, σ_ν, σ_Ψ = (values[name] for name in ("γ", "η", "κ_1", "σ_ν", "σ_Ψ"))
    equivalent = made["ambiguity root"](ambiguity_moment(points, values), points.m_d, points.c)
    predictive = points.s * numpy.exp(κ + (1 - γ) * (σ_ν**2 + σ_Ψ**2) / 2)
    assert equivalent / predictive == pytest.approx(
        numpy.exp((γ - η) * σ_ν**2 / 2), rel=RELATIVE, abs=0
    )
    assert equivalent / predictive == pytest.approx(ratio, rel=RELATIVE, abs=0)


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_primitive_grain_composes_the_ambiguity_power_with_the_risk_root(
    smooth_ambiguity_kernels, index
):
    """At the primitive grain the power of the ambiguity certainty
    equivalent, given the risk root, gives what the sub-builder's power
    gives."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    root = made["risk root"](risk_moment(points, values), points.m_d, points.c, points.ν)
    power = made["ambiguity power"](root, points.m_d, points.c, points.ν)
    # the reference is a kernel's output: the assert checks that it is finite
    # and positive, so that agreement to a relative tolerance shows that the
    # compared value is finite and positive too
    assert numpy.isfinite(power).all() and (power > 0).all()
    assert made["primitive ambiguity power"](
        root, points.m_d, points.c, points.ν
    ) == pytest.approx(power, rel=RELATIVE, abs=0)


def test_at_equal_aversions_the_ambiguity_power_undoes_the_risk_root(smooth_ambiguity_kernels):
    """At η = γ the primitive power of the ambiguity certainty equivalent,
    given the risk root of E_Ψ[(s*Ψ)^(1-γ)], gives that expectation
    back."""
    values = SA_SAVINGS_CALIBRATIONS[1]
    points, made = comparison_points(values), smooth_ambiguity_kernels(1)
    assert values["η"] == values["γ"]
    moment = risk_moment(points, values)
    root = made["risk root"](moment, points.m_d, points.c, points.ν)
    assert made["primitive ambiguity power"](
        root, points.m_d, points.c, points.ν
    ) == pytest.approx(moment, rel=RELATIVE, abs=0)


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_value_of_the_smooth_ambiguity_stage_is_the_ces_aggregate_of_its_closed_form(
    smooth_ambiguity_kernels, index
):
    """The compiled value gives, at the ambiguity certainty equivalent AMB,
    the aggregate ((1-β)*c^(1-ρ) + β*AMB^(1-ρ))^(1/(1-ρ))."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    β, ρ = values["β"], values["ρ"]
    equivalent = made["ambiguity root"](ambiguity_moment(points, values), points.m_d, points.c)
    reference = ambiguity_equivalent(points, values)
    assert made["value"](equivalent, points.m_d, points.c) == pytest.approx(
        ((1 - β) * points.c ** (1 - ρ) + β * reference ** (1 - ρ)) ** (1 / (1 - ρ)),
        rel=RELATIVE,
        abs=0,
    )


@pytest.mark.parametrize("index", CALIBRATIONS)
def test_the_primitive_grain_composes_the_value_with_the_ambiguity_root(
    smooth_ambiguity_kernels, index
):
    """At the primitive grain the value, given the ambiguity root, gives
    what the sub-builders' value gives."""
    values = SA_SAVINGS_CALIBRATIONS[index]
    points, made = comparison_points(values), smooth_ambiguity_kernels(index)
    root = made["ambiguity root"](ambiguity_moment(points, values), points.m_d, points.c)
    value = made["value"](root, points.m_d, points.c)
    # the reference is a kernel's output: the assert checks that it is finite
    # and positive, so that agreement to a relative tolerance shows that the
    # compared value is finite and positive too
    assert numpy.isfinite(value).all() and (value > 0).all()
    assert made["primitive value"](root, points.m_d, points.c) == pytest.approx(
        value, rel=RELATIVE, abs=0
    )


# the definitions of human wealth h by cases that the JAX tests read, each
# with three growth factors Γ and the values of h that calibration gives
# there, at the interest factor R = 1.04 of the perfect-foresight
# calibration
DEFINITIONS_BY_CASES = [
    pytest.param(
        "h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf",
        (1.02, 1.04, 1.05),
        [52.0, math.inf, math.inf],
        id="infinite-at-and-above-the-interest-factor",
    ),
    pytest.param(
        "h := if Γ < R then 1/(1 - Γ/R) else 1000",
        (1.02, 1.04, 1.05),
        [52.0, 1000.0, 1000.0],
        id="a-number-at-and-above-the-interest-factor",
    ),
    pytest.param(
        "h0 := if Γ < R then 2 else 3\nh := h0^(-1)",
        (1.02, 1.04, 1.05),
        [1 / 2, 1 / 3, 1 / 3],
        id="a-negative-power-of-an-integer-branch",
    ),
    # (h0^60 + 1) - h0^60 is 1 in integers and 0 in floats; h has no value
    # at Γ = R
    pytest.param(
        "h0 := if Γ < R then 2 else 3\nh := (h0^60 + 1) - h0^60 + 1/(1 - Γ/R)",
        (1.02, 1.05, 1.02),
        [52.0, -104.0, 52.0],
        id="arithmetic-exact-in-integers-alone",
    ),
]


def wealth_by_calibration(derived_parameters, stage, growths):
    """The value that calibration gives h at each growth factor Γ of
    `growths`, each on a copy of `stage`."""
    return [
        copy_native(stage)
        .calibrate({**derived_parameters.calibration, "Γ": growth})
        .par["h"]
        .value
        for growth in growths
    ]


def consumption_under_jax(derived_parameters, stage):
    """The function of the consumption kernel of `stage`, methodized with
    `EXPLICIT_POLICY`, whose one line writes consumption as
    (1 - (R*β)^(1/ρ)/R)*(m - 1 + h), its Python text run with `jax.numpy` in
    place of NumPy, and the calibrated values of the parameters it reads, by
    name; `stage` is methodized and calibrated in place."""
    stage.methodize({"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"})
    stage.calibrate({"calibration": derived_parameters.calibration})
    held = stage.builder.policy.primitives["consumption:Aggregation"].kernel()
    namespace = {}
    exec(held.python.replace("import numpy as np", "import jax.numpy as np"), namespace)
    return namespace["G_policy_consumption"], dict(
        zip(held.parameters, held.parameter_values, strict=True)
    )


@pytest.mark.parametrize(("definition", "growths", "wealth"), DEFINITIONS_BY_CASES)
def test_a_kernel_that_reads_a_definition_by_cases_gives_calibrations_value_under_jax_jit(
    derived_parameter_stages, definition, growths, wealth
):
    """The text of the consumption kernel that reads a definition of h by
    cases, traced by `jax.jit` with JAX's arrays in place of NumPy's, gives
    at each growth factor the consumption at the value of h that
    calibration gives; a traced test of the conditional has no single truth
    value, so both branches are evaluated and one is selected, and a run
    without JAX reports the test as skipped."""
    jax = require_package("jax")
    jax.config.update("jax_enable_x64", True)
    stage = derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    assert wealth_by_calibration(derived_parameter_stages, stage, growths) == pytest.approx(wealth)
    function, held = consumption_under_jax(derived_parameter_stages, stage)
    traced = jax.jit(function)
    for growth, value in zip(growths, wealth, strict=True):
        assert numpy.allclose(
            traced(MARKET_RESOURCES, **{**held, "Γ": growth}), consumption_at_human_wealth(value)
        ), growth


@pytest.mark.parametrize(("definition", "growths", "wealth"), DEFINITIONS_BY_CASES)
def test_a_kernel_that_reads_a_definition_by_cases_gives_calibrations_value_at_a_float_under_jax(
    derived_parameter_stages, definition, growths, wealth
):
    """The same text run with JAX's arrays and a Python float for Γ, with
    no `jit`, gives the consumption at calibration's value of h: the test of
    the conditional then has one truth value, and the branch it chooses is a
    float, so that arithmetic exact in integers gives what it gives under
    calibration; a run without JAX reports the test as skipped."""
    jax = require_package("jax")
    jax.config.update("jax_enable_x64", True)
    stage = derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    assert wealth_by_calibration(derived_parameter_stages, stage, growths) == pytest.approx(wealth)
    function, held = consumption_under_jax(derived_parameter_stages, stage)
    for growth, value in zip(growths, wealth, strict=True):
        assert numpy.allclose(
            function(jax.numpy.asarray(MARKET_RESOURCES), **{**held, "Γ": growth}),
            consumption_at_human_wealth(value),
        ), growth


@pytest.mark.parametrize(("definition", "growths", "wealth"), DEFINITIONS_BY_CASES)
def test_a_kernel_that_reads_a_definition_by_cases_gives_calibrations_values_at_jax_arrays(
    derived_parameter_stages, definition, growths, wealth
):
    """The same text run with concrete JAX arrays of growth factors on both
    sides of R gives the consumption at calibration's value of h at each:
    both branches are evaluated, a branch that divides by zero at Γ = R
    gives no wrong value where it is not chosen, and two integer branches
    are selected as floats; a run without JAX reports the test as
    skipped."""
    jax = require_package("jax")
    jax.config.update("jax_enable_x64", True)
    stage = derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    assert wealth_by_calibration(derived_parameter_stages, stage, growths) == pytest.approx(wealth)
    function, held = consumption_under_jax(derived_parameter_stages, stage)
    concrete = function(
        jax.numpy.asarray(MARKET_RESOURCES), **{**held, "Γ": jax.numpy.asarray(growths)}
    )
    assert numpy.allclose(concrete, consumption_at_human_wealth(wealth))
