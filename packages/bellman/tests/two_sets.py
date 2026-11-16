"""The two sets of cases. A plain run of pytest runs the default set and skips
each case marked complete_set; a run with --complete runs every case.
`one_row_by_default` puts one row of a table in the default set."""

import pytest
from application_files import CORPUS, ROOT


def one_row_by_default(rows, default=None):
    """The rows of a table as the cases of `pytest.mark.parametrize`: one row
    without a mark, in the default set, and every other row with the mark
    `complete_set`.

    The row without a mark is `default` when it is given. Otherwise it is
    the consumption stage, when the table holds it as the stage name `cons`,
    as the path of its stage file in the repository or as the absolute path
    of that file. Otherwise it is the first row.

    An empty table gives no cases. A `default` that is not a row of the
    table raises `ValueError`.

    Each case is `pytest.param(row)` with no id of its own, so that the test
    id of a row is the id that the `ids` argument of `parametrize`, or pytest
    itself, makes of the row."""
    rows = list(rows)
    if not rows:
        return []
    if default is None:
        consumption = ("cons", CORPUS["cons"], ROOT / CORPUS["cons"])
        default = next((row for row in rows if row in consumption), rows[0])
    elif default not in rows:
        raise ValueError(f"the default row {default!r} is not a row of the table")
    return [
        pytest.param(row, marks=() if row == default else pytest.mark.complete_set) for row in rows
    ]


# the mark of a case that runs only with --complete
COMPLETE_SET_MARK = "complete_set"


# the reason that pytest gives for each case of the complete set it skips
SKIP_REASON = "in the complete set alone; run pytest with --complete"


# The three hooks below act once in a run, however many conftest.py files
# import them: pytest calls a hook once for each conftest.py that holds it, and
# the root folder `tests/` and the folder of the package's tests each have one.
# The option stands in a group of its own, where the hook finds it; the run
# records in its stash, by these two keys, that the skips are given and that
# the line at the start of the run is written.
OPTION_GROUP = "two sets"


SKIPS_GIVEN = pytest.StashKey[bool]()


HEADER_WRITTEN = pytest.StashKey[bool]()


def pytest_addoption(parser):
    """The option --complete, added by the first conftest.py of the run that
    imports this hook."""
    group = parser.getgroup(OPTION_GROUP, "the default set and the complete set of cases")
    if any("--complete" in option.names() for option in group.options):
        return
    group.addoption(
        "--complete",
        action="store_true",
        default=False,
        help=f"run every case: the default set and the cases marked {COMPLETE_SET_MARK}",
    )


def pytest_collection_modifyitems(config, items):
    """A skip with the reason for each case marked complete_set, given once in
    the run, unless the run has the option --complete."""
    if config.getoption("--complete") or config.stash.get(SKIPS_GIVEN, False):
        return
    config.stash[SKIPS_GIVEN] = True
    skip = pytest.mark.skip(reason=SKIP_REASON)
    for item in items:
        if item.get_closest_marker(COMPLETE_SET_MARK) is not None:
            item.add_marker(skip)


def pytest_report_header(config):
    """The line at the start of a run that says which set runs, written once
    in the run."""
    if config.stash.get(HEADER_WRITTEN, False):
        return None
    config.stash[HEADER_WRITTEN] = True
    if config.getoption("--complete"):
        return "the complete set: every case runs"
    return (
        f"the default set: cases marked {COMPLETE_SET_MARK} are skipped; --complete runs "
        "every case"
    )
