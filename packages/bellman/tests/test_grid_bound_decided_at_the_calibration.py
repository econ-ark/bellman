"""The acceptance file of the change "A grid bound over a set whose endpoint
is a parameter is decided at the calibration" (CDC, 11 November 2026), which
answers the issue of that name: one test for each acceptance item, named
`test_item_<n>_<claim>`, each reading the binding verbs and the realized
grids of a builder's `kernels()`.

1. On the buffer-stock application with the set of savings `Xa := [a_Art,
   inf)`, a grid bound inside the set at the calibration that is bound
   configures, and the grid is constructed.
2. A bound outside the set at the calibration is refused: by the setting's
   own check where the setting is declared on the set, and under
   `grid-bounds` where it is declared on a wider one, in a sentence that
   names the parameter value read. One value receives one answer from both
   checks.
3. Before a calibration is bound nothing decides the membership, and the
   bound is refused as before; a set that reads no parameter is decided
   without a calibration, as before.
4. Each binding judges the bounds at the calibration bound at that moment:
   after a calibration that moves the endpoint, the next `configure` and the
   next `methodize` refuse a bound it has passed.
5. A point of `!Points` is judged in the same way: outside the set at the
   calibration it is refused, inside it the grid is constructed, and before
   a calibration it is admitted and its construction reports the open
   membership, as before.
"""

import pytest
from conftest import (
    BUFFER_STOCK_METHODS,
    BUFFER_STOCK_SETTINGS,
    DERIVED_BUFFER_STOCK_CALIBRATION,
    GRID_STAGE,
    GRID_VALUES,
    ROOT,
    derived_buffer_stock_text,
    stage_from_text,
)

from bellman.refusals import ConstructionError
from bellman.stage.sources import load_settings

SETTINGS = load_settings(ROOT / BUFFER_STOCK_SETTINGS)
METHODS = (ROOT / BUFFER_STOCK_METHODS).read_text(encoding="utf-8")
# the setting of the lower bound of the savings grid, declared on a wider
# set than the coordinate's, so that the grid's check alone judges the bound
ON_THE_SET = "a_min : Xa "
ON_THE_REALS = "a_min : ℝ  "


def _buffer_stock(methods=METHODS, limit=True):
    """The buffer-stock stage with its methods file read into it; with
    `limit`, the set of savings is `[a_Art, inf)` for an artificial borrowing
    limit `a_Art : (-inf, 0]` that the stage file declares."""
    text = derived_buffer_stock_text()
    if limit:
        plain = "Xa := ℝ₊₊"
        probability = 'p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]\n'
        assert text.count(plain) == 1 and text.count(probability) == 1
        text = text.replace(plain, "Xa := [a_Art, inf)")
        text = text.replace(probability, probability + "a_Art : (-inf, 0]\n")
    stage = stage_from_text(text, "buffer_stock.bl")
    return stage.methodize({"text": methods, "origin": "methods.bl"})


def _calibration(limit):
    return {"calibration": {**DERIVED_BUFFER_STOCK_CALIBRATION, "a_Art": limit}}


def test_item_1_a_grid_bound_inside_the_set_at_the_calibration_configures():
    # the recorded settings, whose lower bounds are 0.001, at a limit of zero
    stage = _buffer_stock().calibrate(_calibration(0.0)).configure({"settings": SETTINGS})
    grid = stage.builder["dcsn", "arvl"].kernels().grids["dcsn_to_arvl.evaluate"]
    assert (grid.word, grid.coordinates, len(grid.points)) == ("Cartesian", ("k",), 960)
    assert (float(grid.points[0][0]), float(grid.points[-1][0])) == (0.001, 20.0)
    # a negative limit with the two grids' lower bounds between it and zero
    below = {**SETTINGS, "a_min": -0.4, "k_min": -0.4}
    stage = _buffer_stock().calibrate(_calibration(-0.5)).configure({"settings": below})
    grid = stage.builder["dcsn", "arvl"].kernels().grids["dcsn_to_arvl.evaluate"]
    assert float(grid.points[0][0]) == -0.4 and len(grid.points) == 960


def test_item_2_a_bound_outside_the_set_at_the_calibration_is_refused_by_both_checks():
    outside = {**SETTINGS, "a_min": -1.0}
    # the setting is declared on the set of savings: its own check refuses
    with pytest.raises(ConstructionError) as refused:
        _buffer_stock().calibrate(_calibration(0.0)).configure({"settings": outside})
    assert refused.value.rule == "setting-outside-set"
    assert "the value -1.0 lies outside the declared set [a_Art, inf)" in refused.value.message
    # the setting is declared on the reals: the grid's check refuses the
    # same value, and names the parameter value it read
    assert METHODS.count(ON_THE_SET) == 1
    wide = METHODS.replace(ON_THE_SET, ON_THE_REALS)
    with pytest.raises(ConstructionError) as refused:
        _buffer_stock(wide).calibrate(_calibration(0.0)).configure({"settings": outside})
    assert (refused.value.rule, refused.value.address) == ("grid-bounds", "policy")
    assert (
        "the factor a=(a_min, a_max, n_a) writes the point -1.0, which lies outside the "
        "declared set Xa of a at a_Art = 0.0"
    ) in refused.value.message
    # at a limit below the bound both checks admit it
    for methods in (METHODS, wide):
        inside = {**outside, "k_min": -1.0}
        _buffer_stock(methods).calibrate(_calibration(-2.0)).configure({"settings": inside})


def test_item_3_before_a_calibration_is_bound_the_membership_is_not_decided():
    with pytest.raises(ConstructionError) as refused:
        _buffer_stock().configure({"settings": SETTINGS})
    assert refused.value.rule == "grid-bounds"
    assert (
        "writes the point 0.001, which is not decidably inside the declared set Xa of k;"
    ) in refused.value.message
    # the application as it stands declares `Xa := ℝ₊₊`, which the set
    # algebra decides: it configures before its calibration and after it
    stage = _buffer_stock(limit=False).configure({"settings": SETTINGS})
    stage.calibrate({"calibration": DERIVED_BUFFER_STOCK_CALIBRATION})
    grid = stage.builder["dcsn", "arvl"].kernels().grids["dcsn_to_arvl.evaluate"]
    assert len(grid.points) == 960
    # a set of which a bound has no value at the calibration, `[1/k_lo, inf)`
    # at k_lo = 0, decides no membership either, and the bound is refused
    stage = stage_from_text(
        "@stage: t\nXk := [1/k_lo, inf)\nk_lo : ℝ\n"
        "[id=arvl_to_dcsn, (k : Xk) : !arvl -> (m : ℝ) : !dcsn] { m = k }\n"
        "[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }\n"
    )
    stage.calibrate({"k_lo": 0.0}).methodize(
        {
            "text": "@methods: t\nn_k : ℕ\nk_min : ℝ\nk_max : ℝ\n"
            "dcsn_to_arvl.evaluate.method : !Linear\n"
            "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n",
            "origin": "methods.bl",
        }
    )
    with pytest.raises(ConstructionError) as refused:
        stage.configure({"n_k": 5, "k_min": 1.0, "k_max": 2.0})
    assert refused.value.rule == "grid-bounds"
    assert "which is not decidably inside the declared set Xk of k" in refused.value.message


def test_item_4_each_binding_judges_the_bounds_at_the_calibration_bound_then():
    wide = METHODS.replace(ON_THE_SET, ON_THE_REALS)
    settings = {"settings": {**SETTINGS, "a_min": -1.0, "k_min": -0.4}}
    stage = _buffer_stock(wide).calibrate(_calibration(-2.0)).configure(settings)
    # the limit moves above the savings grid's lower bound and stays below
    # the asset grid's
    stage.calibrate(_calibration(-0.5))
    for bind in (
        lambda: stage.configure(settings),
        lambda: stage.methodize({"text": wide, "origin": "methods.bl"}),
    ):
        with pytest.raises(ConstructionError) as refused:
            bind()
        assert refused.value.rule == "grid-bounds"
        assert "lies outside the declared set Xa of a at a_Art = -0.5" in refused.value.message
    # and back below it
    stage.calibrate(_calibration(-2.0))
    stage.configure(settings)


def test_item_5_a_point_of_points_is_judged_at_the_calibration(grid_stage):
    plain = "Xm := ℝ₊\n"
    assert GRID_STAGE.count(plain) == 1
    text = GRID_STAGE.replace(plain, "m_Low : ℝ₊\nXm := [m_Low, inf)\n")
    values = {**GRID_VALUES, "P": [0.5, 1.0, 2.0]}

    def listed():
        entries = "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : !Points(nodes=P)\n"
        return grid_stage(entries, "P : ℝ × ℝ × ℝ\n", text=text)

    def grids(stage):
        return stage.builder["cntn", "dcsn"].kernels().grids

    with pytest.raises(ConstructionError) as refused:
        listed().calibrate({"m_Low": 0.75}).configure(values)
    assert refused.value.rule == "grid-bounds"
    assert (
        "whose coordinate m = 0.5 lies outside the declared set Xm at m_Low = 0.75"
    ) in refused.value.message
    inside = listed().calibrate({"m_Low": 0.25}).configure(values)
    assert [float(point[0]) for point in grids(inside)["cntn_to_dcsn"].points] == [0.5, 1.0, 2.0]
    # before a calibration the points are admitted, and the construction
    # reports the membership it cannot establish
    open_ = listed().configure(values)
    report = grids(open_)["cntn_to_dcsn"]
    assert "its node m = 0.5 is not decidably inside the declared set Xm" in report.reason
