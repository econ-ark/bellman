"""Age and branch incomes in the durables trellis."""

from pathlib import Path

import pytest

from bellman.trellis import assemble_trellis, connection_report


def evaluate(piece, **values):
    """Evaluate a primitive at its named arguments and bound parameters."""
    return piece.function(
        *(values[name] for name in piece.arguments), *piece.parameter_values
    )


def test_age_is_decremented_by_tenure_and_used_by_each_branch():
    declaration = Path(__file__).resolve().parents[1] / "declaration"
    model = assemble_trellis(declaration, "spec.yml")
    report = connection_report(model)
    assert report.counts["certified"] == len(report.routes) == 204
    stages = model["periods"][0]["stages"]
    tenure = stages["tenure"]
    zero = lambda *coordinates: 0.0
    stages["bequest"].check_inputs({"age": 71, "V[>]": zero})
    inputs = {"V_kp[>]": zero, "V_adj[>]": zero, "age_kp[>]": 71, "age_adj[>]": 60}
    forward = tenure.dcsn.builder.fwd.kernels(inputs=inputs).pieces[0]
    aggregation = next(
        p for p in tenure.dcsn.builder.bwd.kernels(inputs=inputs).pieces
        if p.kind == "Aggregation"
    )
    earnings = tenure.par["Y"].value
    retirement = tenure.par["y_R"].value
    asset_return = tenure.par["R"].value
    housing_return = tenure.par["R_H"].value
    depreciation = tenure.par["δ"].value
    assert earnings[61 - 20] > 0 and retirement[61 - 20] == 0
    assert earnings[62 - 20] == 0 and retirement[62 - 20] == 0.1
    state = {"a_d": 2.0, "h_d": 3.0, "z_d": 4.0, "d": "adjust"}
    keep, _, _, adjust, _ = evaluate(forward, **state, age_kp=71, age_adj=60)
    assert keep == pytest.approx(2 * asset_return + 0.1)
    assert adjust == pytest.approx(
        2 * asset_return + 3 * housing_return * (1 - depreciation) + 4 * earnings[60 - 20]
    )

    age = 71
    for current in range(70, 19, -1):
        value, age = evaluate(
            aggregation, **state, **{"V_kp≻": 5.0, "V_adj≻": 8.0, "age_kp≻": age}
        )
        assert value == 8.0
        assert age == current

    for stage_name, coordinates in (
        ("keeper_cons", {"w_d": 8, "h_d": 3, "z_d": 4, "c": 2}),
        ("adjuster_cons", {"m": 8, "h_choice": 3, "z_d": 4, "c": 2}),
    ):
        builder = stages[stage_name].dcsn.builder.bwd
        kept = next(
            p for p in builder.kernels(inputs={"age": 71, "V[>]": zero}).pieces
            if p.kind == "Aggregation"
        )
        _, age = evaluate(kept, **coordinates, **{"V≻": 5.0, "age": 71})
        assert age == 71
