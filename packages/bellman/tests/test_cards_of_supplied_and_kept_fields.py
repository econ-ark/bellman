"""Cards, kernels and signatures of fields that a stage takes in or keeps: a
field declared on a product set, a field that depends on some states of its
perch, a value kept on a kept state, a bare name beside the same name written
with a mark, a constant whose value is a function, and a block that keeps
every output."""

import pytest
from test_modular_fields import CONSUMPTION, FUNCTION_VALUE, SECOND_FIELD

from bellman.stage import elaborate_text

_PAIR = """\
@stage: pair
y : ℝ
y ~ N(0, 1)
[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] {
    m = k + y
}
[id=dcsn_to_cntn, (m) : !dcsn -> (a : ℝ) : !cntn] {
    a = m
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L[>] : ℝ × ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu, L : ℝ × ℝ @ !vlu) : !dcsn] {
    V = V[>] + m
    L = L[>]
}
[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ARRIVAL @ !vlu) : !arvl] {
    V[<] = E_{y}(V)
    L[<] = LINE
}
"""

_SHOCK = "@stage: consumption\ny : ℝ\ny ~ N(0, 1)"

# a field that depends on one arrival state of two, sent back by a line
_KNOWN_AT_ARRIVAL = (
    SECOND_FIELD.replace("@stage: consumption", _SHOCK)
    .replace("(k : ℝ) : !arvl -> (m : ℝ)", "(k : ℝ, z : ℝ, y) : !arvl -> (m : ℝ, z_d : ℝ)")
    .replace("m = k + 1", "m = k + y\n    z_d = z")
    .replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = z_d")
    .replace("W[<] = W", "W[<] = E_{y}(W)")
)

# a value that the backward block keeps, on a state that the forward block keeps
_KEPT_ON_A_KEPT_STATE = (
    CONSUMPTION.replace("@stage: consumption", _SHOCK)
    .replace("(k : ℝ) : !arvl -> (m : ℝ)", "(k : ℝ, z : ℝ, y) : !arvl -> (m : ℝ, z)")
    .replace("m = k + 1", "m = k + y")
    .replace("(m, c : ℝ₊ @ !ctrl)", "(m, z, c : ℝ₊ @ !ctrl)")
    .replace("(W : ℝ @ !vlu) : !dcsn", "(W : ℝ @ !vlu, B : ℝ @ !vlu) : !dcsn")
    .replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = z*z")
    .replace("(W) : !dcsn -> (W[<] : ℝ @ !vlu)", "(W, B) : !dcsn -> (W[<] : ℝ @ !vlu, B)")
    .replace("W[<] = W", "W[<] = E_{y}(W)")
)

_EVERY_OUTPUT_KEPT = """\
@stage: pass
Z := {1, 2}
[id=arvl_to_dcsn, (z : Z, a : ℝ) : !arvl -> (z, a) : !dcsn] {}
[id=dcsn_to_cntn, (z, a) : !dcsn -> (z, a) : !cntn] {
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


def _pair(line, arrival):
    """The stage whose field `L` is declared on ℝ × ℝ, with one arrival line."""
    return elaborate_text(_PAIR.replace("LINE", line).replace("ARRIVAL", arrival), "pair.bl")


@pytest.mark.parametrize(
    ("line", "printed", "value"),
    (
        ("E_{y}(max(L))", "sup_{r ∈ {𝐿(𝑔≺(k, y))[1], 𝐿(𝑔≺(k, y))[2]}} [r]", 5.0),
        ("E_{y}(min(L))", "−sup_{r ∈ {−𝐿(𝑔≺(k, y))[1], −𝐿(𝑔≺(k, y))[2]}} [r]", 1.0),
    ),
    ids=("max", "min"),
)
def test_an_extremum_of_a_field_on_a_product_set_reads_its_coordinates(line, printed, value):
    """`max(L)` for a field `L` declared on ℝ × ℝ is the greater of its two
    coordinates: the card writes both, and the kernel returns it."""
    builder = _pair(line, "ℝ").builder["dcsn", "arvl"]
    assert printed in str(builder.denote())
    (piece,) = (piece for piece in builder.kernels().pieces if piece.key == "2:Aggregation:1")
    assert piece.arguments == ("L", "k", "y")
    assert piece.function((1.0, 5.0), 0.0, 0.0) == value


@pytest.mark.parametrize(
    ("line", "arrival"),
    (
        ("E_{y}(L[1])", "ℝ"),
        ("E_{y}(L)", "ℝ × ℝ"),
        ("(E_{y}(L[1]), E_{y}(L[2]))", "ℝ × ℝ"),
    ),
    ids=("one coordinate", "the field", "each coordinate"),
)
def test_kernels_answer_for_an_expectation_of_a_field_on_a_product_set(line, arrival):
    """An expectation whose integrand reads a field declared on ℝ × ℝ has
    kernels. The set of an argument whose result set is not derived is left
    out of the record's sets, and the states keep theirs."""
    record = _pair(line, arrival).builder["dcsn", "arvl"].kernels()
    sets = dict(record.sets)
    assert sets["k"] == sets["y"] == "ℝ"
    assert {piece.kind for piece in record.pieces} >= {"Pullback", "Expectation", "Aggregation"}


@pytest.mark.parametrize(
    "text", (_KNOWN_AT_ARRIVAL, _KEPT_ON_A_KEPT_STATE), ids=("sent back by a line", "kept")
)
def test_a_field_on_one_state_of_two_is_written_at_that_state(text):
    """A decision field that depends on one state is sent back on the arrival
    state it depends on. Its card writes the rule at that state, with no term
    left unresolved, where the law of motion also reads a shock or the forward
    block keeps the state."""
    card = str(elaborate_text(text, "consumption.bl").builder["dcsn", "arvl"].denote())
    assert "UNRESOLVED" not in card
    assert "𝐵≺ = 𝐵(z)" in card


def test_a_card_reads_a_bare_name_as_the_field_listed_bare():
    """In a block that takes in `W[>]` and writes `W`, a later line that
    reads `W` reads the decision field. The card prints it so, as the kernel
    computes it."""
    text = SECOND_FIELD.replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = W + 1")
    builder = elaborate_text(text, "consumption.bl").builder["cntn", "dcsn"]
    assert "𝐵(m) = 𝑊(m) + 1" in str(builder.denote())
    (piece,) = (piece for piece in builder.kernels().pieces if piece.kind == "Aggregation")
    values = {"W≻": 4, "m": 0, "c": 1}
    written = dict(zip(piece.outputs, piece.function(*(values[name] for name in piece.arguments))))
    assert written == {"W": 3, "B": 4}


def test_the_initial_diagram_classifies_a_constant_whose_value_is_a_function():
    """A perch that holds a constant on a set of functions beside a value on
    ℝ classifies each: a set of functions and a set of numbers hold no common
    member."""
    stage = elaborate_text(FUNCTION_VALUE, "consumption.bl")
    signature = str(stage.initial.backward.signature())
    assert "UNRESOLVED" not in signature
    assert "W≻ : {W≻}" in signature
    assert "f≻ : {f≻}" in signature


def test_a_block_that_keeps_every_output_has_an_empty_body():
    """A forward block that lists each of its states on both sides keeps
    them, and writes no line."""
    stage = elaborate_text(_EVERY_OUTPUT_KEPT, "pass.bl")
    for key, written in ((("arvl", "dcsn"), ("z", "a")), (("dcsn", "cntn"), ("z≻", "a≻"))):
        record = stage.builder[key].kernels()
        (piece,) = (piece for piece in record.pieces if piece.kind == "Pushforward")
        assert piece.outputs == written
        assert tuple(piece.function(2, 3.5)) == (2, 3.5)
