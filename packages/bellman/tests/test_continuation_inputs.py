"""Supplied fields retain their declared names, domains and dependence."""

import numpy as np
import pytest

from bellman.factory.elaboration import elaborate_text
from bellman.refusals import ConstructionError
from bellman.stage.input_requirements import continuation_inputs, supplied_constants


def constant_stage(domain, declarations=""):
    return elaborate_text(
        f"""@stage: terminal
{declarations}
[id=cntn_to_dcsn, (L : {domain} @ !vlu @ !cnst) : !cntn
    -> (B : {domain} @ !vlu @ !cnst) : !dcsn] {{
    B = L
}}
""",
        "terminal.bl",
    )


@pytest.mark.parametrize(
    "domain,valid,invalid",
    [
        ("ℝ", np.float64(2), np.nan),
        ("ℝ̄", np.inf, np.nan),
        ("ℝ̄ × ℝ", (np.inf, 2), (np.nan, 2)),
        ("{low, high} → ℝ̄", {"low": 1, "high": np.inf}, {"low": 1, "high": np.nan}),
        ("ℝ × ℝ", np.array([1, 2]), np.array([1, 2, 3])),
        ("{low, high}", "low", "middle"),
        ("{low, high} → ℝ", {"low": 1, "high": 2}, {"low": 1}),
    ],
)
def test_constant_membership(domain, valid, invalid):
    stage = constant_stage(domain)
    values = {"L": valid}
    assert stage.check_inputs(values) == ()
    assert values["L"] is valid
    assert next(iter(supplied_constants(stage, values).values())) is valid
    with pytest.raises(ConstructionError) as refused:
        stage.check_inputs({"L": invalid})
    assert refused.value.rule == "continuation-input"
    assert refused.value.file == "terminal.bl"
    assert "L" in refused.value.message


@pytest.mark.parametrize("domain", ["ℝ → ℝ", "{low, high} → ℝ", "F"])
def test_fixed_callables_leave_membership_undecided(domain):
    stage = constant_stage(domain, "F := {low, high} → ℝ" if domain == "F" else "")

    def supplied(_point):
        pytest.fail("The checker must not evaluate a supplied function.")

    conditions = stage.check_inputs({"L": supplied})
    assert len(conditions) == 1
    assert conditions[0].status == "required"


@pytest.mark.parametrize("values", [{}, {"L[>]": -1}, {"L": -1, "V": 0}, [-1]])
def test_exact_input_mapping(values):
    stage = constant_stage("(-inf, 0]")
    with pytest.raises(ConstructionError, match="inputs"):
        stage.check_inputs(values)
    assert tuple(continuation_inputs(stage)) == ("L",)


def test_calibrated_domain_and_unchanged_obligations():
    stage = constant_stage("[0, n]", "n : ℝ₊₊")
    assert stage.check_inputs({"L": 3})[0].status == "required"
    stage.calibrate({"n": 2})
    before = tuple(str(item) for item in stage.obligations())
    assert stage.check_inputs({"L": 1}) == ()
    assert tuple(str(item) for item in stage.obligations()) == before
    with pytest.raises(ConstructionError, match="L"):
        stage.check_inputs({"L": 3})


@pytest.mark.parametrize("marked", [False, True])
def test_constant_domain_reads_another_supplied_constant(marked):
    text = """@stage: terminal
[id=cntn_to_dcsn, (L : ℝ₊₊ @ !vlu @ !cnst, C : [0, L] @ !vlu @ !cnst) : !cntn
    -> (B : ℝ @ !vlu @ !cnst) : !dcsn] {
    B = L + C
}
"""
    name = "L[>]" if marked else "L"
    stage = elaborate_text(text.replace("L", name), "terminal.bl")
    assert stage.check_inputs({name: 2, "C": 1}) == ()
    with pytest.raises(ConstructionError, match="C"):
        stage.check_inputs({name: 2, "C": 3})


def test_undefined_domain_is_a_located_refusal():
    stage = constant_stage("[0, 1/(n-1)]", "n : ℝ")
    stage.calibrate({"n": 1})
    with pytest.raises(ConstructionError, match="declared set") as refused:
        stage.check_inputs({"L": 0})
    assert refused.value.address == "inputs.L"


def test_interior_constant_is_not_supplied_again():
    stage = elaborate_text(
        """@stage: terminal
[id=seed, () : !dcsn -> (L : ℝ @ !vlu @ !cnst) : !cntn] {
    L = 2
}
[id=cntn_to_dcsn, (L) : !cntn -> (B : ℝ @ !vlu @ !cnst) : !dcsn] {
    B = L
}
""",
        "terminal.bl",
    )
    assert stage.check_inputs({}) == ()
    assert not continuation_inputs(stage)


def test_calibration_membership_keeps_its_existing_undecided_result():
    stage = elaborate_text("@stage: t\nx : ℝ_{-∞}", "calibration.bl")
    stage.calibrate({"x": float("nan")})
    conditions = tuple(stage.obligations())
    assert any(
        condition.condition == "calibration-domain-membership" and condition.status == "required"
        for condition in conditions
    )
