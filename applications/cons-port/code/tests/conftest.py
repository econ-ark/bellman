"""The fixtures of the portfolio-consumption acceptance: the fixed reference, read and never regenerated;
the five configurations of the reference, built from this application's trellis files and solved once per
session by the model's tool; and the two orders the notebooks present."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "applications" / "cons-port"
# the folder of the files the language reads: the trellis files, the calibration, the methods and the settings
DECLARATION = APP / "declaration"
# the folder of the stage folders, each holding a stage file written with the maximization alone and the
# methods file beside it, the addition that opens its policy builder (AAS, 21 and 28 October 2026)
STAGES = DECLARATION / "stages"
CONSUMPTION = STAGES / "cons" / "cons.bl"
sys.path.insert(0, str(APP / "code"))

from bellman.stage import elaborate_stage, load_stage  # noqa: E402
from bellman.trellis import (  # noqa: E402
    calibrate_trellis,
    configure_trellis,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    methodize_trellis,
)
import cons_port_tool as tool  # noqa: E402

REFERENCE = APP / "reference" / "legacy"
ARCHIVE_SHA256 = "1fa1264cfe37297c59a9cf209374d5a340157393fdc675f9552ac8b668ea0ecc"
EVIDENCE = APP / "code" / "tests" / "evidence"
# the sources of the earlier implementation, none of which the comparison may open (A09, first step)
LEGACY_SOURCES = tuple(str(path) for path in (APP / "code" / "capture_legacy_reference.py", APP / "code" / "ffp_utils.py",
                                              APP / "code" / "ffp_plots.py", APP / "reference" / "legacy" / "syntax",
                                              APP / "notebooks" / "port-cons"))
# each configuration of the reference: the name of its trellis file, declaration/trellis.<name>.yml, and the grid
# its terminal value stands on
CONFIGURATIONS = {"cons_only": ("reference-cons-only", "a"), "beginning_egm": ("reference-port-cons", "a"),
                  "beginning_vfi": ("reference-port-cons-vfi", "a"), "end_returns": ("reference-cons-port", "m"),
                  "port_only": ("reference-port-only", "k")}
# the grids the reference placed its terminal values on: savings and capital multi-exponential, resources linear
TERMINAL = {"a": tool.expmult_grid(100.0, 800), "k": tool.expmult_grid(1000.0, 800), "m": np.linspace(0.01, 2000.0, 8000)}
# the backward order of each period: the reference's, with the discount stage where the fields place it
BACKWARD = {"cons_only": ["disc", "cons", "noport"], "beginning_egm": ["disc", "cons", "port"],
            "beginning_vfi": ["disc", "cons", "port"], "end_returns": ["port", "disc", "cons"], "port_only": ["disc", "port"]}

OPENED = []
sys.addaudithook(lambda event, args: OPENED.append(os.fsdecode(args[0]))
                 if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)) else None)


def stage_file(key):
    """The stage file the trellis files and the recipes name for the stage `key`, in its folder under STAGES."""
    return STAGES / key / f"{key}.bl"


def consumption_stage():
    """A consumption stage of its own, elaborated from stage_file("cons") and calibrated, for a test that binds
    methods on it: a binding verb binds the stage it is called on (decision SB-10), so such a test binds no
    session fixture (as SB-25 rules for the package's tests)."""
    return elaborate_stage(load_stage(str(stage_file("cons")))).calibrate(str(DECLARATION / "calibration" / "portfolio.yml"))


def specified(name):
    """The specified trellis of the file `declaration/trellis.<name>.yml`: read, elaborated and bound by the three
    verbs. A name that begins with `spec.` is a recipe of
    the folder, read with `load_recipe`."""
    syntactic = (load_recipe(DECLARATION, name) if name.startswith("spec.")
                 else load_trellis(str(DECLARATION / f"trellis.{name}.yml")))
    return configure_trellis(calibrate_trellis(methodize_trellis(
        elaborate_trellis(syntactic), syntactic), syntactic), syntactic)


@pytest.fixture(scope="session")
def manifest():
    return json.loads((REFERENCE / "port_cons_h5.manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def archive():
    with np.load(REFERENCE / "port_cons_h5.npz", allow_pickle=False) as held:
        return {key: held[key] for key in held.files}


@pytest.fixture(scope="session")
def ending():
    """The consumption stage, calibrated and with its methods file stages/cons/methods.bl read into it, whose
    aggregation gives the terminal value: the stage file writes no marginal value, and the envelope line of the
    methods file states the marginal value beside the value (decision SD-33)."""
    return elaborate_stage(load_stage(str(stage_file("cons")))).calibrate(
        str(DECLARATION / "calibration" / "portfolio.yml")).methodize(str(STAGES / "cons" / "methods.bl"))


@pytest.fixture(scope="session")
def reference_runs(ending):
    """(model, solutions) for each configuration of the reference, and the files opened while they were built and solved."""
    start = len(OPENED)
    runs = {}
    for name, (file, grid) in CONFIGURATIONS.items():
        model = specified(file)
        runs[name] = (model, tool.solve_trellis(model, {"V[>]": tool.terminal_value(ending, TERMINAL[grid])}))
    return runs, OPENED[start:]


@pytest.fixture(scope="session")
def orders():
    """The two orders the notebooks present, specified."""
    return {name: specified(f"spec.{name}.yml") for name in ("port-cons", "cons-port")}


@pytest.fixture(scope="session")
def corrected_vfi(ending):
    """Six periods on the fifth configuration's grids, with ordinary portfolio handlers."""
    model = specified("reference-port-cons-vfi")
    path = STAGES / "port" / "methods.reference.bl"
    text = path.read_text(encoding="utf-8")
    text = text.replace('"cons-port:share_search_reference"', '"cons-port:share_search"')
    text = text.replace('"cons-port:gauss_hermite_reference"', '"cons-port:gauss_hermite"')
    for period in model["periods"]:
        period["stages"]["port"].methodize({"text": text, "origin": str(path) + " (ordinary handlers)"})
    terminal = tool.terminal_value(ending, TERMINAL["a"])
    return model, tool.solve_trellis(model, {"V[>]": terminal}), terminal
