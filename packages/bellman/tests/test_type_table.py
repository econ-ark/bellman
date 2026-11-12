"""The acceptance file of the table of types, `OBJECTS`, `SET_FORMS` and
`LIMITS` of `bellman.typing.type_table` (the second layer of the tests,
`packages/bellman/README.md` §8): one test for each of the five items of its
brief, and a sixth for the objects in whose type a form of a set is read.

A row of `OBJECTS` states one object of a stage, with a line of a file of
the repository that declares it, the record of the package that holds it and
the expression that reads it from the stage object. A row of `SET_FORMS`
states one constructor of a set expression, with a declaration that writes
it and the objects in whose type the package reads it. A row of `LIMITS`
states one limit of the language on a type, with a line that breaks it and
the rule of the refusal. The tests below run every row through the package:
each constructor has one row, each example lowers to its constructor and is
read in the types its row names, each line that breaks a limit is refused
under its rule, each record is read by import and each expression answers on
the stage of the file that holds its line.

The page `docs/Bellman-Sym/reference/types.md` is printed from the tables by
`docs/_hooks/reference_pages.py`, whose `--check` item 5 runs on that page.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from collections import Counter

from conftest import ROOT

from bellman.factory.elaboration import elaborate_stage
from bellman.factory.loading import load_stage
from bellman.refusal_catalogue import VOCABULARIES
from bellman.refusals import ConstructionError
from bellman.semantic_rules import resolve
from bellman.syntax import terms
from bellman.syntax.lower import parse_with_spans
from bellman.typing.type_table import LIMITS, OBJECTS, SET_FORMS, WITH_A_SET

HOOKS = ROOT / "docs" / "_hooks"
PAGE = "docs/Bellman-Sym/reference/types.md"

# the perfect-foresight application, whose stage file and gridded methods
# file hold most of the lines of `OBJECTS`, with its calibration file and
# values for the three settings of its grid of savings, which the
# application's module supplies and no file of its folder holds
PERFECT_FORESIGHT = "applications/consumption-perfect-foresight-crra/declaration"
STAGE_FILE = f"{PERFECT_FORESIGHT}/stages/perfect_foresight/perfect_foresight.bl"
METHODS_FILE = f"{PERFECT_FORESIGHT}/stages/perfect_foresight/methods.egm.bl"
CALIBRATION_FILE = f"{PERFECT_FORESIGHT}/calibration/perfect_foresight.yml"
GRID_OF_SAVINGS = {"n_a": 50, "a_min": -40.0, "a_max": 60.0}
# the buffer-stock stage, which declares a shock
BUFFER_STOCK = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"


def perfect_foresight():
    """The perfect-foresight stage with its gridded methods file read, its
    calibration file bound and the settings of its grid given values."""
    stage = elaborate_stage(load_stage(ROOT / STAGE_FILE))
    stage.methodize(ROOT / METHODS_FILE)
    stage.calibrate(ROOT / CALIBRATION_FILE)
    return stage.configure(GRID_OF_SAVINGS)


def buffer_stock():
    """The symbolic buffer-stock stage."""
    return elaborate_stage(load_stage(ROOT / BUFFER_STOCK))


# the stage on which an expression of `OBJECTS` is evaluated, by the file
# that holds the row's line
STAGES = {
    STAGE_FILE: perfect_foresight,
    METHODS_FILE: perfect_foresight,
    BUFFER_STOCK: buffer_stock,
}


def reported(problems):
    return "\n" + "\n".join(f"- {problem}" for problem in problems)


def every_rule():
    """Every rule of the three vocabularies the package refuses under."""
    return {rule for _, _, rules in VOCABULARIES for rule in rules}


def written_constructors():
    """The names of the constructors of a set expression that a file writes:
    the classes of `bellman.syntax.terms` under `setexpr`. The typed
    expressions define further classes under it in their own module, and no
    file writes one of those."""
    return {
        name
        for name, held in vars(terms).items()
        if inspect.isclass(held) and held is not terms.setexpr and issubclass(held, terms.setexpr)
    }


def declared_set(line):
    """The set that the lowering keeps for the one declaration `line`, read
    from the parsed line with no stage built."""
    term, _ = parse_with_spans(line + "\n", "t.bl")
    (domain,) = [
        held for held in term.items[-1].declaration.classifiers if isinstance(held, terms.Domain)
    ]
    return domain.space


def stage_record(text, methods=None):
    """The source record of a stage text, with one methods file where
    `methods` gives its text."""
    return {
        "stage": {"text": text, "origin": "t.bl"},
        "calibration": {},
        "settings": {},
        "methods": [] if methods is None else [{"text": methods, "origin": "methods.bl"}],
    }


def smallest_record(name, written):
    """The source record of the smallest stage text that writes the set
    `written` in the type of an object named `name` in `OBJECTS`: a
    parameter on its own line, a derived parameter defined from one
    parameter, a setting in a methods file, a field on the header of one
    block, a shock declared by its role word, and the argument of a
    function."""
    if name == "setting":
        return stage_record("@stage: t\n", f"@methods: t\nx : {written}\n")
    items = {
        "parameter": f"x : {written}\n",
        "derived parameter": f"β : (0,1)\nx : {written} := 2*β\n",
        "field": (
            f"[id=arvl_to_dcsn, (x : {written}) : !arvl -> (m : ℝ) : !dcsn] {{\n    m = 1\n}}\n"
        ),
        "shock": f"x : {written} @ !shck\n",
        "function": f"𝑓(x : {written}) := 1\n",
    }
    return stage_record("@stage: t\n" + items[name])


def is_read(record):
    """Whether the package reads the stage of `record` without a refusal."""
    try:
        elaborate_stage(record)
    except ConstructionError:
        return False
    return True


def test_item_1_every_constructor_of_a_set_expression_has_exactly_one_row():
    rows = Counter(row.constructor for row in SET_FORMS)
    written = written_constructors()
    problems = [f"the constructor {name} has no row" for name in sorted(written - set(rows))]
    problems += [
        f"the row {name} names no constructor of a set expression that a file writes"
        for name in sorted(set(rows) - written)
    ]
    problems += [
        f"the constructor {name} has {count} rows" for name, count in rows.items() if count > 1
    ]
    assert not problems, reported(problems)


def test_item_2_each_example_lowers_to_a_declaration_whose_set_is_of_the_rows_constructor():
    problems = []
    for row in SET_FORMS:
        kept = type(declared_set(row.example)).__name__
        if kept != row.constructor:
            problems.append(
                f"the example {row.example!r} of {row.constructor} lowers to the set of a {kept}"
            )
    assert not problems, reported(problems)


def test_item_3_each_line_that_breaks_a_limit_is_refused_under_the_rows_rule():
    assert LIMITS, "the table holds no limit"
    rules = every_rule()
    problems = []
    for row in LIMITS:
        if row.rule not in rules:
            problems.append(f"{row.line!r}: {row.rule} is no rule of the refusal catalogue")
        if "\n" in row.line:
            problems.append(f"{row.line!r} holds more than one line")
            continue
        try:
            elaborate_stage(stage_record(f"@stage: t\n{row.line}\n"))
        except ConstructionError as refused:
            if refused.rule != row.rule:
                problems.append(
                    f"{row.line!r} is refused under {refused.rule}, and its row names {row.rule}"
                )
        else:
            problems.append(f"{row.line!r} is read, and its row says that it breaks a limit")
    assert not problems, reported(problems)


def test_item_4_each_record_resolves_and_each_expression_answers_on_a_stage_of_the_repository():
    assert OBJECTS, "the table holds no object"
    stages, problems = {}, []
    for row in OBJECTS:
        try:
            held = resolve(row.record)
        except (ImportError, AttributeError) as error:
            problems.append(f"{row.name}: the record {row.record} does not resolve ({error})")
        else:
            if not inspect.isclass(held):
                problems.append(f"{row.name}: {row.record} is no class of the package")
        if row.file not in STAGES:
            problems.append(f"{row.name}: no stage of this test is built from {row.file}")
            continue
        lines = (ROOT / row.file).read_text(encoding="utf-8").splitlines()
        # a line of the file is compared without its annotation, which a
        # row leaves out
        if row.line not in [line.partition("::")[0].rstrip() for line in lines]:
            problems.append(f"{row.name}: {row.line!r} is no line of {row.file}")
        make = STAGES[row.file]
        if make not in stages:
            stages[make] = make()
        # the expression is text of the package's own table, in which
        # `stage` names the stage
        try:
            eval(row.read_by, {"stage": stages[make]})
        except Exception as error:  # every failure of the expression is a fault of its row
            problems.append(
                f"{row.name}: {row.read_by} raises {type(error).__name__} on the stage of "
                f"{row.file} ({error})"
            )
    assert not problems, reported(problems)


def test_item_5_the_printed_page_equals_the_tables():
    run = subprocess.run(
        [sys.executable, str(HOOKS / "reference_pages.py"), "--check", "--page", PAGE],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_item_6_each_form_of_a_set_is_read_in_the_type_of_the_objects_its_row_names():
    named = [row.name for row in OBJECTS]
    problems = [
        f"{name} of WITH_A_SET is the name of no one row of OBJECTS"
        for name in WITH_A_SET
        if named.count(name) != 1
    ]
    for row in SET_FORMS:
        beside = sorted(set(row.read_in) - set(WITH_A_SET))
        if beside:
            problems.append(
                f"{row.constructor}: {', '.join(beside)} is no object whose type holds a set"
            )
        name, colon, written = row.example.partition(" : ")
        if not colon or not name.isidentifier():
            problems.append(f"{row.constructor}: {row.example!r} is no declaration of one name")
            continue
        for kind in WITH_A_SET:
            read = is_read(smallest_record(kind, written))
            if read and kind not in row.read_in:
                problems.append(
                    f"{row.constructor}: `{written}` is read in the type of a {kind}, and the "
                    f"row does not name it"
                )
            if not read and kind in row.read_in:
                problems.append(
                    f"{row.constructor}: `{written}` is refused in the type of a {kind}, and "
                    f"the row names it"
                )
    assert not problems, reported(problems)
