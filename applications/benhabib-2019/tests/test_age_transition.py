"""Age and earnings along the specified life cycle."""

from pathlib import Path

import pytest

from bellman.trellis import assemble_trellis, connection_report


def evaluate(piece, **values):
    """Evaluate a primitive at its named arguments and bound parameters."""
    return piece.function(
        *(values[name] for name in piece.arguments), *piece.parameter_values
    )


def test_working_age_and_earnings():
    declaration = Path(__file__).resolve().parents[1] / "declaration"
    model = assemble_trellis(declaration, "spec.yml")
    assert connection_report(model).counts["certified"] == 36
    age, terminal_value = 61, lambda a: 0.0
    bequest = model["periods"][0]["stages"]["bequest"]
    bequest.check_inputs({"age": age, "V[>]": terminal_value})
    stage = model["periods"][1]["stages"]["benhabib_bellman"]
    supplied = {"age[>]": age, "V[>]": terminal_value}
    wage = stage.par["wage_fn"].value
    gross_return = stage.par["R_vec"].value[0]
    forward = stage.dcsn.builder.fwd.kernels(inputs=supplied).pieces[0]
    (transition,) = (
        piece for piece in stage.dcsn.builder.bwd.kernels(inputs=supplied).pieces
        if piece.kind == "Aggregation"
    )
    (inverse,) = (
        piece for piece in stage.dcsn.builder.policy.kernels(inputs=supplied).pieces
        if piece.key == ("inv_g_dcsn_to_cntn", "Aggregation")
    )
    visited = []
    for current in range(60, 24, -1):
        visited.append(age)
        saving = evaluate(forward, m=10.0, c=2.0, age=age)
        assert saving == pytest.approx(gross_return * 8 + wage[age - 25][0])
        assert evaluate(inverse, c=2.0, a=saving, **{"age≻": age}) == pytest.approx(10.0)
        _, age = evaluate(transition, m=10.0, c=2.0, **{"age≻": age, "V≻": 0.0})
        assert age == current
    assert visited == list(range(61, 25, -1))
