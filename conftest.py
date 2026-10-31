"""The root of the tests: `pytest` run from the repository's root collects
and runs every folder that the `testpaths` of pytest.ini name.

Three of those folders hold a `conftest.py` and are not packages: `tests/`,
`packages/bellman/tests/` and `packages/bellman-workbench/tests/`. pytest
imports each of them under the one module name `conftest`, so once it has
read all three, `conftest` names the last it read, and a test of another
folder that writes `from conftest import ROOT`, when its module is imported
or inside the test itself, reads the wrong one. Before pytest imports a test
module, and again before it sets up and runs each test, the hooks below give
the name `conftest` to the `conftest.py` nearest above the test's file, the
one its own folder's tests import. A `conftest.py` of a package, such as that
of `applications/cons-port/code/tests/`, is imported under its package's name
and is left as it is.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
# each folder's conftest.py by its path, as pytest loaded it
_LOADED = {}


def _own_conftest(path, config):
    """The module of the `conftest.py` nearest above `path`, or None where
    there is none below the root or its folder is a package."""
    for folder in Path(path).resolve().parents:
        if folder == HERE:
            return None
        nearest = folder / "conftest.py"
        if not nearest.is_file():
            continue
        if (folder / "__init__.py").is_file():
            return None
        if nearest not in _LOADED:
            for plugin in config.pluginmanager.get_plugins():
                if getattr(plugin, "__file__", None) and Path(plugin.__file__).resolve() == nearest:
                    _LOADED[nearest] = plugin
        return _LOADED.get(nearest)
    return None


def _name_own_conftest(path, config):
    """Give `sys.modules["conftest"]` the `conftest.py` of the folder of
    `path`, where it has one."""
    module = _own_conftest(path, config)
    if module is not None:
        sys.modules["conftest"] = module


def pytest_collectstart(collector):
    """Before pytest imports a test module."""
    if isinstance(collector, pytest.Module):
        _name_own_conftest(collector.path, collector.config)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Before pytest sets up a test's fixtures."""
    _name_own_conftest(item.path, item.config)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    """Before pytest runs a test."""
    _name_own_conftest(item.path, item.config)
