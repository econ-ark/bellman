"""The skips of a test that needs what a copy of the repository may lack: a
package outside the list `dev` of the package's requirements, or a git
checkout; and the environment of a call of git in a test."""

import importlib
import os
import shutil

import pytest
from application_files import ROOT

# how to install each package that no extra of the package installs
INSTRUCTIONS = {
    "asva": 'install it with "pip install -e packages/asva"',
    "jax": 'install it with "pip install jax"',
    "@viz-js/viz": 'install Node, then run "npm ci" in the folder packages/bellman',
}


def require_package(name, extra=None, *, found=None):
    """The module `name`, imported, or None where `found` is given; where the
    package itself is absent, a skip of the test whose reason names the extra
    `extra` of the package, or the instruction of `INSTRUCTIONS`, that
    installs it."""
    # pytest reports the skip at the line that called this function
    __tracebackhide__ = True
    package = name.split(".")[0]
    how = f'install the extra "{extra}"' if extra is not None else INSTRUCTIONS[package]
    reason = f"the package {package} is not installed; {how}"
    # `found` says whether a package that Python does not import, such as the
    # Node package of the drawings, is installed; any other package is imported
    if found is not None:
        if not found:
            pytest.skip(reason)
        return None
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:
        # a module missing inside the package, or a dependency of the package
        # that is missing, is a fault of a package that is installed
        if error.name != package:
            raise
    # a module may call this function at its top, to skip all its tests
    pytest.skip(reason, allow_module_level=True)


def require_git_checkout():
    """A skip of the test where the repository is not a git checkout or the
    program git is not installed."""
    # pytest reports the skip at the line that called this function
    __tracebackhide__ = True
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip(
            "this test reads what git records of the repository, and the repository is not "
            "a git checkout or git is not installed; clone the repository with git to run it"
        )


def environment_without_git_variables():
    """The environment of this process without the variables whose names
    begin with `GIT_`, for a call of git in a test, so that git reads the
    repository that the call names."""
    # a run started from a git hook holds GIT_DIR, GIT_WORK_TREE and others of
    # these variables, and git reads the repository that they name in place of
    # the folder that the call names with -C or as its working folder
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
