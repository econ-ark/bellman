"""Table indices in shock laws are checked at their formal arguments."""

import pytest

from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text
from bellman.syntax.source import to_source
from test_modular_fields import CONSUMPTION

LAW = "t : {1, 2} → ℝ\ny : ℝ\ny(_index) ~ N(t[_index], 1)"


def test_unapplied_law_keeps_its_required_index_membership():
    stage = elaborate_text(f"@stage: probe\n{LAW}\n", "unapplied_table_law.bl")
    (law,) = (item for item in stage.definitions.values() if item.kind == "distribution")
    card = stage.definitions.denote(law.identity)
    assert "_index ↦ N(t[_index], 1)" in str(card)
    assert "UNRESOLVED[_index; argument set]" in str(card.denoted[0].mathematical_type)
    assert "_index ∈ {1, 2}" in str(card)
    (membership,) = (item for item in stage.obligations() if item.condition == "set-inclusion")
    assert membership.status == "required"
    assert membership.predicate.subject.symbol.name.owner == law.identity


@pytest.mark.parametrize("index_set", ("{1, 2}", "{3, 4}"))
def test_applied_law_checks_the_supplied_field_against_the_table(index_set):
    text = (
        CONSUMPTION.replace("@stage: consumption", f"@stage: consumption\n{LAW}")
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y, date[>])")
        .replace("a = m - c", "a = m - c + y(date[>])")
        .replace(
            "(W[>] : ℝ @ !vlu, c)",
            f"(W[>] : ℝ @ !vlu, date[>] : {index_set} @ !vlu @ !cnst, c)",
        )
        .replace("W = c + W[>]/2", "W = c + E_{y}(W[>])/2")
        .replace("cp + W[>]/2", "cp + E_{y}(W[>])/2")
    )
    if index_set == "{3, 4}":
        with pytest.raises(ConstructionError, match=r"supplied by 'date'.*not within") as refusal:
            elaborate_text(text, "applied_table_law.bl")
        assert refusal.value.rule == "family-selection"
        return

    stage = (
        elaborate_text(text, "applied_table_law.bl")
        .methodize({})
        .calibrate({"t": [5, 6]})
        .configure({})
    )
    builder = stage.builder["dcsn", "cntn"]
    for date, mean in ((1, 5), (2, 6)):
        laws = builder.kernels(inputs={"W[>]": lambda a: a, "date[>]": date}).laws
        (declaration,) = laws["DistributionExtension:y"].declarations
        assert to_source(declaration.term) == f"N({mean}, 1)"
