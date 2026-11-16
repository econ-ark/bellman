"""Shock law arguments have scope before a forward edge supplies them."""

from bellman.fold.conditions import numerical_law
from bellman.stage import elaborate_text
from bellman.syntax.source import to_source
from test_modular_fields import CONSUMPTION

LAW = "y : ℝ\ny(_mu) ~ N(_mu, 1)"


def _law_card(stage):
    (definition,) = (d for d in stage.definitions.values() if d.kind == "distribution")
    return stage.definitions.denote(definition.identity)


def test_unapplied_law_binds_its_formal_with_an_unresolved_domain():
    stage = elaborate_text(f"@stage: example\n{LAW}\n", "unapplied_law.bl")
    card = _law_card(stage)
    assert "_mu ↦ N(_mu, 1)" in str(card)
    assert "UNRESOLVED[_mu; argument set]" in str(card.denoted[0].mathematical_type)
    refusal = numerical_law(stage, builder="cntn_to_dcsn", integrated=("y",))
    assert refusal.diagnostic["rule"] == "law-requirement"
    assert "requires the arguments _mu" in refusal.reason


def test_applied_law_uses_the_supplied_constant_domain_and_value():
    text = (
        CONSUMPTION.replace("@stage: consumption", f"@stage: consumption\n{LAW}")
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y, location[>])")
        .replace("a = m - c", "a = m - c + y(location[>])")
        .replace(
            "(W[>] : ℝ @ !vlu, c)",
            "(W[>] : ℝ @ !vlu, location[>] : ℝ₊ @ !vlu @ !cnst, c)",
        )
        .replace("W = c + W[>]/2", "W = c + E_{y}(W[>])/2")
        .replace("cp + W[>]/2", "cp + E_{y}(W[>])/2")
    )
    stage = elaborate_text(text, "applied_law.bl")
    assert str(_law_card(stage).denoted[0].mathematical_type) == "ℝ₊ → probability measure on ℝ"
    builder = stage.builder["dcsn", "cntn"]
    missing = builder.kernels().laws["DistributionExtension:y"]
    assert missing.diagnostic["rule"] == "law-requirement"
    assert "requires continuation fields location[>]" in missing.reason
    for location in (1, 2):
        laws = builder.kernels(inputs={"W[>]": lambda a: a, "location[>]": location}).laws
        (declaration,) = laws["DistributionExtension:y"].declarations
        assert to_source(declaration.term) == f"N({location}, 1)"
