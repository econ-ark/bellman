"""The life-cycle shock laws retain their formal and supplied ages."""

from pathlib import Path

import pytest

from bellman.trellis import assemble_trellis

_RECIPE = Path(__file__).resolve().parents[3] / "applications" / "life-cycle" / "declaration"


@pytest.mark.parametrize(
    ("stage_name", "edge", "binding", "carrier", "application"),
    (
        (
            "draw", ("arvl", "dcsn"),
            "(_age, z_2) ↦ MarkovChain(Π[_age], Z, z_2)",
            "Ages × Z → probability measure on Z", "P_{z|z_2}(𝑎𝑔𝑒≻(), z_2)",
        ),
        (
            "mortality", ("dcsn", "cntn"),
            "_age ↦ Categorical(ψ[_age], 1 − ψ[_age])",
            "Ages → probability measure on {survive, die}", "P_s(𝑎𝑔𝑒≻())",
        ),
    ),
)
def test_probability_law_binds_formal_age_and_reads_supplied_age(
    stage_name, edge, binding, carrier, application,
):
    stages = assemble_trellis(_RECIPE, "spec.yml")["periods"][1]["stages"]
    stage = stages[stage_name]
    (definition,) = (d for d in stage.definitions.values() if d.kind == "distribution")
    law = stage.definitions.denote(definition.identity)
    assert binding in str(law)
    assert str(law.denoted[0].mathematical_type) == carrier
    (subject,) = definition.identity.subjects
    builder = stage.builder[edge]
    extension = builder.primitives[f"DistributionExtension:{subject}"]
    for piece in (builder, extension):
        assert application in " ".join(str(piece.denote()).split())
