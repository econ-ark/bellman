"""The two sets of the suite: a plain run skips each case marked complete_set,
a run with --complete runs every case, and a table keeps one row in the
default set."""

from pathlib import Path

import pytest
from two_sets import one_row_by_default

# pytester is the plugin of pytest that runs pytest on a project in a
# temporary folder. pytest leaves the plugin off unless a test module or a
# setting names it.
pytest_plugins = ["pytester"]


# the folder of this file, which holds two_sets.py
HERE = Path(__file__).resolve().parent


CONFTEST = """
from two_sets import pytest_addoption, pytest_collection_modifyitems, pytest_report_header
"""


SETTINGS = """
[pytest]
markers =
    complete_set: runs only with --complete
"""


CASES = """
import pytest


def test_in_the_default_set():
    pass


@pytest.mark.complete_set
def test_in_the_complete_set():
    pass
"""


def write_project(pytester):
    """The project of two cases, in the folder of `pytester`, with this
    file's folder on `sys.path` so that the project imports two_sets.py."""
    pytester.syspathinsert(HERE)
    pytester.makeconftest(CONFTEST)
    pytester.makefile(".ini", pytest=SETTINGS)
    pytester.makepyfile(CASES)


def write_project_of_two_folders(pytester):
    """The project of two folders, `one` and `two`, each with a conftest.py
    that imports the three hooks and with the two cases, as the root folder
    `tests/` and the folder of the package's tests are."""
    pytester.syspathinsert(HERE)
    pytester.makefile(".ini", pytest=SETTINGS + "testpaths = one two\n")
    for folder in ("one", "two"):
        pytester.mkdir(folder)
        (pytester.path / folder / "conftest.py").write_text(CONFTEST, encoding="utf-8")
        (pytester.path / folder / f"test_{folder}.py").write_text(CASES, encoding="utf-8")


@pytest.mark.parametrize(
    ("options", "outcomes", "lines"),
    [
        pytest.param(
            ("-v", "-rs"),
            {"passed": 1, "skipped": 1},
            [
                "the default set: cases marked complete_set are skipped; "
                "--complete runs every case",
                "*::test_in_the_default_set PASSED*",
                "*::test_in_the_complete_set SKIPPED*",
                # `[[]` and `[]]` match the brackets around the count of
                # skipped cases
                "SKIPPED [[]1[]] *: in the complete set alone; run pytest with --complete",
            ],
            id="a plain run",
        ),
        pytest.param(
            ("-v", "--complete"),
            {"passed": 2},
            [
                "the complete set: every case runs",
                "*::test_in_the_default_set PASSED*",
                "*::test_in_the_complete_set PASSED*",
            ],
            id="a run with --complete",
        ),
    ],
)
def test_a_run_skips_the_marked_case_with_its_reason_unless_it_has_the_option_complete(
    pytester, options, outcomes, lines
):
    """A run of the project of two cases skips the marked case with its
    reason, under the line that names the default set, unless the option
    `--complete` runs both cases under the line that names the complete set."""
    write_project(pytester)
    result = pytester.runpytest(*options)
    result.assert_outcomes(**outcomes)
    result.stdout.fnmatch_lines(lines)


def test_two_conftest_files_that_import_the_hooks_add_the_option_once(pytester):
    """Where two conftest.py files import the hooks, the help of pytest lists
    the option `--complete` once."""
    write_project_of_two_folders(pytester)
    result = pytester.runpytest("--help")
    assert result.ret == 0
    named = [line.split()[0] for line in result.stdout.lines if "--complete" in line]
    assert named == ["--complete"]


@pytest.mark.parametrize(
    ("options", "outcomes", "first_line", "skipped"),
    [
        pytest.param(
            ("-v", "-rs"),
            {"passed": 2, "skipped": 2},
            "the default set: cases marked complete_set are skipped; --complete runs every case",
            [
                "one/test_one.py::test_in_the_complete_set",
                "two/test_two.py::test_in_the_complete_set",
            ],
            id="a plain run",
        ),
        pytest.param(
            ("-v", "--complete"),
            {"passed": 4},
            "the complete set: every case runs",
            [],
            id="a run with --complete",
        ),
    ],
)
def test_with_two_conftest_files_a_run_writes_one_line_and_skips_marked_cases_unless_complete(
    pytester, options, outcomes, first_line, skipped
):
    """Where two conftest.py files import the hooks, a run writes the line
    that names its set once and skips the two marked cases, unless the
    option `--complete` runs every case."""
    write_project_of_two_folders(pytester)
    result = pytester.runpytest(*options)
    result.assert_outcomes(**outcomes)
    assert result.stdout.lines.count(first_line) == 1
    reported = [
        line for line in result.stdout.lines if line.endswith("SKIPPED") or " SKIPPED (" in line
    ]
    assert [line.split()[0] for line in reported] == skipped


def test_with_two_conftest_files_each_marked_case_carries_one_skip_mark(pytester):
    """Where two conftest.py files import the hooks, the collection of a plain
    run gives each marked case one skip mark and the other cases none."""
    write_project_of_two_folders(pytester)
    items, _ = pytester.inline_genitems()
    marks = {item.nodeid: len(list(item.iter_markers("skip"))) for item in items}
    assert marks == {
        "one/test_one.py::test_in_the_default_set": 0,
        "one/test_one.py::test_in_the_complete_set": 1,
        "two/test_two.py::test_in_the_default_set": 0,
        "two/test_two.py::test_in_the_complete_set": 1,
    }


def test_an_empty_table_gives_no_cases():
    """`one_row_by_default` gives no case for a table that has no row."""
    assert one_row_by_default([]) == []


def test_one_row_by_default_leaves_the_default_row_unmarked_and_refuses_one_the_table_lacks():
    """`one_row_by_default` leaves the row named as the default unmarked and
    marks the others, and it refuses a default that is no row of the table
    with a message that names it."""
    cases = one_row_by_default(("a", "b"), default="b")
    assert [[mark.name for mark in case.marks] for case in cases] == [["complete_set"], []]
    with pytest.raises(ValueError, match="'c'"):
        one_row_by_default(("a", "b"), default="c")
