"""Scope of controls in distributions used by a policy objective."""

import pytest

from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text


@pytest.mark.parametrize("candidate", ("c", "cp"))
def test_a_candidate_control_supplies_the_laws_in_its_objective(candidate):
    text = (
        TWO_NODES.replace("y ~ N(0,1)", "y ~ N(c,1)")
        .replace("z ~ N(0,1)", "z ~ N(y,1)")
        .replace("argmax_{c :", f"argmax_{{{candidate} :")
    )
    stage = elaborate_text(text, "two-nodes.bl")
    signature = stage.dcsn.builder.policy.signature()
    assert tuple(port.identity.field for port in signature.inputs) == ("V",)
    assert tuple(port.identity.field for port in signature.outputs) == ("c",)

    unbound = text.replace(
        f"argmax_{{{candidate} : Γ(k_d)}}(E_{{y,z}}(β*V[>]) + E_{{y,z}}(β*V[>]))",
        "E_{y,z}(y)",
    )
    with pytest.raises(ConstructionError) as refusal:
        elaborate_text(unbound, "two-nodes.bl")
    assert refusal.value.rule == "output-defined"
