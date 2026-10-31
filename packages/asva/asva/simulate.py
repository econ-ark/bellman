"""Generic forward Monte Carlo simulator for DDSL models.

The simulator carries a population of agents forward through
the stages of a model, applying transition callables and
evaluating solved policies at each stage.  Model-specific
parts are injected as callables; the loop is model-agnostic.

Mathematical object: the **pushforward measure operator**,
conjugate to the backward Bellman operator.

Shocks are **pre-drawn** before the simulation loop for
reproducibility and JIT compatibility.  Each model provides
a ``draw_shocks`` function that returns a ``draws`` dict
(keyed by ``(t, point)``) of ``(N,)`` arrays.  The walker
indexes into this dict instead of consuming an rng inline.

Shock injection points (per-transition, not per-stage):

    ====================== =================== ===========================
    Point                  When                Backward conjugate
    ====================== =================== ===========================
    shock_arvl             before agent acts   E in dcsn_to_arvl_builder
    shock_cntn             after agent acts    E inside cntn_to_dcsn_builder
    inter-period connector between periods     inter-period expectation
    ====================== =================== ===========================

The walk over the stages of a period and over the periods,
:func:`simulate_period` and :func:`simulate`, raises at the call:
it read the graph of one period and a fixed horizon, and a
trellis is walked from its forward record, which the package
``bellman`` does not yet provide.  The one-stage step
:func:`forward_stage`, the rename :func:`apply_rename` and the
shock draws :func:`draw_shocks` are complete.
"""

from __future__ import annotations

from collections import namedtuple

import numpy as np

# The message of the walk that waits for the trellis's forward record.
_WAITS_FOR_THE_TRELLIS = (
    "The simulator waits for the forward record of a trellis: for each "
    "period, the forward kernels of its stages as plain records, and the "
    "connectors within and between the periods. The package bellman does not "
    "yet provide that record, so the simulator cannot run in this release; "
    "the period graph and the fixed horizon it walked are retired."
)


# ── Types ──────────────────────────────────────────────────

StageForward = namedtuple("StageForward", [
    "arvl_to_dcsn",       # (particles, shocks) → particles
    "policy",             # (particles) → controls
    "dcsn_to_cntn",       # (particles, controls, shocks) → particles
    "shock_draw_arvl",    # str key into draws dict | None
    "shock_draw_cntn",    # str key into draws dict | None
])

BranchingForward = namedtuple("BranchingForward", [
    "arvl_to_dcsn",       # (particles, shocks) → particles
    "branch_policy",      # (particles) → labels array
    "dcsn_to_cntn",       # dict[label → callable(particles, shocks) → particles]
    "shock_draw_arvl",    # str key into draws dict | None
    "shock_draw_cntn",    # str key into draws dict | None
])


# ── Rename (connectors within and between periods) ─────────

def apply_rename(rename: dict, particles: dict) -> dict:
    """Apply the rename map of a connector, within a period or
    between periods (an inter-period connector)."""
    if not rename:
        return particles
    return {rename.get(k, k): v for k, v in particles.items()}


# ── Single-stage forward step ─────────────────────────────

def forward_stage(sfwd: StageForward, particles: dict,
                  draws_t: dict) -> tuple[dict, dict]:
    """Walk one standard stage: arvl → dcsn → cntn.

    Parameters
    ----------
    sfwd : StageForward
    particles : dict[str, ndarray]
    draws_t : dict
        Pre-drawn shocks for this period, keyed by the
        shock point names declared in the StageForward.

    Returns (poststates, records).
    """
    shocks_a = draws_t.get(sfwd.shock_draw_arvl, {}) if sfwd.shock_draw_arvl else {}
    states = sfwd.arvl_to_dcsn(particles, shocks_a)
    controls = sfwd.policy(states)
    shocks_c = draws_t.get(sfwd.shock_draw_cntn, {}) if sfwd.shock_draw_cntn else {}
    poststates = sfwd.dcsn_to_cntn(states, controls, shocks_c)
    return poststates, {"states": states, "controls": controls,
                        "poststates": poststates}


# ── Period walk, waiting for the trellis's forward record ──

def simulate_period(*args, **kwargs):
    """Walk one period forward through its stages.

    Raises ``NotImplementedError`` at the call: the walk read the
    stages' kinds, successors, renames and branch labels from one
    period's graph, which the trellis's forward record replaces.
    """
    raise NotImplementedError(_WAITS_FOR_THE_TRELLIS)


# ── Shock pre-drawing ─────────────────────────────────────

def draw_shocks(N: int, t0: int, T_end: int,
                shock_spec: dict, rng_seed: int = 42) -> dict:
    """Pre-draw all Monte Carlo shocks before the simulation.

    Parameters
    ----------
    N : int
        Number of agents.
    t0, T_end : int
        Period range (inclusive).
    shock_spec : dict
        Declares which shocks to draw and how.  Keyed by
        shock point name (the same string used in
        ``StageForward.shock_draw_arvl`` etc.).  Each value
        is a callable ``(N, rng) → ndarray(N,)`` or dict
        of arrays.
    rng_seed : int

    Returns
    -------
    draws : dict[int, dict]
        ``draws[t][point_name]`` = pre-drawn shock array
        for period *t* and shock point *point_name*.
    """
    rng = np.random.default_rng(rng_seed)
    draws = {}
    for t in range(t0, T_end + 1):
        draws[t] = {}
        for name, draw_fn in shock_spec.items():
            draws[t][name] = draw_fn(N, rng)
    return draws


# ── Top-level simulate, waiting for the trellis's forward record ──

def simulate(*args, **kwargs):
    """Simulate a population forward over the periods of a trellis.

    Raises ``NotImplementedError`` at the call: the simulation
    walked one period graph over a fixed horizon, applying one
    inter-period connector between consecutive periods, whereas a
    trellis holds its own periods and one inter-period connector
    for each adjacent pair, read from its forward record, which
    the package ``bellman`` does not yet provide.
    """
    raise NotImplementedError(_WAITS_FOR_THE_TRELLIS)
