"""The record of a builder's kernels and the compiled kernel used outside
its call: the source of a compiled kernel and its text in another version,
Numba, cloudpickle and pickle, a second calibration passed to a function
compiled once, the operations that compile to no function and so stand in
the record as relations, the record that `kernels()` answers, and the
endogenous grid step of the cons-port tool built from two such records."""

import collections.abc
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import pickle
import subprocess
import sys
import types
from operator import attrgetter
from pathlib import Path

import cloudpickle
import numba
import numpy
import pytest
from application_files import (
    CONS_METHODS,
    CORPUS,
    DURABLES,
    FIRST_CALIBRATIONS,
    ROOT,
    SA_SAVINGS_CALIBRATIONS,
    SECOND_CALIBRATIONS,
)
from stage_builders import stage_from_text
from stage_texts import corpus_text

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.pieces import (
    BoxHandle,
    BubbleHandle,
    BuilderPairs,
    Definitions,
    GraphHandle,
    Graphs,
    LineHandle,
    PerchBuilders,
    PerchHandle,
)

# the four kernels that the endogenous grid step of the cons-port tool
# composes, each as (the path of `stage.dcsn.builder` that reads its
# builder, the key of its operation): the candidate line and the grid line of
# the policy builder, the law of motion and the aggregation of the backward
# decision builder
STEP_KERNELS = (
    ("policy", "InvEuler:Aggregation"),
    ("policy", "grid:Aggregation"),
    ("bwd", "Pullback"),
    ("bwd", "Aggregation"),
)


STEP_KERNEL_IDS = ["candidate-line", "grid-line", "law-of-motion", "aggregation"]


def operation(version, builder, key):
    """The operation `key` of the builder that the path `builder` of
    `stage.dcsn.builder` reads: `policy`, the policy builder, or `bwd`, the
    backward decision builder."""
    return getattr(version.dcsn.builder, builder)[key]


def kernel_arguments(piece, value):
    """The arguments of the compiled kernel of the operation `piece`:
    `value` for each argument of its printed kernel, then the calibrated
    value of each parameter that the kernel reads."""
    held = piece.kernel()
    count = len(inspect.signature(piece.compile_kernel()).parameters) - len(held.parameters)
    return [value] * count + list(held.parameter_values)


def explicit_operations(graph):
    """(key, operation) of each operation of a builders graph or a builder,
    at the primitive grain, whose kernel holds a Python text."""
    pieces = [(str(key), graph.primitives[str(key)]) for key in graph.primitives.list()]
    return [(key, piece) for key, piece in pieces if piece.kernel().python is not None]


def definition_block(text):
    """The lines of a kernel's Python text from the line at the first column
    that opens its function to its last line that is not blank."""
    lines = text.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.startswith("def "))
    block = lines[start:]
    while block and not block[-1].strip():
        block.pop()
    return "".join(block)


def as_floats(value):
    """A kernel's value, one number or a tuple of them, as a list of
    floats."""
    return numpy.asarray(value, dtype=float).ravel().tolist()


def at_twos(function):
    """The function's value with each of its arguments 2.0, as a list of
    floats."""
    return as_floats(function(*[2.0] * function.__code__.co_argcount))


def run_in_a_new_process(code, *arguments, path=()):
    """The finished process of a new Python interpreter that runs `code`
    with the given arguments and the folders `path` before the import path
    of this process."""
    folders = [str(folder) for folder in path] + [folder for folder in sys.path if folder]
    return subprocess.run(
        [sys.executable, "-c", code, *map(str, arguments)],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(folders)),
    )


@pytest.fixture(scope="module")
def methodized_cons_elaborated_again():
    """The consumption stage elaborated anew from its file, with its
    methods file, calibrated at ρ = 6, as `cons_methodized` is."""
    stage = stage_from_text(corpus_text("cons"), CORPUS["cons"]).methodize(CONS_METHODS)
    return stage.calibrate(FIRST_CALIBRATIONS["cons"])


@pytest.fixture(scope="module")
def methodized_cons_at_rho_two(cons_methodized_without_calibration):
    """A copy of the consumption stage with its methods file, calibrated at
    ρ = 2."""
    return copy_native(cons_methodized_without_calibration).calibrate(SECOND_CALIBRATIONS["cons"])


@pytest.mark.parametrize(("builder", "key"), STEP_KERNELS, ids=STEP_KERNEL_IDS)
def test_numba_compiles_a_kernel_of_the_step_in_one_call_to_a_function_that_takes_arrays(
    cons_methodized, builder, key
):
    """`numba.njit` compiles the function of each kernel of the endogenous
    grid step in one call, with no function that the kernel calls compiled
    beforehand, to a function that gives on arrays, at each point, its value
    on numbers; a refusal of Numba or a value that differs fails the
    test."""
    piece = operation(cons_methodized, builder, key)
    function = numba.njit(piece.compile_kernel())
    # each argument of the kernel is 2, as a number and as an array of three
    # points
    at_numbers = function(*kernel_arguments(piece, 2.0))
    on_arrays = function(*kernel_arguments(piece, numpy.full(3, 2.0)))
    numbers = numpy.asarray(at_numbers, dtype=float)[..., None]
    numpy.testing.assert_array_equal(
        numpy.asarray(on_arrays, dtype=float), numpy.broadcast_to(numbers, numpy.shape(on_arrays))
    )


@pytest.mark.parametrize(
    ("key", "arguments", "value"),
    [
        # (m_d, c) = (3, 1): the saving 3 - 1
        pytest.param("Pullback", (3.0, 1.0), 2.0, id="law-of-motion"),
        # (V≻, m_d, c, ρ) = (2, 3, 1, 6): 𝑢(1) + 2 = 1/(1 - 6) + 2
        pytest.param("Aggregation", (2.0, 3.0, 1.0, 6.0), 1.8, id="aggregation"),
    ],
)
def test_the_function_that_numba_compiles_from_a_kernel_of_the_decision_builder_gives_its_value(
    cons_methodized, key, arguments, value
):
    """The function that `numba.njit` compiles from the law of motion or
    from the aggregator of the decision builder gives its value at a
    point."""
    compiled = numba.njit(operation(cons_methodized, "bwd", key).compile_kernel())
    assert compiled(*arguments) == value


@pytest.mark.parametrize(
    ("direction", "among"),
    [
        pytest.param(
            "bwd",
            {
                "policy.InvEuler:Aggregation",
                "policy.grid:Aggregation",
                "cntn_to_dcsn:Pullback",
                "cntn_to_dcsn:Aggregation",
            },
            id="backward-builders-graph",
        ),
        pytest.param(
            "fwd",
            {"arvl_to_dcsn:Pushforward", "dcsn_to_cntn:Pushforward"},
            id="forward-builders-graph",
        ),
    ],
)
def test_the_source_of_each_compiled_kernel_is_the_function_definition_of_its_text(
    cons_methodized, direction, among
):
    """`inspect.getsource` gives, for the function compiled from each kernel
    of a builders graph that holds a Python text, the definition of the
    function in that text, from its line `def` to its last line."""
    explicit = explicit_operations(getattr(cons_methodized.builder, direction))
    # the kernels of the endogenous grid step, or the two push-forwards, are
    # among them
    assert {key for key, _ in explicit} >= among
    for key, piece in explicit:
        assert inspect.getsource(piece.compile_kernel()) == definition_block(
            piece.kernel().python
        ), key


@pytest.mark.parametrize(
    "direction", ["bwd", "fwd"], ids=["backward-builders-graph", "forward-builders-graph"]
)
def test_a_second_elaboration_of_the_stage_file_gives_each_kernel_the_same_text_byte_for_byte(
    cons_methodized, methodized_cons_elaborated_again, direction
):
    """A second elaboration of the consumption stage file with its methods
    file gives each kernel of a builders graph the Python text that it has
    in the methodized consumption stage, byte for byte."""
    explicit = explicit_operations(getattr(cons_methodized.builder, direction))
    assert explicit, direction
    again = getattr(methodized_cons_elaborated_again.builder, direction)
    for key, piece in explicit:
        text = piece.kernel().python
        assert again.primitives[key].kernel().python.encode("utf-8") == text.encode("utf-8"), key


@pytest.mark.parametrize(
    "direction", ["bwd", "fwd"], ids=["backward-builders-graph", "forward-builders-graph"]
)
def test_a_second_calibration_changes_only_the_parameter_values_of_each_kernel(
    cons_methodized, methodized_cons_at_rho_two, direction
):
    """At ρ = 2 in place of ρ = 6, each kernel of a builders graph keeps its
    Python text, byte for byte, and the names of its parameters, and holds 2
    as the value of each parameter."""
    explicit = explicit_operations(getattr(cons_methodized.builder, direction))
    assert explicit, direction
    other = getattr(methodized_cons_at_rho_two.builder, direction)
    for key, piece in explicit:
        six, two = piece.kernel(), other.primitives[key].kernel()
        assert two.python.encode("utf-8") == six.python.encode("utf-8"), key
        assert two.parameters == six.parameters, key
        assert two.parameter_values == tuple(2.0 for _ in two.parameters), key


@pytest.mark.parametrize(("builder", "key"), STEP_KERNELS, ids=STEP_KERNEL_IDS)
def test_cloudpickle_saves_and_loads_the_function_compiled_from_a_kernel(
    cons_methodized, builder, key
):
    """cloudpickle saves the function compiled from each kernel of the
    endogenous grid step, which was made in memory, and loads a function
    that gives the same values."""
    piece = operation(cons_methodized, builder, key)
    function = piece.compile_kernel()
    # each argument of the kernel is 2
    values = kernel_arguments(piece, 2.0)
    restored = cloudpickle.loads(cloudpickle.dumps(function))
    assert as_floats(restored(*values)) == as_floats(function(*values))


# the program that a new process runs on the functions that pickle saved:
# it loads each, calls it with its arguments and prints the values
LOAD_THE_PICKLED_FUNCTIONS = """\
import json, pickle, sys
import numpy
pickled = json.load(open(sys.argv[1], encoding='utf-8'))
loaded = {name: pickle.loads(bytes.fromhex(data))(*values)
          for name, (data, values) in pickled.items()}
print(json.dumps({name: numpy.asarray(value, dtype=float).ravel().tolist()
                  for name, value in loaded.items()}))
"""


def test_a_new_process_loads_the_function_that_pickle_saved_from_a_kernel_text_in_a_module(
    cons_methodized, tmp_path, monkeypatch
):
    """The Python text of each kernel of the endogenous grid step, written
    to a file of the reader's choosing, is a module whose function the
    standard pickle saves by the module's name, and a new process loads
    each such function, which gives the values of the compiled kernel."""
    expected, pickled = {}, {}
    for index, (builder, key) in enumerate(STEP_KERNELS):
        piece = operation(cons_methodized, builder, key)
        function = piece.compile_kernel()
        # each argument of the kernel is 2
        values = kernel_arguments(piece, 2.0)
        name = f"cons_kernel_{index}"
        (tmp_path / f"{name}.py").write_text(piece.kernel().python, encoding="utf-8")
        specification = importlib.util.spec_from_file_location(name, tmp_path / f"{name}.py")
        module = importlib.util.module_from_spec(specification)
        monkeypatch.setitem(sys.modules, name, module)
        specification.loader.exec_module(module)
        pickled[name] = (pickle.dumps(getattr(module, function.__name__)).hex(), values)
        expected[name] = as_floats(function(*values))
    (tmp_path / "pickled.json").write_text(json.dumps(pickled), encoding="utf-8")
    done = run_in_a_new_process(
        LOAD_THE_PICKLED_FUNCTIONS, tmp_path / "pickled.json", path=[tmp_path]
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == expected


def derivative_function(version):
    """The function of the piece of kind `Derivative` in the record of the
    backward decision builder's kernels: the stated derivative of the
    value."""
    pieces = version.dcsn.builder.bwd.kernels().pieces
    return next(piece.function for piece in pieces if piece.kind == "Derivative")


def test_a_second_calibration_reaches_the_aggregation_that_numba_compiled_once(
    cons_methodized, methodized_cons_at_rho_two
):
    """The aggregation of the decision builder, compiled by `numba.njit` at
    ρ = 6, gives at the values of a second calibration, ρ = 2, what that
    calibration's own function gives, with no second compilation."""
    six = operation(cons_methodized, "bwd", "Aggregation").kernel()
    two = operation(methodized_cons_at_rho_two, "bwd", "Aggregation").kernel()
    assert six.parameter_values == (6.0,)
    assert two.parameter_values == (2.0,)
    compiled = numba.njit(operation(cons_methodized, "bwd", "Aggregation").compile_kernel())
    # (V≻, m_d, c) = (2, 3, 0.5): 𝑢(0.5) + 2 = 0.5^(1-ρ)/(1-ρ) + 2, which is
    # -6.4 + 2 at ρ = 6 and -2 + 2 at ρ = 2
    at_six = compiled(2.0, 3.0, 0.5, *six.parameter_values)
    at_two = compiled(2.0, 3.0, 0.5, *two.parameter_values)
    assert at_six == pytest.approx(-4.4)
    assert at_two == pytest.approx(0.0)
    own = operation(methodized_cons_at_rho_two, "bwd", "Aggregation").compile_kernel()
    assert as_floats(at_two) == as_floats(own(2.0, 3.0, 0.5, *two.parameter_values))
    assert len(compiled.signatures) == 1


def test_a_second_calibration_reaches_the_stated_derivative_that_numba_compiled_once(
    cons_methodized, methodized_cons_at_rho_two
):
    """The function of the stated derivative in the record of the decision
    builder, compiled by `numba.njit`, gives the marginal utility at ρ = 6
    and at ρ = 2, as the second calibration's record does, with no second
    compilation."""
    marginal = numba.njit(derivative_function(cons_methodized))
    second = derivative_function(methodized_cons_at_rho_two)
    # (V≻, m_d, c, ρ): 𝑑𝑢(0.5) = 0.5^(-ρ), which is 64 at ρ = 6 and 4 at
    # ρ = 2
    assert marginal(2.0, 3.0, 0.5, 6.0) == 64.0
    assert marginal(2.0, 3.0, 0.5, 2.0) == second(2.0, 3.0, 0.5, 2.0) == 4.0
    assert len(marginal.signatures) == 1


def test_the_stated_derivative_that_numba_compiles_gives_arrays_on_arrays(cons_methodized):
    """The function of the stated derivative, compiled by `numba.njit`,
    gives on arrays the marginal utility at each point; a refusal of Numba
    or a value that differs fails the test."""
    marginal = numba.njit(derivative_function(cons_methodized))
    # (V≻, m_d, c, ρ) = (2, 3, 0.5, 6) at each point: 0.5^(-6)
    numpy.testing.assert_array_equal(
        marginal(numpy.full(3, 2.0), numpy.full(3, 3.0), numpy.full(3, 0.5), 6.0),
        numpy.full(3, 64.0),
    )


# what a record walked by `held_by` holds without being opened
LEAVES = (
    str, bytes, bool, int, float, complex, type(None), numpy.ndarray, numpy.generic,
    types.ModuleType, type,
)  # fmt: skip


def stage_objects(version):
    """The classes whose objects hold a stage: the class of `version` and
    the handles by which its pieces are reached."""
    return (
        type(version), BoxHandle, BubbleHandle, LineHandle, GraphHandle, Graphs, Definitions,
        BuilderPairs, PerchHandle, PerchBuilders,
    )  # fmt: skip


def held_by(record, stops=(), into_functions=True):
    """Every object a record holds, the record included: the items of a
    tuple, a list, a set or a mapping; of a function Numba compiled the
    Python function it compiled; of an object of a class of the package
    its attributes; and, with `into_functions`, of a function its closure,
    its defaults and the values of its namespace other than the builtins,
    the modules, the classes and the functions. A string, a number, an
    array, a module, a class and an object of a class in `stops` are held
    and not opened."""
    seen, stack, found = set(), [record], []
    while stack:
        held = stack.pop()
        if id(held) in seen:
            continue
        seen.add(id(held))
        found.append(held)
        if isinstance(held, LEAVES + tuple(stops)):
            continue
        if isinstance(held, collections.abc.Mapping):
            stack += list(held.keys()) + list(held.values())
        elif isinstance(held, (tuple, list, set, frozenset)):
            stack += list(held)
        elif isinstance(held, types.FunctionType):
            if into_functions:
                stack += [
                    cell.cell_contents for cell in held.__closure__ or () if cell_holds(cell)
                ]
                stack += list(held.__defaults__ or ())
                stack += list((held.__kwdefaults__ or {}).values())
                stack += [
                    value
                    for name, value in held.__globals__.items()
                    if name != "__builtins__"
                    and not isinstance(
                        value,
                        (types.ModuleType, type, types.FunctionType, types.BuiltinFunctionType),
                    )
                ]
        elif isinstance(getattr(held, "py_func", None), types.FunctionType):
            stack.append(held.py_func)
        elif isinstance(held, types.SimpleNamespace) or type(held).__module__.startswith(
            "bellman"
        ):
            stack += list(getattr(held, "__dict__", {}).values())
            stack += [
                getattr(held, name)
                for name in getattr(type(held), "__slots__", ())
                if hasattr(held, name)
            ]
    return found


def cell_holds(cell):
    """Whether a cell of a function's closure holds a value."""
    try:
        cell.cell_contents
    except ValueError:
        return False
    return True


def functions_of(record, stops=()):
    """The Python functions a record holds, by name; a function held only
    inside another function is not one of them."""
    return {
        held.__name__: held
        for held in held_by(record, stops, into_functions=False)
        if isinstance(held, types.FunctionType)
    }


def stated_derivatives(record):
    """The names of the functions of the pieces of kind `Derivative` of a
    record of a builder's kernels, one for each stated derivative."""
    return {
        piece.function.__name__
        for piece in record.pieces
        if piece.kind == "Derivative" and piece.function is not None
    }


@pytest.fixture(scope="module")
def adjuster_cons_with_egm_lines_calibrated(adjuster_cons_with_egm_lines):
    """A copy of the two-control durable-adjustment stage whose policy
    block writes its endogenous grid lines in the stage file itself,
    calibrated by the calibration file of the durables model."""
    return copy_native(adjuster_cons_with_egm_lines).calibrate(
        str(DURABLES / "calibration/durables.yml")
    )


@pytest.fixture(scope="module")
def cons_argmax_calibrated(cons_argmax):
    """A copy of the consumption stage whose maximization is its operative
    line, calibrated at ρ = 6."""
    return copy_native(cons_argmax).calibrate(FIRST_CALIBRATIONS["cons"])


@pytest.fixture(scope="module")
def sa_savings_calibrated(sa_savings):
    """A copy of the smooth-ambiguity savings stage at its first
    calibration."""
    return copy_native(sa_savings).calibrate(SA_SAVINGS_CALIBRATIONS[0])


@pytest.mark.parametrize(
    ("stage", "graph", "refused"),
    [
        pytest.param(
            "cons_methodized",
            "builder.bwd",
            {
                "cntn_to_dcsn:Evaluation",
                "dcsn_to_arvl:Evaluation",
                "policy.identification:Pullback",
                "policy:Evaluation",
            },
            id="cons-backward-builders-graph",
        ),
        pytest.param("cons_methodized", "builder.fwd", set(), id="cons-forward-builders-graph"),
        pytest.param(
            "adjuster_cons_with_egm_lines_calibrated",
            "builder.policy",
            {"choice:Aggregation", "Evaluation"},
            id="adjuster-policy-builder",
        ),
        pytest.param(
            "cons_argmax_calibrated",
            "builder.policy",
            {"optimality:Argmax", "Evaluation"},
            id="maximizing-policy-builder",
        ),
        pytest.param(
            "sa_savings_calibrated",
            "builder.policy",
            {
                "objective:Expectation:2",
                "objective:Expectation:1",
                "objective:Argmax",
                "Evaluation",
            },
            id="smooth-ambiguity-policy-builder",
        ),
    ],
)
def test_compile_kernel_refuses_exactly_the_operations_that_apply_no_explicit_function(
    request, stage, graph, refused
):
    """`compile_kernel` refuses under `kernel-target` each operation that
    applies no explicit function, an evaluation, an expectation, a choice
    or a relation with no explicit side, and compiles each other operation
    of the builders graph or the builder, whose kernel holds the Python
    text of the function."""
    handle = attrgetter(graph)(request.getfixturevalue(stage))
    keys = [str(key) for key in handle.primitives.list()]
    assert refused <= set(keys)
    for key in sorted(refused):
        with pytest.raises(ConstructionError) as refusal:
            handle.primitives[key].compile_kernel()
        assert refusal.value.rule == "kernel-target", key
    for key in keys:
        if key not in refused:
            assert handle.primitives[key].kernel().python is not None, key
            # the operation compiles; a refusal fails the test
            handle.primitives[key].compile_kernel()


@pytest.mark.parametrize("builder", ["policy", "bwd"], ids=["policy-builder", "decision-builder"])
def test_the_record_of_a_builders_kernels_is_a_named_tuple_that_holds_no_object_of_the_stage(
    cons_methodized, builder
):
    """The record that `kernels()` answers for the policy builder or the
    backward decision builder is a named tuple, and no object that it holds
    is a stage or a handle of a piece of one."""
    record = getattr(cons_methodized.dcsn.builder, builder).kernels()
    stops = stage_objects(cons_methodized)
    assert isinstance(record, tuple) and hasattr(type(record), "_fields")
    assert [
        type(item).__name__ for item in held_by(record, stops) if isinstance(item, stops)
    ] == []


# the builders whose records the tests read, each as (the fixture of its
# stage, the path that reads the builder from the stage)
RECORDED_BUILDERS = [
    pytest.param("cons_methodized", "dcsn.builder.policy", id="cons-policy-builder"),
    pytest.param("cons_methodized", "dcsn.builder.bwd", id="cons-decision-builder"),
    pytest.param(
        "adjuster_cons_with_egm_lines_calibrated", "builder.policy", id="adjuster-policy-builder"
    ),
]


@pytest.mark.parametrize(("stage", "builder"), RECORDED_BUILDERS)
def test_the_record_of_a_builders_kernels_holds_the_function_of_each_operation_with_a_text(
    request, stage, builder
):
    """Apart from its stated derivatives, the record of a builder's kernels
    holds the function compiled from each operation whose kernel holds a
    Python text, and no other function, each with the source of that
    text."""
    handle = attrgetter(builder)(request.getfixturevalue(stage))
    record = handle.kernels()
    derivatives = stated_derivatives(record)
    functions = functions_of(record, stage_objects(handle.version))
    compiled = {
        piece.compile_kernel().__name__: definition_block(piece.kernel().python)
        for _, piece in explicit_operations(handle)
    }
    texts = {
        name: inspect.getsource(function)
        for name, function in functions.items()
        if name not in derivatives
    }
    assert texts == compiled


@pytest.mark.parametrize(
    ("stage", "builder", "key"),
    [
        pytest.param(
            "cons_methodized",
            "dcsn.builder.policy",
            "identification:Pullback",
            id="cons-identification",
        ),
        pytest.param(
            "cons_methodized", "dcsn.builder.policy", "Evaluation", id="cons-policy-evaluation"
        ),
        pytest.param(
            "cons_methodized", "dcsn.builder.bwd", "Evaluation", id="cons-decision-evaluation"
        ),
        pytest.param(
            "adjuster_cons_with_egm_lines_calibrated",
            "builder.policy",
            "choice:Aggregation",
            id="adjuster-joint-choice",
        ),
        pytest.param(
            "adjuster_cons_with_egm_lines_calibrated",
            "builder.policy",
            "Evaluation",
            id="adjuster-policy-evaluation",
        ),
    ],
)
def test_an_operation_that_compiles_to_no_function_stands_in_the_record_as_its_relation(
    request, stage, builder, key
):
    """An operation whose kernel `compile_kernel` refuses under
    `kernel-target` stands in the record of its builder's kernels as the
    relation that its kernel prints."""
    handle = attrgetter(builder)(request.getfixturevalue(stage))
    with pytest.raises(ConstructionError) as refused:
        handle[key].compile_kernel()
    assert refused.value.rule == "kernel-target"
    record = handle.kernels()
    relation = str(handle[key].kernel())
    texts = [
        held for held in held_by(record, stage_objects(handle.version)) if isinstance(held, str)
    ]
    assert relation in texts or relation in str(record)


# the program that a new process runs on the records and texts that the test
# saves: it reads each record, which cloudpickle saved, and each set of source
# texts, which pickle saved, makes each text's function in a namespace holding
# NumPy alone, and prints the value of every function of both at arguments
# 2.0
READ_THE_RECORDS = """\
import json, pickle, sys, types
import numpy

def functions(held, found):
    if isinstance(held, types.FunctionType):
        found[held.__name__] = held
    elif isinstance(held, dict):
        [functions(value, found) for value in held.values()]
    elif isinstance(held, (tuple, list)):
        [functions(value, found) for value in held]
    elif type(held).__module__.startswith("bellman"):
        [functions(value, found) for value in getattr(held, "__dict__", {}).values()]
    return found

def at_twos(function):
    value = function(*[2.0] * function.__code__.co_argcount)
    return numpy.asarray(value, dtype=float).ravel().tolist()

answers = {}
for builder, held in json.load(open(sys.argv[1], encoding="utf-8")).items():
    record = pickle.loads(bytes.fromhex(held["record"]))
    assert type(record).__name__ == held["type"]
    assert list(record._fields) == held["fields"]
    made = {}
    for name, text in pickle.loads(bytes.fromhex(held["texts"])).items():
        namespace = {"np": numpy}
        exec(text, namespace)
        made[name] = namespace[name]
    answers[builder] = [{name: at_twos(f) for name, f in functions(record, {}).items()},
                        {name: at_twos(f) for name, f in made.items()}]
print(json.dumps(answers))
"""


def test_a_new_process_with_numpy_alone_gives_the_values_of_the_functions_of_two_records(
    cons_methodized, tmp_path
):
    """A new process reads the records of the policy builder's and of the
    decision builder's kernels, which cloudpickle saved, and the source
    texts of their functions, which pickle saved, makes from each text a
    function in a namespace that holds NumPy alone, and each function of a
    record and of a text gives there the value that it gives in this
    process."""
    stops = stage_objects(cons_methodized)
    saved, expected = {}, {}
    for builder in ("policy", "bwd"):
        record = getattr(cons_methodized.dcsn.builder, builder).kernels()
        functions = functions_of(record, stops)
        texts = {name: inspect.getsource(function) for name, function in functions.items()}
        saved[builder] = {
            "record": cloudpickle.dumps(record).hex(),
            "texts": pickle.dumps(texts).hex(),
            "type": type(record).__name__,
            "fields": list(type(record)._fields),
        }
        expected[builder] = {name: at_twos(function) for name, function in functions.items()}
    (tmp_path / "saved.json").write_text(json.dumps(saved), encoding="utf-8")
    done = run_in_a_new_process(READ_THE_RECORDS, tmp_path / "saved.json")
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == {
        builder: [expected[builder], expected[builder]] for builder in saved
    }


# the folder of the portfolio-consumption application
APPLICATION = ROOT / "applications/cons-port"


# grid settings other than those of
# applications/cons-port/declaration/settings/cons.yml: fewer points on both
# grids, other bounds of the grid of resources and a lower upper bound of the
# savings grid; the methods file gives both grids the multi-exponential
# spacing, as it does at the settings of that file
CHANGED_GRIDS = {
    "n_m": 60, "m_min": 0.05, "m_max": 8.0,
    "n_a": 300, "a_min": 1.0e-6, "a_max": 50.0,
}  # fmt: skip


@pytest.fixture(scope="module")
def cons_port_tool():
    """The modules `cons_port_tool` of applications/cons-port/code and
    `asva.egm_1d` of packages/asva, imported with both folders on the
    module path."""
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(ROOT / "packages/asva"))
        patch.syspath_prepend(str(APPLICATION / "code"))
        adapter = importlib.import_module("asva.egm_1d")
        tool = importlib.import_module("cons_port_tool")
        yield types.SimpleNamespace(adapter=adapter, tool=tool)


@pytest.fixture(scope="module")
def cons_port_stages():
    """The consumption stage of cons-port with its methods file, bound at
    two sets of values by name: `reference`, the calibration and the grid
    settings with which the application's reference solution was computed,
    and `changed`, the calibration ρ = 2 and the changed grids."""
    methods = str(APPLICATION / "declaration/stages/cons/methods.bl")
    # the methods file of cons-port restates the signature of the policy
    # builder of the consumption stage beside it, so it is bound to that
    # stage file
    stage = elaborate_stage(load_stage(str(APPLICATION / "declaration/stages/cons/cons.bl")))
    bindings = {
        "reference": (
            str(APPLICATION / "declaration/calibration/portfolio.yml"),
            str(APPLICATION / "declaration/settings/cons.yml"),
        ),
        "changed": (SECOND_CALIBRATIONS["cons"], CHANGED_GRIDS),
    }
    return {
        name: copy_native(stage).calibrate(calibration).methodize(methods).configure(settings)
        for name, (calibration, settings) in bindings.items()
    }


BINDINGS = ["reference", "changed"]


BINDING_IDS = ["calibration-and-grids-of-the-reference", "second-calibration-and-changed-grids"]


@pytest.mark.parametrize("binding", BINDINGS, ids=BINDING_IDS)
def test_the_cons_port_tool_builds_its_step_by_one_call_of_egm_on_two_records_and_two_grids(
    cons_port_tool, cons_port_stages, monkeypatch, binding
):
    """The cons-port tool builds the endogenous grid operator of its
    consumption stage by one call of asva's `egm` from this checkout, on the
    record of the policy builder's kernels, the record of the decision
    builder's kernels less its stated derivative, the savings grid and the
    evaluation grid."""
    adapter, tool = cons_port_tool.adapter, cons_port_tool.tool
    assert Path(adapter.__file__).resolve().is_relative_to(ROOT.resolve()), adapter.__file__
    stage = cons_port_stages[binding]
    original, calls = adapter.egm, []

    def counted(*arguments, **keywords):
        calls.append(inspect.signature(original).bind(*arguments, **keywords))
        return original(*arguments, **keywords)

    monkeypatch.setattr(adapter, "egm", counted)
    for module in (sys.modules["asva"], tool):
        for name, value in list(vars(module).items()):
            if value is original:
                monkeypatch.setattr(module, name, counted)
    # the complete mapping of the fields that the stage takes in at its
    # continuation perch: the value zero after the terminal decision
    tool.stage_operator(stage, {"V[>]": tool.zero_value})
    assert len(calls) == 1, calls
    policy, decision, savings, evaluation = list(calls[0].arguments.values())[:4]
    stops = stage_objects(stage)
    assert sorted(functions_of(policy, stops)) == sorted(
        functions_of(stage.builder.policy.kernels(), stops)
    )
    kernels = stage.dcsn.builder.bwd.kernels()
    operators = kernels._replace(
        pieces=tuple(piece for piece in kernels.pieces if piece.kind != "Derivative")
    )
    assert sorted(functions_of(decision, stops)) == sorted(functions_of(operators, stops))
    numpy.testing.assert_array_equal(savings, tool.savings_grid(stage.builder.policy.kernels()))
    numpy.testing.assert_array_equal(evaluation, tool.evaluation_grid(kernels))


def step_composed_from_the_kernels(stage, tool, continuation):
    """The endogenous grid step on the consumption stage of cons-port,
    composed here from its four compiled kernels, each given the parameter
    values of its kernel: on the savings grid the candidate line gives
    consumption and the grid line the resources it is chosen at;
    consumption is interpolated onto the evaluation grid and held in
    (1e-10, m_d - 1e-10); savings follow from the law of motion, held to
    the savings grid; the value from the aggregation, and the marginal value
    c^(-ρ)."""
    resources = tool.evaluation_grid(stage.dcsn.builder.bwd.kernels())
    savings = tool.savings_grid(stage.builder.policy.kernels())
    bound = {
        key: (
            operation(stage, builder, key).compile_kernel(),
            operation(stage, builder, key).kernel().parameter_values,
        )
        for builder, key in STEP_KERNELS
    }

    def apply(key, *arguments):
        function, values = bound[key]
        return function(*arguments, *values)

    chosen = apply(
        "InvEuler:Aggregation", continuation(savings), savings, continuation.dV(savings)
    )
    at = apply("grid:Aggregation", chosen, savings)
    order = numpy.argsort(at)
    c = numpy.clip(numpy.interp(resources, at[order], chosen[order]), 1e-10, resources - 1e-10)
    a = numpy.clip(apply("Pullback", resources, c), savings[0], savings[-1])
    continued = continuation(a)
    value = apply("Aggregation", continued, resources, c)
    marginal = c ** (-stage.par["ρ"].value)
    return {
        "grid": resources,
        "values": numpy.where(c > 0, value, tool.LOW + continued),
        "dvalues": numpy.where(c > 0, marginal, tool.HIGH),
        "c": c,
        "a": a,
    }


@pytest.mark.parametrize("binding", BINDINGS, ids=BINDING_IDS)
def test_the_step_of_the_cons_port_tool_reads_no_stage_and_gives_the_step_of_its_four_kernels(
    cons_port_tool, cons_port_stages, monkeypatch, binding
):
    """The endogenous grid operator that the cons-port tool builds with
    asva from this checkout reads no attribute of a stage while it
    computes, and gives on the evaluation grid the values, the marginal
    values, the consumption and the savings of the step composed from the
    four compiled kernels."""
    adapter, tool = cons_port_tool.adapter, cons_port_tool.tool
    assert Path(adapter.__file__).resolve().is_relative_to(ROOT.resolve()), adapter.__file__
    stage = cons_port_stages[binding]
    # the continuation's grid: twice the points of the savings grid, up to
    # its upper bound
    grid = tool.expmult_grid(stage.settings["a_max"].value, 2 * stage.settings["n_a"].value)
    continuation = tool.terminal_value(stage, grid)
    operator = tool.stage_operator(stage, {"V[>]": continuation})
    before = step_composed_from_the_kernels(stage, tool, continuation)

    def refuse(self, name):
        raise AssertionError(f"the operator read the stage's attribute {name!r}")

    with monkeypatch.context() as guard:
        guard.setattr(type(stage), "__getattribute__", refuse, raising=False)
        solved = operator(continuation)
    numpy.testing.assert_array_equal(solved.grid, before["grid"])
    numpy.testing.assert_allclose(
        [solved.values, solved.dvalues, solved.policy["c"], solved.policy["a"]],
        [before["values"], before["dvalues"], before["c"], before["a"]],
        rtol=1e-12,
        atol=1e-12,
    )


# the lesson of the tutorials that composes kernels, compiles them with
# Numba and passes them a second calibration
LESSON = "topics/kernels"


def test_the_lesson_on_kernels_is_recorded_as_executed_without_failures_for_its_notebook():
    """The record tutorials/lessons.json holds the lesson topics/kernels as
    executed to its end with no failure, at the digest of its present
    notebook."""
    record = json.loads((ROOT / "tutorials/lessons.json").read_text(encoding="utf-8"))
    entry = record.get(LESSON)
    assert entry is not None, f"execute tutorials/tools/execute_lessons.py --record {LESSON}"
    assert entry["status"] == "completed" and entry["failures"] == [], entry["failures"]
    lesson = ROOT / "tutorials" / f"{LESSON}.ipynb"
    assert entry["sha256"] == hashlib.sha256(lesson.read_bytes()).hexdigest()
