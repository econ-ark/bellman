"""A partial law retains the supplied data needed for later evaluation."""

import numpy as np
import pytest

from bellman.distributions.families import numeric_value, specialize_distribution
from bellman.fold.conditions import numerical_law
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text
from bellman.syntax.source import to_source

STAGE = """\
@stage: law_cases
Γ_c(x : ℝ) := [0, x]

[id=arvl_to_dcsn, (k : ℝ, z, y, tab) : !arvl -> (m : ℝ) : !dcsn] {
    m = k + y(tab)
}
[id=dcsn_to_cntn, (m, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (W[>] : ℝ @ !vlu, tab : F @ !vlu @ !cnst, c) : !cntn
    -> (W : ℝ @ !vlu) : !dcsn] {
    W = c + W[>]/2
}
[id=dcsn_to_arvl, (W) : !dcsn -> (W[<] : ℝ @ !vlu) : !arvl] {
    W[<] = E_{z,y}(W)
}
[id=policy, (W[>]) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(cp + W[>]/2)
}
"""


def detached(declarations, supplied, *, calibration=None):
    text = STAGE.replace("@stage: law_cases", "@stage: law_cases\n" + declarations)
    stage = elaborate_text(text, "law_cases.bl")
    if calibration is not None:
        stage.calibrate({"calibration": calibration})
    inputs = {"W[>]": lambda a: a, "tab": supplied}
    stage.check_inputs(inputs)
    law = numerical_law(
        stage, builder="dcsn_to_arvl", integrated=("y",), given=("z",), inputs=inputs
    )
    return law.declarations[0]


@pytest.mark.parametrize(
    "domain,draw,values,key",
    [
        ("{low, high}", "Categorical((0.5, 0.5))", {"low": 2.0, "high": 7.0}, "high"),
        ("{low, high}", "Categorical((0.5, 0.5))", np.array([2.0, 7.0]), "high"),
        ("{1, 3}", "Bernoulli(0.5)", {1: 2.0, 3: 7.0}, 3),
        ("{1, 3}", "Bernoulli(0.5)", np.array([2.0, 7.0]), 3),
    ],
    ids=("label-mapping", "label-array", "integer-mapping", "integer-array"),
)
def test_detached_law_keeps_a_snapshot_of_its_table(domain, draw, values, key):
    owner = detached(
        f"Key := {domain}\nF := Key → ℝ\nz : Key\nz ~ {draw}\ny : ℝ\ny(_tab) ~ N(_tab[z], 1)",
        values,
    )
    assert owner.bindings

    if isinstance(values, dict):
        values[key] = 42.0
    else:
        values[-1] = 42.0
    concrete = specialize_distribution(owner, {"z": key})
    assert numeric_value(concrete.term.args[0], {}) == 7.0
    assert concrete.bindings == ()
    first_key = "low" if isinstance(key, str) else 1
    assert numeric_value(specialize_distribution(owner, {"z": first_key}).term.args[0], {}) == 2.0
    assert to_source(owner.term) == "N(_tab[z], 1)"


@pytest.mark.parametrize("coordinate", ("z", "k"))
def test_detached_law_uses_callable_after_its_argument_is_supplied(coordinate):
    calls = []

    def variance(z):
        calls.append(z)
        return 2.0 + z

    owner = detached(
        f"F := ℝ → ℝ\nz : ℝ\nz ~ N(0, 1)\ny : ℝ\ny(_tab) ~ N(0, _tab({coordinate}))",
        variance,
    )
    assert owner.bindings

    assert calls == []
    assert owner.bindings[0][1] is variance
    assert numeric_value(specialize_distribution(owner, {coordinate: 3.0}).term.args[1], {}) == 5.0
    with pytest.raises(ConstructionError, match="negative") as refusal:
        specialize_distribution(owner, {coordinate: -3.0})
    assert refusal.value.rule == "distribution-domain"
    assert calls == [3.0, -3.0]



def test_detached_table_domain_keeps_calibrated_bounds():
    owner = detached(
        "J : ℕ\nKeys := {1, …, J}\nF := Keys → ℝ\nZ := {1, 3}\n"
        "z : Z\nz ~ Bernoulli(0.5)\ny : ℝ\ny(_tab) ~ N(_tab[z], 1)",
        [2.0, 5.0, 7.0],
        calibration={"J": 3},
    )
    concrete = specialize_distribution(owner, {"z": 3})
    assert numeric_value(concrete.term.args[0], {}) == 7.0


def test_detached_law_inlines_called_functions_and_their_calibration():
    owner = detached(
        "F := ℝ\nβ : ℝ\ng(x : ℝ) := 2*x + β\nf(x : ℝ) := g(x) + 1\nh := f\n"
        "z : ℝ\nz ~ N(0, 1)\ny : ℝ\ny(_tab) ~ N(h(z) + _tab, 1)",
        4.0,
        calibration={"β": 3.0},
    )
    assert owner.bindings == ()
    for z, expected in ((1.0, 10.0), (3.0, 14.0)):
        concrete = specialize_distribution(owner, {"z": z})
        assert numeric_value(concrete.term.args[0], {}) == expected



def test_detached_nested_table_retains_a_supplied_label_key():
    laws = (
        "Region := {north, south}\nKeys := {1, 3}\nF := Region × Keys → ℝ\n"
        "z : Keys\nz ~ Bernoulli(0.5)\ny : ℝ\ny(_tab, _region) ~ N(_tab[_region][z], 1)"
    )
    text = (
        STAGE.replace("@stage: law_cases", "@stage: law_cases\n" + laws)
        .replace("(k : ℝ, z, y, tab)", "(k : ℝ, z, y, tab, region)")
        .replace("y(tab)", "y(tab, region)")
        .replace("tab : F @ !vlu @ !cnst, c", "tab : F @ !vlu @ !cnst, region : Region @ !vlu @ !cnst, c")
    )
    stage = elaborate_text(text, "law_cases.bl")
    supplied = {"W[>]": lambda a: a, "tab": [[2.0, 7.0], [11.0, 17.0]], "region": "south"}
    stage.check_inputs(supplied)
    law = numerical_law(
        stage, builder="dcsn_to_arvl", integrated=("y",), given=("z",), inputs=supplied
    )
    owner = specialize_distribution(law.declarations[0], {"z": 3})
    assert numeric_value(owner.term.args[0], {}) == 17.0
