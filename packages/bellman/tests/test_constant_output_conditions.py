"""The output conditions of constant and state-dependent fields."""

import pytest

from bellman.stage import elaborate_text
from bellman.syntax import terms as T
from bellman.typing import typed_expressions as S
from test_modular_fields import KEPT_BOUND


@pytest.mark.parametrize("bound", ["L", "L - 1"])
def test_constant_output_conditions_have_no_state_argument(bound):
    stage = elaborate_text(
        KEPT_BOUND.replace("L[<] = L", f"L[<] = {bound}"), "consumption.bl"
    )
    subjects = {}
    for condition in stage.obligations():
        if condition.condition == "aggregation-admissibility":
            output, predicate = condition.entries[-2:]
            subjects[(output.address, output.field)] = predicate.subject

    for block in ("cntn_to_dcsn", "dcsn_to_arvl"):
        assert isinstance(subjects[block, "L"], T.Sym)
        assert isinstance(subjects[block, "W"], S.Apply)
