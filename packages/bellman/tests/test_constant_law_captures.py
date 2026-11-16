"""Constants read by a law of motion remain inputs of its pullbacks."""

from pathlib import Path
from unicodedata import normalize

import pytest

from bellman.graphs.initial_diagrams import GRAINS
from bellman.stage import elaborate_text
from bellman.stage.grains import graph_of
from bellman.trellis import assemble_trellis
from test_modular_fields import CONSUMPTION

_APPLICATIONS = Path(__file__).resolve().parents[3] / "applications"


def _stage(application, period, key):
    recipe = _APPLICATIONS / application / "declaration"
    return assemble_trellis(recipe, "spec.yml")["periods"][period]["stages"][key]


def _fields(signature):
    return tuple(wire.identity.field for wire in signature.inputs)


def _zero(*coordinates):
    return 0.0


def _kernel_values(piece, values):
    return dict(zip(
        piece.outputs,
        piece.function(*(values[name] for name in piece.arguments), *piece.parameter_values),
        strict=True,
    ))


def test_durables_sections_and_policy_use_their_incoming_ages():
    stage = _stage("durables", 0, "tenure")
    inputs = {"V_kp[>]": _zero, "V_adj[>]": _zero, "age_kp[>]": 61, "age_adj[>]": 62}
    for builders in (stage.declared, stage.builder):
        policy = builders.policy
        assert _fields(policy.signature()) == ("V_kp", "V_adj", "age_kp", "age_adj")
        kernels = policy.kernels(inputs=inputs)
        assert tuple(normalize("NFKC", name) for name in kernels.inputs) == (
            "V_kp≻", "V_adj≻", "age_kp≻", "age_adj≻",
        )
        for grain in GRAINS:
            graph = graph_of(builders.version, "builders", "backward", grain)
            names = [wire.identity.field for wire in graph.dom.inside]
            assert names.count("age_kp") == names.count("age_adj") == 1
        for label, suffix in (("keep", "kp"), ("adjust", "adj")):
            pullback = policy.primitives[f"Pullback:{label}"]
            assert _fields(pullback.signature()) == (f"V_{suffix}", f"age_{suffix}")
            assert tuple(name for name, _ in pullback.kernel().section.arguments) == (
                "a_d", "h_d", "z_d", f"age_{suffix}",
            )
        for builder in (policy, builders["cntn", "dcsn"], builders["dcsn", "cntn"]):
            card = " ".join(str(builder.denote()).split())
            assert "UNRESOLVED" not in card
            assert "𝑔_keep≻(a_d, h_d, z_d, age_kp) =" in card
            assert "𝑔_adjust≻(a_d, h_d, z_d, age_adj) =" in card
            assert "𝑔_keep≻(a_d, h_d, z_d, 𝑎𝑔𝑒_kp≻())" in card
            assert "𝑔_adjust≻(a_d, h_d, z_d, 𝑎𝑔𝑒_adj≻())" in card

    kernels = stage.dcsn.builder.policy.kernels(inputs=inputs)
    values = {"a_d": 2, "h_d": 3, "z_d": 4, "age_kp": 61, "age_adj": 62, "d": "keep"}
    for label in ("keep", "adjust"):
        piece = next(p for p in kernels.pieces if p.key == f"Pullback:{label}")
        assert {"age_kp", "age_adj"} <= set(piece.arguments)
        base = _kernel_values(piece, values)
        keep = _kernel_values(piece, {**values, "age_kp": 62})
        adjust = _kernel_values(piece, {**values, "age_adj": 61})
        assert base["w_kp≻"] == pytest.approx(adjust["w_kp≻"])
        assert base["w_adj≻"] == pytest.approx(keep["w_adj≻"])
        assert base["w_kp≻"] != keep["w_kp≻"]
        assert base["w_adj≻"] != adjust["w_adj≻"]


def test_benhabib_applies_g_to_the_age_and_state():
    stage = _stage("benhabib-2019", 1, "benhabib_bellman")
    assert "age" in _fields(stage.declared.policy.signature())
    for policy in (stage.declared.policy, stage.builder.policy):
        assert "𝑔≻(m, cp, 𝑎𝑔𝑒≻())" in " ".join(str(policy.denote()).split())
    for builder in (
        stage.declared.policy, stage.dcsn.builder.policy,
        stage.dcsn.builder.bwd, stage.dcsn.builder.fwd,
    ):
        assert "law-of-motion coordinate adaptation" not in str(builder.denote())


def test_two_pullbacks_share_the_constant_without_sharing_the_guard():
    text = (
        CONSUMPTION.replace("Γ_c(x : ℝ) := [0, x]", "Γ_c(x : ℝ) := [0, 1]")
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, age[>])")
        .replace("a = m - c", "a = m - c + age[>]")
        .replace("(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ @ !vlu, B[>] : ℝ @ !vlu, age[>] : ℝ @ !vlu @ !cnst, c)")
        .replace("(W : ℝ @ !vlu) : !dcsn", "(W : ℝ @ !vlu, B : ℝ @ !vlu) : !dcsn")
        .replace("W = c + W[>]/2", "W = if m > 0 then W[>] else 0\n    B = B[>] + c")
        .replace("(W) : !dcsn -> (W[<] : ℝ @ !vlu)", "(W, B) : !dcsn -> (W[<] : ℝ @ !vlu, B[<] : ℝ @ !vlu)")
        .replace("W[<] = W", "W[<] = W\n    B[<] = B")
        .replace("c = argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "c = 0")
    )
    stage = elaborate_text(text, "guarded-law.bl")
    builder = stage.dcsn.builder.bwd
    piece = builder.primitives["Pullback"]
    assert _fields(piece.signature()) == ("W", "B", "age")
    assert tuple(output.identity.field for output in piece.signature().outputs) == ("W", "B")
    record = builder.kernels(inputs={"W[>]": _zero, "B[>]": _zero, "age[>]": 2})
    (guard,) = record.guards["Pullback"]
    assert guard.subject.field == "W"
    assert guard.arguments == ("m",)
    assert not guard.function(0)
    assert guard.function(1)
