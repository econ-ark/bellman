"""A branch's value and derivative use the same applied categorical law."""

import numpy as np
import pytest

from bellman.distributions.families import numeric_value
from bellman.fold.stage_fold import stage_blocks_of
from bellman.stage import elaborate_text
from bellman.syntax.source import to_source

MORTALITY = """\
@stage: mortality
Ages := {0, 1}
p : Ages → [0, 1]
s : {survive, die}
s(_time) ~ Categorical((p[_time], 1 - p[_time]))
[id=arvl_to_dcsn, (a_1 : ℝ₊) : !arvl -> (a_m : ℝ₊) : !dcsn] {
    a_m = a_1
}
[id=dcsn_to_cntn, (a_m, s, age) : !dcsn -> ()] {
    [label=survive, () -> (a_2 : ℝ₊) : !cntn] {
        a_2 = a_m
    }
    [label=die, () -> (a_b : ℝ₊, death : {survive, die}) : !cntn] {
        a_b = a_m
        death = s(age)
    }
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, age : Ages @ !vlu @ !cnst) : !cntn
    -> (V : ℝ @ !vlu, age) : !dcsn] {
    V = E_{s}((V[>], -1/(a_m + 1))[s])
    D_{a_m}V = E_{s}((D_{a_2}V[>], 1/(a_m + 1)^2)[s]) :: [id=marginal]
}
[id=dcsn_to_arvl, (V, age) : !dcsn -> (V[<] : ℝ @ !vlu, age) : !arvl] {
    V[<] = V
}
"""


@pytest.mark.parametrize("use_function", [False, True], ids=("table", "function"))
def test_applied_categorical_weights_are_arguments_of_the_value_kernel(use_function):
    text = MORTALITY
    if use_function:
        text = text.replace("s : {survive, die}", "prob(t : Ages) := p[t]\ns : {survive, die}")
        text = text.replace("p[_time]", "prob(_time)")
    stage = (
        elaborate_text(text, "mortality.bl")
        .methodize({})
        .calibrate({"p": [0.9, 0.6]})
        .configure({})
    )
    original = to_source(stage_blocks_of(stage).owners[0].term)
    for age, probability in ((0, 0.9), (1, 0.6), (0, 0.9)):
        supplied = {"V[>]": lambda a: 7.0, "age": age}
        records = stage.builder["cntn", "dcsn"].kernels(inputs=supplied)
        value = next(
            piece
            for identity, piece in records.output_kernels["Aggregation"].items()
            if identity.field == "V"
        )
        arguments = {"age": age, "V≻": 7.0, "a_m": 3.0}
        result = value.function(
            *(arguments[name] for name in value.arguments), *value.parameter_values
        )
        assert result == pytest.approx(probability * 7 - (1 - probability) / 4)
        assert value.arguments.count("age") == 1
        assert "_time" not in str(value.kernel)

        derivative = next(piece for piece in records.pieces if piece.kind == "Derivative")
        law = records.laws[derivative.key]
        weights = tuple(numeric_value(item, {}) for item in law.declarations[0].term.args[0].items)
        arguments = {"a_m": 3.0, "D_{a_2}V[>]": 2.0}
        components = []
        for label in ("survive", "die"):
            arguments["s"] = label
            components.append(
                derivative.function(
                    *(arguments[name] for name in derivative.arguments),
                    *derivative.parameter_values,
                )
            )
        assert np.dot(weights, components) == pytest.approx(
            probability * 2 + (1 - probability) / 16
        )
        assert to_source(stage_blocks_of(stage).owners[0].term) == original
