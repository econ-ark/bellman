"""The table of rules and their code: the function, test and refusal that each
row names."""

import inspect
import os
import subprocess
import sys

from application_files import ROOT
from refusal_rules import every_rule, problem_lines, unchecked_rows

from bellman.refusals import ConstructionError
from bellman.semantic_rules import SEMANTIC_RULES, example_texts, resolve
from bellman.stage import elaborate_text

# the options with which pytest lists the tests of files and runs none
COLLECT = ("--collect-only", "-q", "-p", "no:cacheprovider")


def refusal_of(text):
    """The rule under which the package refuses one text of an example, or
    None where it reads the text. The stage text is elaborated, and the call
    that ends the text, where it has one, is evaluated with `stage` naming
    that stage and `methods` the methods file of the text."""
    try:
        stage = elaborate_text(text.stage, "t.bl")
        if text.call is not None:
            methods = None if text.methods is None else {"text": text.methods, "origin": "m.bl"}
            eval(text.call, {"stage": stage, "methods": methods})
    except ConstructionError as refused:
        return refused.rule
    return None


def test_every_function_that_a_row_names_resolves_to_a_function_a_method_or_a_property():
    """Every name that a row lists among the functions that implement or check
    its rule is imported and looked up as a function, a method or a
    property."""
    problems = []
    for row in SEMANTIC_RULES:
        for name in row.implements + row.checks:
            try:
                held = resolve(name)
            except (ImportError, AttributeError) as error:
                problems.append(f"{row.section}, {row.item!r}: {name} does not resolve ({error})")
                continue
            if not (inspect.isroutine(held) or isinstance(held, property)):
                problems.append(
                    f"{row.section}, {row.item!r}: {name} is a {type(held).__name__}, and a "
                    f"row names functions, methods and properties"
                )
    assert not problems, problem_lines(problems)


def test_every_test_that_a_row_names_is_one_that_pytest_collects():
    """Every test that a row names stands in a test file that exists, and
    pytest collects it, as a case or as a function with all its cases."""
    named = {row.test for row in SEMANTIC_RULES if row.test is not None}
    files = sorted({test.split("::", 1)[0] for test in named})
    absent = [file for file in files if not (ROOT / file).is_file()]
    assert not absent, f"the rows name test files that do not exist: {absent}"
    assert files, "no row of the table of rules names a test"
    # the tests pytest collects in the files the rows name, each by its
    # path from the repository's root, its function and its case
    root = ("--rootdir", str(ROOT), "-c", str(ROOT / "pytest.ini"))
    run = subprocess.run(
        [sys.executable, "-m", "pytest", *COLLECT, *root, *files],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")},
    )
    assert run.returncode == 0, f"pytest did not collect {files}\n{run.stdout}\n{run.stderr}"
    collected = {line.strip() for line in run.stdout.splitlines() if "::" in line}
    # a row names one collected case, or a function with every case of it
    problems = [
        f"{test} is no test that pytest collects"
        for test in sorted(named)
        if test not in collected and not any(held.startswith(test + "[") for held in collected)
    ]
    assert not problems, problem_lines(problems)


def test_every_refusal_that_a_row_names_is_a_rule_of_the_refusal_catalogue():
    """Every rule that a row names among its refusals is a rule of one of the
    three vocabularies of the refusal catalogue."""
    rules = every_rule()
    problems = [
        f"{row.section}, {row.item!r}: {rule!r} is no rule of the three vocabularies"
        for row in SEMANTIC_RULES
        for rule in row.refusals
        if rule not in rules
    ]
    assert not problems, problem_lines(problems)


def test_a_row_of_a_checked_rule_holds_none_of_the_fields_of_a_rule_not_yet_checked():
    """A row whose rule the package checks holds no `package_today`,
    `example`, `also_concerns`, `see_also` or `refused_under`."""
    problems = []
    for row in SEMANTIC_RULES:
        held = (row.package_today, row.example, row.also_concerns, row.see_also, row.refused_under)
        if row.checked and any(held):
            problems.append(
                f"{row.section}, {row.item!r}: a checked row holds none of `package_today`, "
                f"`example`, `also_concerns`, `see_also` and `refused_under`"
            )
    assert not problems, problem_lines(problems)


def test_the_refusal_that_a_rule_not_yet_checked_names_is_a_rule_of_the_refusal_catalogue():
    """The rule under which a row of a rule not yet checked says that its
    example is refused is a rule of one of the three vocabularies."""
    rules = every_rule()
    problems = [
        f"{where}: {row.refused_under!r} is no rule of the three vocabularies"
        for where, row in unchecked_rows()
        if row.refused_under is not None and row.refused_under not in rules
    ]
    assert not problems, problem_lines(problems)


def test_the_example_of_each_rule_not_yet_checked_is_read_or_refused_as_its_row_says():
    """Each row of a rule not yet checked states what the package does today
    and gives an example, and the package reads each text of the example, or
    refuses it under the rule that the row names."""
    # a row whose example no longer behaves as it says is out of date: where
    # the package now checks the rule, a row of SEMANTIC_RULES is given
    # checked=True with its functions, its refusals and a test, and a row of
    # UNCHECKED_ELSEWHERE is removed
    problems = []
    for where, row in unchecked_rows():
        if not row.package_today or not row.example:
            problems.append(f"{where}: a rule not yet checked holds `package_today` and `example`")
            continue
        for text in example_texts(row.example):
            refused = refusal_of(text)
            if refused == row.refused_under:
                continue
            if row.refused_under is None:
                problems.append(
                    f"{where}: the package no longer reads the example and refuses it under "
                    f"{refused}"
                )
            elif refused is None:
                problems.append(
                    f"{where}: the package now reads the example, which its row says is refused "
                    f"under {row.refused_under}"
                )
            else:
                problems.append(
                    f"{where}: the package refuses the example under {refused}, and its row "
                    f"names {row.refused_under}"
                )
    assert not problems, problem_lines(problems)
