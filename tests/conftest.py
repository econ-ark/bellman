"""The configuration of the tests of the root folder: the import path, the
fixtures that both folders of tests share, a fixture that two files of this
folder share, and the hooks of the two sets."""

import functools
import sys
from pathlib import Path

import pytest

# The tests of this folder read fixtures and support modules of the package's
# tests: that folder stands first on the import path, the fixtures that both
# folders share are imported by name from shared_stage_fixtures.py, and the
# hooks of the two sets, the option --complete among them, from two_sets.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "bellman" / "tests"))

from application_files import ROOT  # noqa: E402
from shared_stage_fixtures import (  # noqa: E402
    bound_port_cons_trellis,
    buffer_stock,
    buffer_stock_application,
    cache_folder,
    catalogue_entries,
    cons,
    cons_argmax,
    cons_argmax_text,
    cons_methodized,
    cons_methodized_without_calibration,
    cons_obs,
    cons_savings_iid,
    cons_sources,
    cons_with_egm_lines,
    cons_with_egm_lines_text,
    derived_parameter_stages,
    example_additions,
    example_shocks,
    ez_savings,
    grid_stage_with_one_addition,
    model_explorer_package,
    perfect_foresight,
    perfect_foresight_explicit,
    port,
    retiree_death,
    sa_savings,
    tenure,
    two_nodes_registry,
    worker_cons,
)
from two_sets import (  # noqa: E402
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_report_header,
)

__all__ = [
    "bound_port_cons_trellis",
    "buffer_stock",
    "buffer_stock_application",
    "cache_folder",
    "catalogue_entries",
    "cons",
    "cons_argmax",
    "cons_argmax_text",
    "cons_methodized",
    "cons_methodized_without_calibration",
    "cons_obs",
    "cons_savings_iid",
    "cons_sources",
    "cons_with_egm_lines",
    "cons_with_egm_lines_text",
    "derived_parameter_stages",
    "example_additions",
    "example_shocks",
    "ez_savings",
    "grid_stage_with_one_addition",
    "model_explorer_package",
    "perfect_foresight",
    "perfect_foresight_explicit",
    "port",
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_report_header",
    "retiree_death",
    "sa_savings",
    "tenure",
    "two_nodes_registry",
    "worker_cons",
]


@pytest.fixture(scope="module")
def text_of():
    """The text of a file of the repository by its path from the root, each
    file read once."""
    return functools.cache(lambda path: (ROOT / path).read_text(encoding="utf-8"))
