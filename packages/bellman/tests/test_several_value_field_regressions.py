"""Value definitions, derivative terms, and connections between stages."""

import pytest
from application_files import ROOT
from printed_text import card_section_lines
from stage_builders import stage_from_text

from bellman.refusals import ConstructionError
from bellman.trellis import (
    calibrate_trellis,
    connection_report,
    derivative_missing,
    elaborate_trellis,
)

IDENTITY_ARRIVAL = """\
@stage: supplier
y : ℝ
y ~ N(0, 1)
[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] {
    m = k
}
[id=dcsn_to_cntn, (m) : !dcsn -> (a : ℝ) : !cntn] {
    a = m
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>] + m
    D_{m}V = 1
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V) :: [id=expectation]
}
"""


def test_aggregation_uses_the_value_line_after_a_derivative():
    text = """\
@stage: derivative_order
β : (0, 1)
[id=dcsn_to_cntn, (k : ℝ) : !dcsn -> (a : ℝ) : !cntn] {
    a = k
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    D_{k}V = 2
    V = 2*k + β*V[>]
}
"""
    stage = stage_from_text(text, "derivative_order.bl").calibrate({"calibration": {"β": 0.5}})
    (piece,) = (
        piece
        for piece in stage.builder["cntn", "dcsn"].kernels().pieces
        if piece.kind == "Aggregation"
    )
    values = {"V≻": 4, "k": 3}
    assert (
        piece.function(*(values[name] for name in piece.arguments), *piece.parameter_values) == 8
    )


def test_derivative_passes_through_an_expectation_under_the_identity_law():
    reader = stage_from_text(
        """\
@stage: reader
[id=dcsn_to_cntn, (m : ℝ, c : ℝ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
    a = m + c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>] + c
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = D_{a}V[>]
}
""",
        "reader.bl",
    )
    for motion in ("m = k", "m = k + y"):
        supplier = stage_from_text(IDENTITY_ARRIVAL.replace("m = k", motion), "supplier.bl")
        trellis = elaborate_trellis(
            {
                "periods": [
                    {"stages": {"supplier": supplier}, "connectors": []},
                    {"stages": {"reader": reader}, "connectors": []},
                ],
                "inter_connectors": [{"a": "k"}],
            }
        )
        (route,) = connection_report(trellis).routes
        assert route.status == "certified"
        missing = derivative_missing(trellis)
        if motion == "m = k":
            assert missing == ()
        else:
            (diagnostic,) = missing
            assert diagnostic.rule == "derivative-missing"
            assert diagnostic.address == "periods[0].stages['supplier']"


def test_connection_compares_function_endpoints_at_each_periods_calibration():
    text = """\
@stage: bounded
b : ℝ
𝑓(x : ℝ) := x + b
[id=dcsn_to_cntn, (k : [𝑓(0), inf)) : !dcsn -> (a : [𝑓(0), inf)) : !cntn] {
    a = k
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}
"""
    for (arrival, continuation), expected in [((1, 0), "incompatible"), ((0, 1), "compatible")]:
        recipe = {
            "periods": [
                {
                    "stages": {
                        "bounded": {
                            "stage": {"text": text, "origin": "bounded.bl"},
                            "calibration": {"b": bound},
                            "settings": {},
                            "methods": {},
                        }
                    },
                    "connectors": [],
                }
                for bound in (arrival, continuation)
            ],
            "inter_connectors": [{"a": "k"}],
        }
        trellis = calibrate_trellis(elaborate_trellis(recipe), recipe)
        (pair,) = connection_report(trellis).pairs
        assert pair.compatibility == expected
        assert f"[{continuation}, inf) against [{arrival}, inf)" in pair.reason
        assert [entry[:2] for entry in pair.basis] == [(1, "bounded"), (0, "bounded")]
        assert pair.basis[0][2] != pair.basis[1][2]


def test_rendahl_multiplier_prints_a_derivative_term():
    path = ROOT / "packages/bellman/tests/copied_files/rendahl-2015/growth.bl"
    growth = stage_from_text(path.read_text(encoding="utf-8"), str(path))
    aggregation = growth.builder["cntn", "dcsn"].primitives["multiplier:Aggregation"]
    rule = "\n".join(card_section_lines(str(aggregation.denote()), "Rule"))
    assert "D_{k_c}𝑉≻(" in rule
    assert "sup_{" not in rule


def test_self_expectation_requires_distinct_perch_marks():
    marked = IDENTITY_ARRIVAL.replace("V", "L")
    with pytest.raises(ConstructionError) as caught:
        stage_from_text(marked.replace("L[<]", "L"), "arrival.bl")
    assert caught.value.rule == "definition-order"
    assert caught.value.address == "dcsn_to_arvl.expectation"
    assert "reads the bare name L" in caught.value.message

    stage = stage_from_text(marked, "arrival.bl")
    card = str(stage.builder["dcsn", "arvl"].denote())
    assert "𝐿≺" in card
    assert "E_{y}[" in card
