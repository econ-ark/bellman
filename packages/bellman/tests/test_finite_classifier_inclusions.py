"""Inclusion of finite sets and the sets of real coordinates."""

from bellman.syntax import terms as T
from bellman.typing.sets import within


def test_finite_and_infinite_classifier_inclusions():
    age = T.IntegerRange(T.Number(0), T.Sym(T.Constant("J")))
    levels = T.Points((T.Number(1), T.Number(2), T.Number(3)))
    labels = T.FiniteSet(("survive", "die"))
    real, positive = T.Named("ℝ"), T.Named("ℝ₊₊")
    assert within(age, real, {}) is True
    assert within(real, age, {}) is False
    assert within(positive, levels, {}) is False
    assert within(labels, real, {}) is False
    assert within(real, labels, {}) is False
    assert within(T.IntegerRange(T.Sym(T.Constant("first")), T.Number(3)), positive, {}) is None
