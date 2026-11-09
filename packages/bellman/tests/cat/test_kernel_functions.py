"""The acceptance file of lane E of the internal developer release 0.01,
kernels as clean functions (the second layer of the tests,
`packages/bellman/README.md` §8): one test for each of the six items of
`kernels-as-functions.md` §9.

A primitive operator's `kernel()` answers, besides its printed text, `python`,
the source text of one plain function whose arguments are the kernel's own in
printed order followed by each parameter the kernel reads, in declaration
order; `parameters`, the names of those parameters; and `parameter_values`,
the values the version's calibration binds to them, in the same order.
`compile_kernel()` answers the function that text defines, attached to no
stage. A builder answers `kernels()`, one plain record of its kernels from
which a numerical operator is built with no stage in hand; `egm` of
`packages/asva/asva/egm_1d.py` builds the endogenous grid step of the
consumption stage from the records of its policy builder and of its backward
decision builder and from two grids.

Every item reads the consumption stage
`applications/portfolio-choice/declaration/stages/cons/cons.bl` calibrated at
ρ = 6. Item 5 also reads the numerical tool of the
portfolio-consumption application,
`applications/cons-port/code/cons_port_tool.py`, and imports asva from this
checkout; item 6 reads the policy builders of three further stages, each
holding a row of a kind with no explicit function, and the record of the
kernels lesson, `tutorials/lessons.json`.
"""

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
from pathlib import Path

import cloudpickle
import numba
import numpy
import pytest
from conftest import (
    CORPUS,
    CORPUS_CALIBRATIONS,
    CONS_METHODS,
    DURABLES,
    ROOT,
    SA_SAVINGS_CALIBRATIONS,
    SECOND_CALIBRATIONS,
)

from bellman.native.hypergraphs import copy_native
from bellman.stage import elaborate_stage, load_stage
from bellman.refusals import ConstructionError
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

APPLICATION = ROOT / "applications/cons-port"
LESSON = "topics/kernels"
# the four kernels the cons-port tool composes into its endogenous grid
# step, each as (the path of `stage.dcsn.builder` that reads the builder,
# operation): the inverse Euler row and the grid row of the policy builder,
# the law of motion and the aggregation of the backward decision builder
COMPOSED = (
    ("policy", "InvEuler:Aggregation"),
    ("policy", "grid:Aggregation"),
    ("bwd", "Pullback"),
    ("bwd", "Aggregation"),
)
# grid settings other than those of
# applications/cons-port/declaration/settings/cons.yml: fewer points, other
# bounds and the multi-exponential spacing
CHANGED_GRIDS = {
    "n_m": 60, "m_min": 0.05, "m_max": 8.0,
    "n_a": 300, "a_min": 1.0e-6, "a_max": 50.0,
}
# what a record walked by `held_by` holds without being opened
LEAVES = (str, bytes, bool, int, float, complex, type(None), numpy.ndarray,
          numpy.generic, types.ModuleType, type)


def stage_objects(version):
    """The classes whose objects hold a stage: the class of `version` and
    the handles by which its pieces are reached."""
    return (type(version), BoxHandle, BubbleHandle, LineHandle, GraphHandle,
            Graphs, Definitions, BuilderPairs, PerchHandle, PerchBuilders)


def operation(version, builder, key):
    """The operation `key` of the backward builder that the path `builder`
    of `stage.dcsn.builder` reads, the policy builder `policy` or the
    backward decision builder `bwd`."""
    return getattr(version.dcsn.builder, builder)[key]


def definition_block(text):
    """The lines of a kernel's source text from the line at the first column
    that opens its function to its last line that is not blank."""
    lines = text.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.startswith("def "))
    block = lines[start:]
    while block and not block[-1].strip():
        block.pop()
    return "".join(block)


def compiled_operations(graph):
    """(key, operation, function) of each operation of a builders graph or a
    builder, at the primitive grain, whose kernel compiles; an operation
    refused under `kernel-target` is left out."""
    found = []
    for key in graph.primitives.list():
        piece = graph.primitives[str(key)]
        try:
            found.append((str(key), piece, piece.compile_kernel()))
        except ConstructionError as refused:
            assert refused.rule == "kernel-target", (str(key), refused.rule)
    return found


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
                stack += [cell.cell_contents for cell in held.__closure__ or ()
                          if cell_holds(cell)]
                stack += list(held.__defaults__ or ())
                stack += list((held.__kwdefaults__ or {}).values())
                stack += [value for name, value in held.__globals__.items()
                          if name != "__builtins__" and not isinstance(value, (
                              types.ModuleType, type, types.FunctionType,
                              types.BuiltinFunctionType))]
        elif isinstance(getattr(held, "py_func", None), types.FunctionType):
            stack.append(held.py_func)
        elif isinstance(held, types.SimpleNamespace) or type(held).__module__.startswith("bellman"):
            stack += list(getattr(held, "__dict__", {}).values())
            stack += [getattr(held, name) for name in getattr(type(held), "__slots__", ())
                      if hasattr(held, name)]
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
    return {held.__name__: held for held in held_by(record, stops, into_functions=False)
            if isinstance(held, types.FunctionType)}


def as_floats(value):
    """A kernel's value, one number or a tuple of them, as a list of
    floats."""
    return numpy.asarray(value, dtype=float).ravel().tolist()


def at_twos(function):
    """The function's value with each of its arguments 2.0, as a list of
    floats."""
    return as_floats(function(*[2.0] * function.__code__.co_argcount))


def run_in_a_new_process(code, *arguments, path=()):
    """What a new Python process prints, run with `code`, the given
    arguments and the folders `path` before the import path of this
    process."""
    folders = [str(folder) for folder in path] + [folder for folder in sys.path if folder]
    done = subprocess.run(
        [sys.executable, "-c", code, *map(str, arguments)], capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(folders)))
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_item_1_numba_compiles_each_kernel_the_tool_composes_in_one_call(cons_methodized):
    compiled = {}
    for builder, key in COMPOSED:
        kernel = operation(cons_methodized, builder, key).kernel()
        function = numba.njit(operation(cons_methodized, builder, key).compile_kernel())
        count = len(inspect.signature(function.py_func).parameters) - len(kernel.parameters)
        # one call of numba.njit, with no function the kernel calls compiled
        # beforehand; the compiled function evaluates on numbers and on
        # arrays
        at_numbers = function(*[2.0] * count, *kernel.parameter_values)
        on_arrays = function(*[numpy.full(3, 2.0)] * count, *kernel.parameter_values)
        numbers = numpy.asarray(at_numbers, dtype=float)[..., None]
        numpy.testing.assert_array_equal(
            numpy.asarray(on_arrays, dtype=float),
            numpy.broadcast_to(numbers, numpy.shape(on_arrays)))
        compiled[key] = function
    assert compiled["Pullback"](3.0, 1.0) == 2.0
    assert compiled["Aggregation"](2.0, 3.0, 1.0, 6.0) == 1.8


def test_item_2_the_source_is_the_text_and_the_text_does_not_change(
        cons_methods_only, elaborate_text, text_of):
    first = copy_native(cons_methods_only).calibrate(CORPUS_CALIBRATIONS["cons"])
    again = elaborate_text(text_of("cons"), CORPUS["cons"]).methodize(CONS_METHODS).calibrate(CORPUS_CALIBRATIONS["cons"])
    other = copy_native(cons_methods_only).calibrate(SECOND_CALIBRATIONS["cons"])
    for direction in ("bwd", "fwd"):
        compiled = compiled_operations(getattr(first.builder, direction))
        assert compiled, direction
        for key, piece, function in compiled:
            text = piece.kernel().python
            assert inspect.getsource(function) == definition_block(text), key
            for version in (again, other):
                held = getattr(version.builder, direction).primitives[key].kernel().python
                assert held.encode("utf-8") == text.encode("utf-8"), key
    # the four kernels the cons-port tool composes are among them
    assert {key for key, _, _ in compiled_operations(first.builder.bwd)} >= {
        "policy.InvEuler:Aggregation", "policy.grid:Aggregation",
        "cntn_to_dcsn:Pullback", "cntn_to_dcsn:Aggregation"}


def test_item_3_cloudpickle_saves_a_kernel_and_pickle_loads_its_text_in_a_new_process(
        cons_methodized, tmp_path, monkeypatch):
    expected, pickled = {}, {}
    for index, (builder, key) in enumerate(COMPOSED):
        kernel = operation(cons_methodized, builder, key).kernel()
        function = operation(cons_methodized, builder, key).compile_kernel()
        count = len(inspect.signature(function).parameters) - len(kernel.parameters)
        values = [2.0] * count + list(kernel.parameter_values)
        # cloudpickle saves and loads the function made in memory
        restored = cloudpickle.loads(cloudpickle.dumps(function))
        assert as_floats(restored(*values)) == as_floats(function(*values)), key
        # the text written to a file of the reader's choosing is a module,
        # whose function the standard pickle saves by the module's name
        name = f"cons_kernel_{index}"
        (tmp_path / f"{name}.py").write_text(kernel.python, encoding="utf-8")
        specification = importlib.util.spec_from_file_location(name, tmp_path / f"{name}.py")
        module = importlib.util.module_from_spec(specification)
        monkeypatch.setitem(sys.modules, name, module)
        specification.loader.exec_module(module)
        pickled[name] = (pickle.dumps(getattr(module, function.__name__)).hex(), values)
        expected[name] = as_floats(function(*values))
    (tmp_path / "pickled.json").write_text(json.dumps(pickled), encoding="utf-8")
    code = (
        "import json, pickle, sys\n"
        "import numpy\n"
        "pickled = json.load(open(sys.argv[1], encoding='utf-8'))\n"
        "loaded = {name: pickle.loads(bytes.fromhex(data))(*values)\n"
        "          for name, (data, values) in pickled.items()}\n"
        "print(json.dumps({name: numpy.asarray(value, dtype=float).ravel().tolist()\n"
        "                  for name, value in loaded.items()}))\n")
    written = run_in_a_new_process(code, tmp_path / "pickled.json", path=[tmp_path])
    assert json.loads(written) == expected


def test_item_4_a_new_calibration_reaches_the_function_compiled_once(cons_methods_only, cons_methodized):
    at_two = copy_native(cons_methods_only).calibrate({"ρ": 2.0})
    for builder, key in COMPOSED:
        six = operation(cons_methodized, builder, key).kernel()
        two = operation(at_two, builder, key).kernel()
        assert two.python == six.python, key
        assert two.parameters == six.parameters, key
        assert two.parameter_values == tuple(2.0 for _ in two.parameters), key
    aggregator_six = operation(cons_methodized, "bwd", "Aggregation").kernel()
    aggregator_two = operation(at_two, "bwd", "Aggregation").kernel()
    assert aggregator_six.parameter_values == (6.0,)
    assert aggregator_two.parameter_values == (2.0,)
    compiled = numba.njit(operation(cons_methodized, "bwd", "Aggregation").compile_kernel())
    # at V≻ = 2, m_d = 3 and c = 0.5: u(0.5) + 2 = 0.5^(−5)/(−5) + 2 and
    # du(0.5) = 0.5^(−6) at ρ = 6; 0.5^(−1)/(−1) + 2 and 0.5^(−2) at ρ = 2
    six_values = compiled(2.0, 3.0, 0.5, *aggregator_six.parameter_values)
    two_values = compiled(2.0, 3.0, 0.5, *aggregator_two.parameter_values)
    assert six_values == pytest.approx(-4.4)
    assert two_values == pytest.approx(0.0)
    derivative_six = next(piece.function for piece in cons_methodized.dcsn.builder.bwd.kernels().pieces
                          if piece.kind == "Derivative")
    derivative_two = next(piece.function for piece in at_two.dcsn.builder.bwd.kernels().pieces
                          if piece.kind == "Derivative")
    marginal = numba.njit(derivative_six)
    assert marginal(2.0, 3.0, 0.5, 6.0) == 64.0
    assert marginal(2.0, 3.0, 0.5, 2.0) == derivative_two(2.0, 3.0, 0.5, 2.0) == 4.0
    assert len(marginal.signatures) == 1
    numpy.testing.assert_array_equal(
        marginal(numpy.full(3, 2.0), numpy.full(3, 3.0), numpy.full(3, 0.5), 6.0),
        numpy.full(3, 64.0))
    own = operation(at_two, "bwd", "Aggregation").compile_kernel()
    assert as_floats(two_values) == as_floats(
        own(2.0, 3.0, 0.5, *aggregator_two.parameter_values))
    # the second calibration's values reached the compiled code without a
    # second compilation
    assert len(compiled.signatures) == 1


def step_as_before(stage, tool, continuation):
    """The endogenous grid step on the consumption stage as the cons-port
    tool composed it before its operator was built from the records (its
    function `egm` at c3486f10f): the four compiled kernels, each given the
    parameter values of its kernel, composed on the evaluation grid and the
    savings grid, consumption held in (1e-10, m_d − 1e-10) and savings held
    to the savings grid."""
    resources, savings = tool.evaluation_grid(stage), tool.savings_grid(stage)
    bound = {key: (operation(stage, builder, key).compile_kernel(),
                   operation(stage, builder, key).kernel().parameter_values)
             for builder, key in COMPOSED}

    def apply(key, *arguments):
        function, values = bound[key]
        return function(*arguments, *values)
    chosen = apply("InvEuler:Aggregation", continuation(savings), savings, continuation.dV(savings))
    at = apply("grid:Aggregation", chosen, savings)
    order = numpy.argsort(at)
    c = numpy.clip(numpy.interp(resources, at[order], chosen[order]), 1e-10, resources - 1e-10)
    a = numpy.clip(apply("Pullback", resources, c), savings[0], savings[-1])
    continued = continuation(a)
    value = apply("Aggregation", continued, resources, c)
    marginal = c ** (-stage.par["ρ"].value)
    return {"grid": resources, "values": numpy.where(c > 0, value, tool.LOW + continued),
            "dvalues": numpy.where(c > 0, marginal, tool.HIGH), "c": c, "a": a}


# the program a new process runs on the records and texts of item 5: it reads
# each record, which cloudpickle saved, and each set of source texts, which
# pickle saved, makes each text's function in a namespace holding NumPy alone,
# and prints the value of every function of both at arguments 2.0
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


def test_item_5_egm_builds_the_tools_operator_from_two_records_free_of_the_stage(
        cons_methods_only, tmp_path, monkeypatch):
    version = copy_native(cons_methods_only).calibrate(CORPUS_CALIBRATIONS["cons"])
    stops = stage_objects(version)
    records = {"policy": version.dcsn.builder.policy.kernels(),
               "bwd": version.dcsn.builder.bwd.kernels()}
    saved, expected = {}, {}
    for builder, record in records.items():
        assert isinstance(record, tuple) and hasattr(type(record), "_fields"), builder
        held = [type(item).__name__ for item in held_by(record, stops) if isinstance(item, stops)]
        assert held == [], builder
        functions = functions_of(record, stops)
        operations = compiled_operations(getattr(version.dcsn.builder, builder))
        compiled = {function.__name__: definition_block(piece.kernel().python)
                    for _, piece, function in operations}
        # a value builder's record also lists one piece of kind `Derivative`
        # per stated derivative, after its primitive operators (AMD-MB-001
        # §4.3, D4); no primitive compiles it, so the comparison with the
        # primitives leaves its function out
        derivatives = {piece.function.__name__ for piece in record.pieces
                       if piece.kind == "Derivative" and piece.function is not None}
        assert sorted(set(functions) - derivatives) == sorted(compiled), builder
        # the source texts of its functions, which the standard pickle saves
        texts = {name: inspect.getsource(function) for name, function in functions.items()}
        assert {name: text for name, text in texts.items() if name not in derivatives} == compiled, builder
        assert pickle.loads(pickle.dumps(texts)) == texts, builder
        saved[builder] = {"record": cloudpickle.dumps(record).hex(),
                          "texts": pickle.dumps(texts).hex(),
                          "type": type(record).__name__, "fields": list(type(record)._fields)}
        expected[builder] = {name: at_twos(function) for name, function in functions.items()}
    (tmp_path / "saved.json").write_text(json.dumps(saved), encoding="utf-8")
    answers = json.loads(run_in_a_new_process(READ_THE_RECORDS, tmp_path / "saved.json"))
    assert answers == {builder: [expected[builder], expected[builder]] for builder in records}

    # the cons-port tool's endogenous grid operator is built by one call of
    # egm of packages/asva/asva/egm_1d.py, read from this checkout
    monkeypatch.syspath_prepend(str(ROOT / "packages/asva"))
    monkeypatch.syspath_prepend(str(APPLICATION / "code"))
    adapter = importlib.import_module("asva.egm_1d")
    assert Path(adapter.__file__).resolve().is_relative_to(ROOT.resolve()), adapter.__file__
    tool = importlib.import_module("cons_port_tool")
    original, calls = adapter.egm, []

    def counted(*arguments, **keywords):
        calls.append(inspect.signature(original).bind(*arguments, **keywords))
        return original(*arguments, **keywords)
    monkeypatch.setattr(adapter, "egm", counted)
    for module in (sys.modules["asva"], tool):
        for name, value in list(vars(module).items()):
            if value is original:
                monkeypatch.setattr(module, name, counted)

    def refuse(self, name):
        raise AssertionError(f"the constructed operator read the stage's attribute {name!r}")
    # the calibration and the grids of the fixed reference, then a changed
    # calibration and changed grid settings
    methods = str(APPLICATION / "declaration/stages/cons/methods.bl")
    reference = (str(APPLICATION / "declaration/calibration/portfolio.yml"),
                 str(APPLICATION / "declaration/settings/cons.yml"))
    # the methods file binds the block file beside it,
    # whose header is the policy builder's of the folder's own
    # consumption stage, so that stage is the one bound (MB-T23)
    demonstration = elaborate_stage(load_stage(str(
        ROOT / "applications/cons-port/declaration/stages/cons/cons.bl")))
    for calibration, settings in (reference, (SECOND_CALIBRATIONS["cons"], CHANGED_GRIDS)):
        stage = copy_native(demonstration).calibrate(calibration).methodize(methods).configure(settings)
        calls.clear()
        operator = tool.stage_operator(stage)
        assert len(calls) == 1, calls
        policy, decision, savings, evaluation = list(calls[0].arguments.values())[:4]
        assert sorted(functions_of(policy, stops)) == sorted(
            functions_of(stage.builder.policy.kernels(), stops))
        # the decision builder's record less its pieces of kind `Derivative`,
        # one per stated derivative, which the tool keeps out of asva's
        # record (AMD-MB-001 §4.3, D4)
        kernels = stage.dcsn.builder.bwd.kernels()
        operators = kernels._replace(
            pieces=tuple(piece for piece in kernels.pieces if piece.kind != "Derivative"))
        assert sorted(functions_of(decision, stops)) == sorted(functions_of(operators, stops))
        numpy.testing.assert_array_equal(savings, tool.savings_grid(stage))
        numpy.testing.assert_array_equal(evaluation, tool.evaluation_grid(stage))
        grid = tool.expmult_grid(stage.settings["a_max"].value, 2 * stage.settings["n_a"].value)
        continuation = tool.terminal_value(stage, grid)
        before = step_as_before(stage, tool, continuation)
        # no attribute of a stage is read while the operator computes
        with monkeypatch.context() as guard:
            guard.setattr(type(stage), "__getattribute__", refuse, raising=False)
            solved = operator(continuation)
        numpy.testing.assert_array_equal(solved.grid, before["grid"])
        for name, computed in (("values", solved.values), ("dvalues", solved.dvalues),
                               ("c", solved.policy["c"]), ("a", solved.policy["a"])):
            numpy.testing.assert_allclose(computed, before[name], rtol=1e-12, atol=1e-12,
                                          err_msg=name)


# one policy builder of each kind of row that has no explicit function: the
# identification and the evaluation (cons), a joint solve's residual system
# (adjuster_cons), a choice (cons_argmax) and an expectation (sa_savings)
WITHOUT = {
    "cons": ("identification:Pullback", "Evaluation"),
    "adjuster_cons": ("choice:Aggregation", "Evaluation"),
    "cons_argmax": ("optimality:Argmax",),
    "sa_savings": ("objective:Expectation:1",),
}


def test_item_6_a_row_without_a_function_refuses_and_stands_as_its_relation(
        cons_methodized, adjuster_cons, cons_argmax, sa_savings, elaborate_text, text_of):
    versions = {
        "cons": cons_methodized,
        "adjuster_cons": copy_native(adjuster_cons).calibrate(
            str(DURABLES / "calibration/durables.yml")
        ),
        "cons_argmax": copy_native(cons_argmax).calibrate(CORPUS_CALIBRATIONS["cons"]),
        "sa_savings": copy_native(sa_savings).calibrate(SA_SAVINGS_CALIBRATIONS[0]),
    }
    for name, keys in WITHOUT.items():
        for key in keys:
            with pytest.raises(ConstructionError) as refused:
                versions[name].builder.policy[key].compile_kernel()
            assert refused.value.rule == "kernel-target", (name, key)
    # in the record of a builder, a row with no explicit function stands as
    # its printed relation and holds no function; every other row holds the
    # function its kernel compiles to
    for name, builder in (("cons", cons_methodized.builder.policy),
                          ("cons", cons_methodized.dcsn.builder.bwd),
                          ("adjuster_cons", versions["adjuster_cons"].builder.policy)):
        record = builder.kernels()
        stops = stage_objects(builder.version)
        texts = [held for held in held_by(record, stops) if isinstance(held, str)]
        compiled = set()
        for key in builder.list():
            piece = builder[str(key)]
            try:
                compiled.add(piece.compile_kernel().__name__)
            except ConstructionError as refused:
                assert refused.rule == "kernel-target", (name, str(key))
                relation = str(piece.kernel())
                assert relation in texts or relation in str(record), (name, str(key), relation)
        derivatives = {piece.function.__name__ for piece in record.pieces
                       if piece.kind == "Derivative" and piece.function is not None}
        assert sorted(set(functions_of(record, stops)) - derivatives) == sorted(compiled), name
    # the inverse Euler row compiles its explicit side,
    # 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻) = 𝑑𝑉≻^(−1/ρ), with the clause ⟂ a >= 0 on its line and
    # without it
    clause = " ⟂ a >= 0"
    addition = CONS_METHODS.read_text()
    assert addition.count(clause) == 1
    without_clause = elaborate_text(text_of("cons"), CORPUS["cons"]).methodize(
        {"text": addition.replace(clause, ""), "origin": str(CONS_METHODS)})
    marginal, saving = numpy.array([2.0, 0.25, 0.8]), numpy.array([0.5, 1.0, 4.0])
    for version in (cons_methodized, without_clause.calibrate(CORPUS_CALIBRATIONS["cons"])):
        row = version.builder.policy["InvEuler:Aggregation"]
        values = row.kernel().parameter_values
        numpy.testing.assert_allclose(row.compile_kernel()(numpy.zeros_like(saving), saving, marginal, *values),
                                      marginal ** (-1 / 6.0))
    # the lesson executes and is recorded
    record = json.loads((ROOT / "tutorials/lessons.json").read_text(encoding="utf-8"))
    entry = record.get(LESSON)
    assert entry is not None, f"execute tutorials/tools/execute_lessons.py --record {LESSON}"
    assert entry["status"] == "completed" and entry["failures"] == [], entry["failures"]
    lesson = ROOT / "tutorials" / f"{LESSON}.ipynb"
    assert entry["sha256"] == hashlib.sha256(lesson.read_bytes()).hexdigest()
