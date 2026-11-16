"""Concrete intrinsic calls determine the parameters of a detached law."""

import math

import pytest
from test_detached_distribution_laws import detached

from bellman.distributions.families import numeric_value, specialize_distribution
from bellman.refusals import ConstructionError
from bellman.syntax.source import to_source


def law_with(body, *, declarations="", domain="ℝ"):
    return detached(
        f"F := ℝ\n{declarations}g(x : {domain}) := {body}\n"
        "z : ℝ\nz ~ N(0, 1)\ny : ℝ\ny(_tab) ~ N(0, g(z))",
        1.0,
    )


def test_detached_logarithm_is_evaluated_when_its_argument_is_supplied():
    owner = law_with("log(x)", domain="ℝ₊₊")
    assert to_source(owner.term) == "N(0, log(z))"
    assert specialize_distribution(owner, {}).term == owner.term

    concrete = specialize_distribution(owner, {"z": math.e})
    assert numeric_value(concrete.term.args[1], {}) == pytest.approx(1.0)

    with pytest.raises(ConstructionError, match="negative") as variance:
        specialize_distribution(owner, {"z": 0.5})
    assert variance.value.rule == "distribution-domain"
    with pytest.raises(ConstructionError, match="log") as undefined:
        specialize_distribution(owner, {"z": -1.0})
    assert undefined.value.rule == "distribution-domain"


@pytest.mark.parametrize(
    "body,coordinate,expected",
    (
        ("exp(x)", 0.0, 1.0),
        ("min(x, 2)", 4.0, 2.0),
        ("max(x, 2)", 1.0, 2.0),
        ("min((x, 2))", 4.0, 2.0),
    ),
)
def test_detached_concrete_elementary_functions_and_extrema(body, coordinate, expected):
    owner = law_with(body)
    concrete = specialize_distribution(owner, {"z": coordinate})
    assert numeric_value(concrete.term.args[1], {}) == expected


def test_detached_authored_function_can_use_an_intrinsic_name():
    owner = law_with("log(x)", declarations="log(x : ℝ) := x + 2\n")
    concrete = specialize_distribution(owner, {"z": -1.0})
    assert numeric_value(concrete.term.args[1], {}) == 1.0



@pytest.mark.parametrize("body", ("exp(x)", "unprovided(x)"))
def test_detached_concrete_call_without_a_value_is_refused(body):
    owner = law_with(body)
    with pytest.raises(ConstructionError) as refusal:
        specialize_distribution(owner, {"z": 1000.0})
    assert refusal.value.rule == "distribution-domain"
