"""The connection of two periods whose declared sets write a bound, and the
compiled kernel of a line that bounds a field by `max` or `min`.

The tests of the connection read two periods of the buffer-stock stage,
joined by the connector `{a: k}`, through `elaborate_trellis`,
`calibrate_trellis` and `connection_report`. End-of-period assets `a` leave
the earlier period and beginning-of-period assets `k` enter the later one,
so the report answers whether the declared set of `a` lies in the declared
set of `k`.

1. A set written with one condition that compares its variable with a
   bound, `{x : ℝ | x > 0}`, is decided as the interval with that bound,
   `(0, inf)`, is.
2. A bound that names a derived parameter is read at the value that the
   definition of the derived parameter takes at the calibration.
3. A comparison that the report leaves undecided states why, and no reason
   names the variable of a condition as a bound.

The tests of the kernel read the buffer-stock stage with a second
value-type field `L` and a parameter `b : ℝ`, and call `compile_kernel()`
on the aggregation of its value builder.

4. The decision line `L = max(L[>], b)` compiles, and the function returns
   the greater of the two numbers beside the value.
5. The decision line `L = min(L[>], b)` compiles, and the function returns
   the lesser of the two numbers beside the value.
"""

import numpy as np
import pytest
from conftest import (
    DERIVED_BUFFER_STOCK_CALIBRATION,
    derived_buffer_stock_text,
    stage_from_text,
)

from bellman.trellis import calibrate_trellis, connection_report, elaborate_trellis

# the two places where the buffer-stock stage file declares the set of `a`
# and of `k`, and the line that defines that set
ARRIVAL, CONTINUATION, SET = "(k : Xa, ψ, ξ)", "(a : Xa)", "Xa := ℝ₊₊\n"


def changed(*changes):
    """The text of the buffer-stock stage file with each pair (text as
    written, text as changed) replaced once."""
    text = derived_buffer_stock_text()
    for written, replacement in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, replacement)
    return text


def named_sets(of_a, of_k, declarations=""):
    """The stage text with `a` declared in the named set `Xa := of_a` and
    `k` in a second named set `Xk := of_k`, after the further
    `declarations`."""
    return changed(
        (SET, f"{declarations}Xa := {of_a}\nXk := {of_k}\n"), (ARRIVAL, "(k : Xk, ψ, ξ)")
    )


def listed_sets(of_a, of_k, declarations=""):
    """The stage text with the sets of `a` and of `k` written in the header
    listings, after the further `declarations`."""
    return changed(
        (SET, SET + declarations),
        (ARRIVAL, f"(k : {of_k}, ψ, ξ)"),
        (CONTINUATION, f"(a : {of_a})"),
    )


def pair_and_route(text, calibration=None):
    """The one pair and the one route that the connection report answers
    for two periods of the stage `text` joined by `{a: k}`, each period
    calibrated with `calibration` where one is given."""
    record = {
        "stage": {"text": text, "origin": "buffer_stock.bl"},
        "calibration": calibration or {},
        "settings": {},
        "methods": {},
    }
    syntactic = {
        "periods": [{"stages": {"bs": record}, "connectors": []} for _ in range(2)],
        "inter_connectors": [{"a": "k"}],
    }
    trellis = elaborate_trellis(syntactic)
    if calibration is not None:
        trellis = calibrate_trellis(trellis, syntactic)
    report = connection_report(trellis)
    (pair,), (route,) = report.pairs, report.routes
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    return pair, route


def test_a_set_with_one_condition_on_its_variable_is_decided_as_the_interval_with_that_bound():
    calibration = DERIVED_BUFFER_STOCK_CALIBRATION
    # the set of `a` lies in the set of `k`
    for text in (
        named_sets("{x : ℝ | x > 0}", "{x : ℝ | x > -0.3}"),
        listed_sets("(0, inf)", "(-0.3, inf)"),
    ):
        pair, route = pair_and_route(text, calibration)
        assert (pair.compatibility, route.status) == ("compatible", "certified")
    pair, _ = pair_and_route(named_sets("{x : ℝ | x > 0}", "{x : ℝ | x > -0.3}"), calibration)
    assert pair.reason == (
        "the continuation set of periods[1].bs.a, ℝ @ (0, inf), lies in the arrival set of "
        "periods[0].bs.k, ℝ @ (-0.3, inf)"
    )
    # the set of `a` does not lie in the set of `k`
    for text in (
        named_sets("{x : ℝ | x > -0.5}", "{x : ℝ | x > -0.3}"),
        listed_sets("(-0.5, inf)", "(-0.3, inf)"),
    ):
        pair, route = pair_and_route(text, calibration)
        assert (pair.compatibility, route.status) == ("incompatible", "uncertified")
    # a weak bound against a strict one at the same number, and an upper bound
    # within a restricted set that has a lower end of its own
    pair, _ = pair_and_route(named_sets("{x : ℝ | x >= 0}", "{x : ℝ | x > 0}"), calibration)
    assert pair.compatibility == "incompatible"
    pair, _ = pair_and_route(named_sets("{x : ℝ₊ | x < 5}", "{x : ℝ | x >= 0}"), calibration)
    assert pair.compatibility == "compatible"
    # one set written on both sides is one set
    pair, route = pair_and_route(changed((SET, "Xa := {x : ℝ | x > 0}\n")))
    assert (pair.compatibility, route.status) == ("compatible", "certified")
    assert "are one set, ℝ @ (0, inf)" in pair.reason
    # a bound that names a parameter is read at the parameter's value
    text = named_sets("{x : ℝ | x > l}", "{x : ℝ | x > j}", "l : ℝ\nj : ℝ\n")
    pair, _ = pair_and_route(text, {**calibration, "l": 0.0, "j": -0.25})
    assert pair.compatibility == "compatible" and len(pair.basis) == 2
    assert "(0, inf) against (-0.25, inf)" in pair.reason
    pair, _ = pair_and_route(text, {**calibration, "l": 0.0, "j": 0.25})
    assert pair.compatibility == "incompatible"
    assert "(0, inf) against (0.25, inf)" in pair.reason


def test_a_bound_that_is_a_derived_parameter_is_read_at_its_value():
    calibration = {**DERIVED_BUFFER_STOCK_CALIBRATION, "l": 0.0}
    # the set of `a` lies in the set of `k`: j is -0.25 at the calibration
    for text in (
        listed_sets("(l, inf)", "(j, inf)", "l : ℝ\nj := l - 0.25\n"),
        named_sets("{x : ℝ | x > l}", "{x : ℝ | x > j}", "l : ℝ\nj := l - 0.25\n"),
    ):
        pair, route = pair_and_route(text, calibration)
        assert (pair.compatibility, route.status) == ("compatible", "certified")
        assert "at the values l = 0.0 of periods[1].bs, j = -0.25 of periods[0].bs" in pair.reason
        assert "(0, inf) against (-0.25, inf)" in pair.reason
        # the comparison names the calibration of each period that it read
        assert [entry[:2] for entry in pair.basis] == [(1, "bs"), (0, "bs")]
    # the set of `a` does not lie in the set of `k`: j is 0.25 there
    text = listed_sets("(l, inf)", "(j, inf)", "l : ℝ\nj := l + 0.25\n")
    pair, route = pair_and_route(text, calibration)
    assert (pair.compatibility, route.status) == ("incompatible", "uncertified")
    assert "(0, inf) against (0.25, inf)" in pair.reason
    # without a calibration the derived parameter has no value
    pair, _ = pair_and_route(text)
    assert pair.compatibility == "not-established" and pair.basis == ()


def test_an_undecided_comparison_states_its_reason_and_names_no_variable_as_a_bound():
    # two bounds without values: the reason names the two parameters, not `x`
    text = named_sets("{x : ℝ | x > l}", "{x : ℝ | x > j}", "l : ℝ\nj : ℝ\n")
    pair, route = pair_and_route(text)
    assert (pair.compatibility, route.status) == ("not-established", "uncertified")
    assert pair.reason == (
        "the bounds j of periods[0].bs and l of periods[1].bs have no finite value in the "
        "bindings given, so the continuation set of periods[1].bs.a, ℝ @ (l, inf), against the "
        "arrival set of periods[0].bs.k, ℝ @ (j, inf), is not decided"
    )
    # a condition on a product of the variable, and two conditions: the
    # reason says that the form is not compared, and names no bound
    for of_a in ("{x : ℝ | x*x > 2}", "{x : ℝ | x > 0, x < 5}"):
        text = named_sets(of_a, "{x : ℝ | x > -0.3}")
        pair, route = pair_and_route(text, DERIVED_BUFFER_STOCK_CALIBRATION)
        assert (pair.compatibility, route.status) == ("not-established", "uncertified")
        assert "is of a form the package does not compare against" in pair.reason
        assert "bound" not in pair.reason
    # one set written on both sides whose condition calls a function of the
    # stage: the function reads a parameter, which has a value of its own in
    # each period, so the two uses are not decided to be one set
    text = changed((SET, "l : ℝ\n𝑓(y : ℝ) := y + l\nXa := {x : ℝ | x >= 𝑓(0)}\n"))
    pair, route = pair_and_route(text, {**DERIVED_BUFFER_STOCK_CALIBRATION, "l": 0.0})
    assert (pair.compatibility, route.status) == ("not-established", "uncertified")
    assert "is of a form the package does not compare against" in pair.reason
    assert "bound" not in pair.reason


# --- the compiled kernel of a line that bounds a field ---

# the header and the line of the two blocks of the buffer-stock stage file
# that write the value: the value block and the arrival block
VALUE_HEADER = "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]"
VALUE_LINE = "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
ARRIVAL_HEADER = "(V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl]"
ARRIVAL_LINE = "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"


def aggregation(decision_line, declarations="b : ℝ\n"):
    """The aggregation of the value builder of the buffer-stock stage with a
    second value-type field `L`, written as the value is: `decision_line`
    writes `L` in the value block, and the arrival block writes `L[<] =
    E_{ψ,ξ}(L)`. The stage declares the parameter `b : ℝ` and is calibrated
    at b = -1."""
    text = changed(
        (SET, SET + declarations),
        (
            VALUE_HEADER,
            "(V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
            " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn]",
        ),
        (VALUE_LINE, f"{VALUE_LINE}    {decision_line}\n"),
        (ARRIVAL_HEADER, "(V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl]"),
        (ARRIVAL_LINE, f"{ARRIVAL_LINE}    L[<] = E_{{ψ,ξ}}(L)\n"),
    )
    stage = stage_from_text(text, "buffer_stock.bl")
    stage.calibrate({"calibration": {**DERIVED_BUFFER_STOCK_CALIBRATION, "b": -1.0}})
    return stage.builder["cntn", "dcsn"]["Aggregation"]


def value_and_bound(piece, continuation_bound):
    """What the compiled kernel of `piece` returns at the continuation values
    1, 2 and 3 of the value and `continuation_bound` of the second field,
    resources 2 and consumption 0.5, with the calibrated parameters: the
    value and the second field, each as a list."""
    kernel = piece.kernel()
    assert kernel.parameters == ("b", "β", "ρ")
    assert kernel.parameter_values == (-1.0, 0.96, 2.0)
    function = piece.compile_kernel()
    value, bound = function(
        np.array([1.0, 2.0, 3.0]), np.array(continuation_bound), 2.0, 0.5, *kernel.parameter_values
    )
    return value.tolist(), bound.tolist()


def test_max_on_a_line_of_a_block_compiles_to_the_greater_of_its_arguments():
    piece = aggregation("L = max(L[>], b)")
    assert str(piece.kernel()).splitlines()[0] == (
        "𝐺 of cntn_to_dcsn: 𝐺(V≻, L≻, m, c) = (𝑢(c) + β*V≻, max(L≻, b))"
    )
    value, bound = value_and_bound(piece, [-2.0, -1.0, 0.5])
    # 𝑢(0.5) = -2 at ρ = 2, and β = 0.96
    assert value == pytest.approx([-1.04, -0.08, 0.88])
    assert bound == [-1.0, -1.0, 0.5]
    assert "L = np.maximum(1.0*L_cntn, b)" in piece.kernel().python
    # a function named `max` that the stage defines is the function called
    own = aggregation("L = max(L[>], b)", "b : ℝ\nmax(x : ℝ, y : ℝ) := x + y\n")
    assert value_and_bound(own, [-2.0, -1.0, 0.5])[1] == [-3.0, -2.0, -0.5]


def test_min_on_a_line_of_a_block_compiles_to_the_lesser_of_its_arguments():
    piece = aggregation("L = min(L[>], b)")
    assert str(piece.kernel()).splitlines()[0] == (
        "𝐺 of cntn_to_dcsn: 𝐺(V≻, L≻, m, c) = (𝑢(c) + β*V≻, min(L≻, b))"
    )
    value, bound = value_and_bound(piece, [-2.0, -1.0, 0.5])
    assert value == pytest.approx([-1.04, -0.08, 0.88])
    assert bound == [-2.0, -1.0, -1.0]
    assert "L = np.minimum(1.0*L_cntn, b)" in piece.kernel().python
