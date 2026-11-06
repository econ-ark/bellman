"""The acceptance file of the brief "finite index sets and indexed data
defined by parameters" (Bellman-SYM specification 0.5; the second layer of
the tests, `packages/bellman/README.md` §8): one test for each of the brief's
six acceptance items, through the public construction, binding and query
calls, with every expected number derived from the mathematical example in
the test's docstring.

Numerical keys are integers under AAS's ruling of 19 October 2026: an
integer range with parameter-dependent inclusive bounds, `{0, …, J}`, or a
listed set such as `{0, θ} ⊂ ℤ`. The proposed declaration `q : S → ℝ₊`
associates one real entry with each key; `q[s]` selects by a name declared on
that set, and `dist[j][i]` selects a table entry. A calibration supplies a
sequence in member order or a mapping by integer keys. Keys are distinct;
entries at different keys may be equal and need not be integers.
"""

import json
import warnings
from fractions import Fraction
from pathlib import Path

import numba
import numpy as np
import pytest
from conftest import stage_from_text

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.trellis import calibrate_trellis, connection_report, elaborate_trellis

ROOT = Path(__file__).resolve().parents[3]

# A location stage: J city locations, the previous location i and the chosen
# location j among them, a location payoff δ and a distance table on city
# pairs. The value of choosing j from i is
#     V(i, j) = δ(j) − m_0 − m_1·D(j, i) + β·V≻.
LOCATION = """@stage: location
J   : ℕ
L_J := {1, …, J}
β   : (0,1)
m_0 : ℝ₊
m_1 : ℝ₊
δ   : L_J → ℝ
dist : L_J × L_J → ℝ₊

[id=arvl_to_dcsn, (i : L_J) : !arvl -> (i_d : L_J) : !dcsn] {
    i_d = i    :: [id=carry]
}

[id=dcsn_to_cntn, (i_d, j : !ctrl @ L_J) : !dcsn -> (i_n : L_J) : !cntn] {
    i_n = j    :: [id=move]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, j) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = δ[j] - m_0 - m_1*dist[j][i_d] + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (j : !ctrl) : !dcsn] {
    j = argmax_{jp : L_J}(δ[jp] - m_0 - m_1*dist[jp][i_d] + β*V[>])   :: [id=optimality]
}
"""

# the two calibrations of the location stage: J = 2 and J = 3, the distance
# tables symmetric with zero diagonal, the payoffs δ(j) = j
LOCATION_J2 = {
    "J": 2,
    "β": 0.9,
    "m_0": 0.5,
    "m_1": 2.0,
    "δ": [1.0, 2.0],
    "dist": [[0.0, 1.5], [1.5, 0.0]],
}
LOCATION_J3 = {
    "J": 3,
    "β": 0.9,
    "m_0": 0.5,
    "m_1": 2.0,
    "δ": [1.0, 2.0, 3.0],
    "dist": [[0.0, 1.5, 4.0], [1.5, 0.0, 2.5], [4.0, 2.5, 0.0]],
}

# Almagro's state ranges over the city and the outside option, I_J = {0, …, J},
# while the distance is defined on city pairs alone: the selection
# `dist[j][i_d]` reads the table at a key the declaration does not admit
# unless a condition establishes that both locations are in the city
ALMAGRO_STATE = LOCATION.replace(
    "L_J := {1, …, J}\n", "I_J := {0, …, J}\nL_J := {1, …, J}\n"
).replace("(i : L_J) : !arvl -> (i_d : L_J) : !dcsn", "(i : I_J) : !arvl -> (i_d : I_J) : !dcsn")

# the outside move: a fixed cost m_2 and no distance
OUTSIDE_MOVE = (
    LOCATION.replace("m_1 : ℝ₊\n", "m_1 : ℝ₊\nm_2 : ℝ₊\n")
    .replace(
        "V = δ[j] - m_0 - m_1*dist[j][i_d] + β*V[>]    :: [id=value]",
        "V = δ[j] - m_2 + β*V[>]    :: [id=value]",
    )
    .replace(
        "j = argmax_{jp : L_J}(δ[jp] - m_0 - m_1*dist[jp][i_d] + β*V[>])",
        "j = argmax_{jp : L_J}(δ[jp] - m_2 + β*V[>])",
    )
)

# A stage whose state takes one of two integer values, 0 and θ, with the
# integer condition retained until θ is valued; wealth is the real entry of q:
#     w = q(s),   s ∈ S_θ = {0, θ}.
POINTS = """@stage: points
θ   : ℝ₊
S_θ := {0, θ} ⊂ ℤ
β   : (0,1)
q   : S_θ → ℝ₊
Γ(x : ℝ₊) := [0, x]

[id=arvl_to_dcsn, (s : S_θ) : !arvl -> (w : ℝ₊) : !dcsn] {
    w = q[s]    :: [id=wealth]
}

[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c    :: [id=saving]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = c + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : !ctrl) : !dcsn] {
    c = argmax_{cp : Γ(w)}(cp + β*V[>])   :: [id=optimality]
}
"""
POINTS_REORDERED = POINTS.replace("S_θ := {0, θ} ⊂ ℤ", "S_θ := {θ, 0} ⊂ ℤ")

# A stage with a finite chain on I_J and one indexed normal shock: the next
# state e_n is drawn from the row of Π at the current state e_c, and the
# vector ε of J + 1 correlated components is drawn jointly; the decision
# state reads the component of ε at the drawn state.
CHAIN = """@stage: chain
J   : ℕ
I_J := {0, …, J}
β   : (0,1)
Π   : I_J × I_J → [0, 1]
μ_ε : I_J → ℝ
Σ_ε : I_J × I_J → ℝ
e_n : I_J
e_n ~ Categorical(Π[e_c])
ε   : I_J → ℝ
ε   ~ N(μ_ε, Σ_ε)

[id=arvl_to_dcsn, (e_c : I_J, e_n, ε) : !arvl -> (x : ℝ, e_d : I_J) : !dcsn] {
    x   = ε[e_n]    :: [id=draw]
    e_d = e_n       :: [id=state]
}

[id=dcsn_to_cntn, (x, e_d) : !dcsn -> (x_n : ℝ, e_nxt : I_J) : !cntn] {
    x_n   = x      :: [id=carry]
    e_nxt = e_d    :: [id=state]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = x + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{e_n, ε}(V)    :: [id=value]
}
"""
# the two calibrations of the chain: J = 1 (two states) and J = 2 (three
# states), each with a stochastic matrix and a correlated covariance
CHAIN_J1 = {
    "J": 1,
    "β": 0.9,
    "Π": [[0.9, 0.1], [0.2, 0.8]],
    "μ_ε": [0.0, 1.0],
    "Σ_ε": [[1.0, 0.5], [0.5, 2.0]],
}
CHAIN_J2 = {
    "J": 2,
    "β": 0.9,
    "Π": [[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.1, 0.1, 0.8]],
    "μ_ε": [0.0, 1.0, 2.0],
    "Σ_ε": [[1.0, 0.5, 0.0], [0.5, 2.0, 0.5], [0.0, 0.5, 3.0]],
}


def aggregation(version, builder="cntn_to_dcsn"):
    """The aggregation box of a backward builder, holding the value line."""
    primitives = version.builder.bwd[builder].primitives
    (name,) = [key for key in primitives.list() if key.split(":")[-1] == "Aggregation"]
    return primitives[name]


def pushforward(version, builder="arvl_to_dcsn"):
    """The push-forward box of a forward builder, with the law of motion."""
    primitives = version.builder.fwd[builder].primitives
    (name,) = [key for key in primitives.list() if key.split(":")[-1] == "Pushforward"]
    return primitives[name]


def test_item_1_one_symbolic_location_stage_two_calibrations_of_j_one_compiled_function(encoding_validator):
    """`LOCATION` elaborates once; its state `i`, its choice `j` and its
    binder `jp` lie in `{1, …, J}`, and `dist` on `L_J × L_J → ℝ₊`. The
    calibrations `J = 2` and `J = 3` give the declared domains their counts and
    the kernel its entries without a change of source. The aggregation kernel
    compiled on the symbolic version takes `J` among its parameters, since the
    index set reads it, and evaluates with both calibrations:
    V(1, 2) = 2 − 0.5 − 2·1.5 + 0.9·10 = 7.5 at J = 2, and
    V(1, 3) = 3 − 0.5 − 2·4 + 0.9·10 = 3.5 at J = 3; a batch of keys
    evaluates entry by entry. The versions are independent: the symbolic
    version stays unbound and each calibrated version answers its values."""
    symbolic = stage_from_text(LOCATION, "location.bl")
    printed = str(symbolic.par)
    assert "L_J → ℝ" in printed and "L_J × L_J → ℝ₊" in printed
    assert "in L_J" in str(symbolic.fields())
    assert "L_J := {1, …, J}" in str(symbolic.view())
    box = aggregation(symbolic)
    record = box.kernel()
    assert "δ[j] - m_0 - m_1*dist[j][i_d]" in str(record)
    assert "J" in record.parameters, record.parameters
    assert record.parameter_values is None
    function = box.compile_kernel()

    at_2 = copy_native(symbolic).calibrate(LOCATION_J2)
    at_3 = copy_native(symbolic).calibrate(LOCATION_J3)
    assert at_2.par["J"].value == 2 and at_3.par["J"].value == 3
    assert at_2.par["dist"].value == ((0.0, 1.5), (1.5, 0.0))
    values_2 = aggregation(at_2).kernel().parameter_values
    values_3 = aggregation(at_3).kernel().parameter_values
    assert values_2 is not None and values_3 is not None
    assert float(function(10.0, 1, 2, *values_2)) == 7.5
    assert float(function(10.0, 1, 3, *values_3)) == 3.5
    assert function(10.0, np.array([1, 2]), np.array([2, 1]), *values_2).tolist() == [7.5, 6.5]
    # the key outside the range gives no value, as a label outside its set does
    assert np.isnan(function(10.0, 1, 3, *values_2))
    assert np.isnan(function(10.0, 1, 1.5, *values_2))
    # The same symbolic function also compiles with Numba, including the
    # nested selection and batches of location keys.
    compiled = numba.njit(function)
    assert float(compiled(10.0, 1, 2, *values_2)) == 7.5
    assert float(compiled(10.0, 1, 3, *values_3)) == 3.5
    assert compiled(10.0, np.array([1, 2]), np.array([2, 1]), *values_2).tolist() == [7.5, 6.5]
    assert np.isnan(compiled(10.0, 1, 3, *values_2))
    assert np.isnan(compiled(10.0, 1, 1.5, *values_2))
    assert str(symbolic.par["J"]) == "J : ℕ, unbound"
    for item in symbolic.obligations():
        assert item.status != "established" or item.condition == "range-compatibility"
    # the encoding of the new forms validates against the one schema, and the
    # parsed term decodes to the term the lowering built

    encoding_validator.validate(json.loads(json.dumps(symbolic.encoding())))
    term, _ = parse_with_spans(LOCATION, "location.bl")
    assert from_json(json.loads(json.dumps(to_json(term)))) == term


def test_item_2_integer_keys_are_values_not_positions_and_reordering_preserves_the_result():
    """The keys of `q` are 0 and θ, while its real entries are 10.25 and
    20.75. Integer θ = 2 and θ = 5 select the second entry, not an array
    position. Reordering members and data, or supplying a mapping, preserves
    these values. Equal real entries at different integer keys are allowed.
    Adjacent integers 2**53 and 2**53 + 1 select different entries in Python
    and Numba even though converting both integers to doubles would lose
    their distinction; a double is read as the integer it actually denotes.
    A noninteger θ is refused without changing either earlier version."""
    symbolic = stage_from_text(POINTS, "points.bl")
    assert "S_θ := {0, θ} ⊂ ℤ" in str(symbolic.view())
    assert "S_θ → ℝ₊" in str(symbolic.par)
    law = pushforward(symbolic)
    function = law.compile_kernel()
    compiled = numba.njit(function)
    assert "θ" in law.kernel().parameters
    versions = []
    for member in (2, 5):
        bound = copy_native(symbolic).calibrate({"θ": member, "β": 0.9, "q": [10.25, 20.75]})
        values = pushforward(bound).kernel().parameter_values
        versions.append(bound)
        for evaluate in (function, compiled):
            assert (float(evaluate(member, *values)), float(evaluate(0, *values))) == (
                20.75,
                10.25,
            )
            assert evaluate(np.array([0, member], dtype=np.int64), *values).tolist() == [
                10.25,
                20.75,
            ]
            assert np.isnan(evaluate(1, *values))
            assert np.isnan(evaluate(1.5, *values))
            assert np.isnan(evaluate(False, *values))
            assert np.isnan(evaluate(np.array([False, True]), *values)).all()

    # A complex value is not an integer key even when its imaginary part
    # is zero; discarding that part must not select an entry.
    values = pushforward(versions[0]).kernel().parameter_values
    for key in (0 + 0j, 2 + 0j):
        with warnings.catch_warnings():
            warnings.simplefilter("error", np.exceptions.ComplexWarning)
            assert np.isnan(function(key, *values))
            try:
                result = compiled(key, *values)
            except numba.core.errors.TypingError:
                # Numba may refuse the unsupported complex argument type.
                pass
            else:
                assert np.isnan(result)

    reordered = stage_from_text(POINTS_REORDERED, "points.bl").calibrate(
        {"θ": 5, "β": 0.9, "q": [20.75, 10.25]}
    )
    reordered_box = pushforward(reordered)
    reordered_function = reordered_box.compile_kernel()
    values = reordered_box.kernel().parameter_values
    assert (float(reordered_function(5, *values)), float(reordered_function(0, *values))) == (
        20.75,
        10.25,
    )
    mapped = copy_native(symbolic).calibrate({"θ": 5, "β": 0.9, "q": {5: 20.75, 0: 10.25}})
    values = pushforward(mapped).kernel().parameter_values
    assert mapped.par["q"].value == (10.25, 20.75)
    assert (float(function(5, *values)), float(function(0, *values))) == (20.75, 10.25)
    equal_entries = copy_native(symbolic).calibrate({"θ": 5, "β": 0.9, "q": [0.375, 0.375]})
    values = pushforward(equal_entries).kernel().parameter_values
    assert function(np.array([0, 5]), *values).tolist() == [0.375, 0.375]
    for member in (2.5, Fraction(1, 3)):
        with pytest.raises(ValueError, match="θ"):
            copy_native(symbolic).calibrate({"θ": member, "β": 0.9, "q": [10.25, 20.75]})
    with pytest.raises(ValueError) as duplicate:
        copy_native(symbolic).calibrate({"θ": 0, "β": 0.9, "q": [10.25, 20.75]})
    assert "S_θ" in str(duplicate.value) and "θ" in str(duplicate.value)
    assert [version.par["θ"].value for version in versions] == [2, 5]
    assert symbolic.bindings.calibration is None

    exact = stage_from_text(POINTS.replace("{0, θ} ⊂ ℤ", "{θ + 1, θ} ⊂ ℤ"), "points.bl")
    start = 2**53
    values = {"θ": start, "β": 0.9, "q": {start + 1: 20.75, start: 10.25}}
    first = copy_native(exact).calibrate(values)
    second = copy_native(exact).calibrate(
        {**values, "q": dict(reversed(tuple(values["q"].items())))}
    )
    assert first.par["q"].value == second.par["q"].value == (20.75, 10.25)
    assert first.provenance["source"]["sha256"] == second.provenance["source"]["sha256"]
    exact_function = pushforward(exact).compile_kernel()
    exact_values = pushforward(first).kernel().parameter_values
    for evaluate in (exact_function, numba.njit(exact_function)):
        assert float(evaluate(start, *exact_values)) == 10.25
        assert float(evaluate(start + 1, *exact_values)) == 20.75
        assert evaluate(np.array([start, start + 1], dtype=np.int64), *exact_values).tolist() == [
            10.25,
            20.75,
        ]
        assert evaluate(np.array([start + 1, start], dtype=np.uint64), *exact_values).tolist() == [
            20.75,
            10.25,
        ]
        assert float(evaluate(float(start), *exact_values)) == 10.25
        assert evaluate(np.array([float(start)]), *exact_values).tolist() == [10.25]

    for domain, first_key in (
        ("{9007199254740992, 9007199254740993} ⊂ ℤ", 2**53),
        ("{0, (9007199254740993/1)} ⊂ ℤ", 0),
        ("{0, θ/1} ⊂ ℤ", 0),
    ):
        literal = stage_from_text(POINTS.replace("{0, θ} ⊂ ℤ", domain), "exact-integer.bl")
        bound = copy_native(literal).calibrate({"θ": 2**53 + 1, "β": 0.9, "q": [10.25, 20.75]})
        literal_function = pushforward(literal).compile_kernel()
        values = pushforward(bound).kernel().parameter_values
        for evaluate in (literal_function, numba.njit(literal_function)):
            assert float(evaluate(first_key, *values)) == 10.25
            assert float(evaluate(2**53 + 1, *values)) == 20.75
            if first_key == 2**53:
                assert float(evaluate(float(2**53 + 1), *values)) == 10.25
            else:
                assert np.isnan(evaluate(float(2**53 + 1), *values))


def test_item_3_a_finite_chain_and_an_indexed_shock_share_one_association_by_index():
    """`CHAIN` draws `e_n` from the row of `Π` at `e_c` and the vector `ε` from
    one joint normal on `I_J`. Symbolically the stage retains that each row of
    Π is a probability vector and that the law of `ε` has the dimension of
    `I_J`. At `J = 1` the chain has two states and `Σ_ε` is 2 × 2; at `J = 2`
    three states and 3 × 3; the covariance of the first calibration bound at
    `J = 2` is refused as an old-size law, a row that does not sum to one is
    refused, and a `Π` of the wrong count is refused. The compiled law of
    motion reads the component of ε at the drawn state. Two stages of
    different periods declaring `θ` alike compare their collections at their
    own values: connected fields on `{0, θ} ⊂ ℤ` are compatible with the same
    members in the same order, and refused when the members are reordered or
    the two θ differ."""
    symbolic = stage_from_text(CHAIN, "chain.bl")
    explanations = {item.condition: item.explanation for item in symbolic.obligations()}
    assert any("each row of Π" in text for text in explanations.values())
    assert "in I_J → ℝ" in str(symbolic.fields())
    at_1 = copy_native(symbolic).calibrate(CHAIN_J1)
    at_2 = copy_native(symbolic).calibrate(CHAIN_J2)
    assert at_1.par["Π"].value == ((0.9, 0.1), (0.2, 0.8))
    assert at_2.par["Σ_ε"].value[2] == (0.0, 0.5, 3.0)
    # the named covariance of the old size has two rows where I_J has three
    # members: a wrong count of entries, named by the parameter
    with pytest.raises(ValueError) as old_size:
        copy_native(symbolic).calibrate(
            {**CHAIN_J2, "Σ_ε": CHAIN_J1["Σ_ε"], "μ_ε": CHAIN_J1["μ_ε"]}
        )
    assert "Σ_ε" in str(old_size.value) or "μ_ε" in str(old_size.value)
    # a named covariance that is not symmetric is refused as a law condition
    with pytest.raises(ConstructionError) as asymmetric:
        copy_native(symbolic).calibrate({**CHAIN_J1, "Σ_ε": [[1.0, 0.5], [0.4, 2.0]]})
    assert asymmetric.value.rule == "distribution-domain" and "symmetric" in str(asymmetric.value)
    # Naming scalar parameters does not supply the two-component normal
    # law required by ε when J = 1.
    scalar_law = stage_from_text(
        CHAIN.replace("μ_ε : I_J → ℝ", "μ_ε : ℝ").replace("Σ_ε : I_J × I_J → ℝ", "Σ_ε : ℝ"),
        "chain.bl",
    )
    with pytest.raises(ConstructionError) as scalar_parameters:
        copy_native(scalar_law).calibrate({**CHAIN_J1, "μ_ε": 0.0, "Σ_ε": 1.0})
    assert scalar_parameters.value.rule == "distribution-domain"
    assert "μ_ε" in scalar_parameters.value.message and "Σ_ε" in scalar_parameters.value.message
    assert scalar_parameters.value.address is not None
    # a law written out for two components is accepted at J = 1 and refused
    # at J = 2, where the field has three
    written = stage_from_text(
        CHAIN.replace("ε   ~ N(μ_ε, Σ_ε)", "ε   ~ N((0, 1), ((1, 0.5), (0.5, 2)))"), "chain.bl"
    )
    assert copy_native(written).calibrate(CHAIN_J1).par["J"].value == 1
    with pytest.raises(ConstructionError) as old_written:
        copy_native(written).calibrate(CHAIN_J2)
    assert old_written.value.rule == "distribution-domain" and "3" in str(old_written.value)
    with pytest.raises(ConstructionError) as not_stochastic:
        copy_native(symbolic).calibrate({**CHAIN_J1, "Π": [[0.9, 0.2], [0.2, 0.8]]})
    assert "Π" in str(not_stochastic.value) and "one" in str(not_stochastic.value)
    with pytest.raises(ValueError) as wrong_count:
        copy_native(symbolic).calibrate({**CHAIN_J2, "Π": CHAIN_J1["Π"]})
    assert "Π" in str(wrong_count.value) and "3" in str(wrong_count.value)
    law = pushforward(at_2).compile_kernel()
    values = pushforward(at_2).kernel().parameter_values
    drawn = law(1, 2, np.array([0.0, 1.0, 2.0]), *values)
    assert float(drawn[0]) == 2.0

    def record(text, θ):
        return {
            "stage": {"text": text, "origin": "points.bl"},
            "methods": {},
            "settings": {},
            "calibration": {"θ": θ, "β": 0.9, "q": [10.0, 20.0]},
        }

    def report(later, earlier):
        syntactic = {
            "periods": [
                {"stages": {"A": earlier}, "connectors": []},
                {"stages": {"B": later}, "connectors": []},
            ],
            "inter_connectors": [{"B.v": "v"}],
        }
        trellis = calibrate_trellis(elaborate_trellis(syntactic), syntactic)
        (pair,) = [
            p for p in connection_report(trellis).pairs if str(p.reading) == "periods[0].A.v"
        ]
        return pair.compatibility, pair.reason

    vector = POINTS.replace(
        "(w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = w - c",
        "(w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊, v : S_θ → ℝ₊) : !cntn] {\n"
        "    v = q    :: [id=keep]\n    a = w - c",
    ).replace(
        "(s : S_θ) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = q[s]",
        "(s : S_θ, v : S_θ → ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = v[s]",
    )
    vector_reordered = vector.replace("S_θ := {0, θ} ⊂ ℤ", "S_θ := {θ, 0} ⊂ ℤ")
    status, reason = report(record(vector, 2), record(vector, 2))
    assert status == "compatible", reason
    status, reason = report(record(vector_reordered, 2), record(vector, 2))
    assert status == "incompatible" and "order" in reason
    status, reason = report(record(vector, 5), record(vector, 2))
    assert status == "incompatible" and "periods[1]" in reason and "periods[0]" in reason
    # These exact integers are distinct even though their double
    # representations coincide. A connection preserves the numerical keys.
    status, reason = report(record(vector, 2**53 + 1), record(vector, 2**53))
    assert status == "incompatible", reason
    # a written weight vector has one weight per member of the index set
    written_weights = stage_from_text(
        CHAIN.replace("e_n ~ Categorical(Π[e_c])", "e_n ~ Categorical((0.5, 0.5))"), "chain.bl"
    )
    assert copy_native(written_weights).calibrate(CHAIN_J1).par["J"].value == 1
    with pytest.raises(ConstructionError, match="2 weights"):
        copy_native(written_weights).calibrate(CHAIN_J2)
    # a transition matrix supplied as a mapping is checked as the sequence is
    with pytest.raises(ConstructionError, match="sums to 1.1"):
        copy_native(symbolic).calibrate(
            {**CHAIN_J1, "Π": {0: {0: 0.9, 1: 0.2}, 1: {0: 0.2, 1: 0.8}}}
        )


def test_item_4_refusals_name_declaration_and_key_and_the_versions_stand_after_a_refused_binding():
    """A key outside the declared domain, `dist[j][i_d]` with `i_d` in
    `{0, …, J}` against the city pairs `{1, …, J}`, is refused under
    `family-selection`; so is scalar data indexed as a collection. A
    calibration with a missing or a surplus entry, a bound that is no integer,
    an empty range and a key outside the entry set each receive a refusal
    naming the parameter and the key or ordered pair. After a refused third
    binding the two earlier versions still answer, and a later valid binding
    computes its own count."""
    with pytest.raises(ConstructionError) as outside:
        stage_from_text(ALMAGRO_STATE, "location.bl")
    assert outside.value.rule == "family-selection"
    assert "{0, …, J}" in outside.value.message and "{1, …, J}" in outside.value.message
    with pytest.raises(ConstructionError) as scalar:
        stage_from_text(LOCATION.replace("dist : L_J × L_J → ℝ₊", "dist : ℝ₊"), "location.bl")
    assert scalar.value.rule == "family-selection" and "dist" in scalar.value.message
    with pytest.raises(ConstructionError) as position:
        stage_from_text(LOCATION.replace("δ[j] - m_0", "δ[1] - m_0"), "location.bl")
    assert position.value.rule == "family-selection" and "δ[1]" in position.value.message

    symbolic = stage_from_text(LOCATION, "location.bl")
    at_2 = copy_native(symbolic).calibrate(LOCATION_J2)
    at_3 = copy_native(symbolic).calibrate(LOCATION_J3)
    with pytest.raises(ValueError) as missing:
        copy_native(symbolic).calibrate({**LOCATION_J3, "δ": [1.0, 2.0]})
    assert "δ" in str(missing.value) and "3" in str(missing.value) and "2" in str(missing.value)
    with pytest.raises(ValueError) as surplus:
        copy_native(symbolic).calibrate(
            {**LOCATION_J2, "dist": {1: {1: 0.0, 2: 1.5}, 2: {1: 1.5, 2: 0.0}, 3: {1: 4.0}}}
        )
    assert "dist" in str(surplus.value) and "3" in str(surplus.value)
    with pytest.raises(ValueError) as entry:
        copy_native(symbolic).calibrate({**LOCATION_J2, "dist": [[0.0, -1.5], [1.5, 0.0]]})
    assert (
        "dist" in str(entry.value) and "(1, 2)" in str(entry.value) and "-1.5" in str(entry.value)
    )
    with pytest.raises(ValueError) as fractional:
        copy_native(symbolic).calibrate({**LOCATION_J2, "J": 2.5})
    assert "J" in str(fractional.value)
    with pytest.raises(ValueError) as empty:
        copy_native(symbolic).calibrate({**LOCATION_J2, "J": 0, "δ": [], "dist": []})
    assert "J" in str(empty.value)
    # A distinct integer lower bound cannot be rounded down to the upper
    # bound and turn an empty range into a singleton.
    ordered = stage_from_text(
        LOCATION.replace("J   : ℕ", "J   : ℕ\nK : ℕ").replace(
            "L_J := {1, …, J}", "L_J := {J, …, K}"
        ),
        "ordered-range.bl",
    )
    with pytest.raises(ValueError) as backwards:
        copy_native(ordered).calibrate(
            {**LOCATION_J2, "J": 2**53 + 1, "K": float(2**53), "δ": [], "dist": []}
        )
    assert "J" in str(backwards.value) and "K" in str(backwards.value)
    # the two earlier versions are untouched by the refusals
    assert aggregation(at_2).kernel().parameter_values[0] == 2
    assert aggregation(at_3).kernel().parameter_values[0] == 3
    assert at_2.par["δ"].value == (1.0, 2.0) and at_3.par["δ"].value == (1.0, 2.0, 3.0)
    again = copy_native(symbolic).calibrate(LOCATION_J2)
    assert again.par["dist"].value == at_2.par["dist"].value
    assert symbolic.bindings.calibration is None
    # An exact integer outside consecutive-double precision remains a
    # valid bound. Only the two members of this short range are stored.
    large_range = stage_from_text(
        POINTS.replace("θ   : ℝ₊", "θ   : ℤ").replace("{0, θ} ⊂ ℤ", "{θ, …, θ+1}"),
        "large-range.bl",
    )
    start = 2**53 + 1
    large_bound = copy_native(large_range).calibrate({"θ": start, "β": 0.9, "q": [10.0, 20.0]})
    large_function = pushforward(large_range).compile_kernel()
    large_values = pushforward(large_bound).kernel().parameter_values
    for evaluate in (large_function, numba.njit(large_function)):
        assert float(evaluate(start, *large_values)) == 10.0
        assert float(evaluate(start + 1, *large_values)) == 20.0
        assert evaluate(np.array([start, start + 1], dtype=np.int64), *large_values).tolist() == [
            10.0,
            20.0,
        ]
        # float(start) denotes the integer just below this range.
        assert np.isnan(evaluate(float(start), *large_values))
        assert np.isnan(evaluate(False, *large_values))
    for start, outside in ((2**63 - 2, -(2**63)), (-(2**63), 2**63 - 1)):
        bound = copy_native(large_range).calibrate({"θ": start, "β": 0.9, "q": [10.25, 20.75]})
        values = pushforward(bound).kernel().parameter_values
        for evaluate in (large_function, numba.njit(large_function)):
            assert evaluate(np.array([start, start + 1], dtype=np.int64), *values).tolist() == [
                10.25,
                20.75,
            ]
            assert np.isnan(evaluate(outside, *values))
    # The mathematical members remain distinct outside signed 64-bit
    # arithmetic; a compiled expression outside that profile must raise
    # before a wrapped result can be mistaken for an ordinary integer key.
    for expression, safe_parameter, safe_key, parameter, wrapped in (
        ("θ+1", 1, 2, 2**63 - 1, -(2**63)),
        ("θ-1", 2, 1, -(2**63), 2**63 - 1),
        ("-θ", 1, -1, -(2**63), -(2**63)),
        ("θ*2", 2, 4, 2**62, -(2**63)),
        ("θ^2", 2, 4, 2**32, 0),
    ):
        arithmetic = stage_from_text(
            POINTS.replace("θ   : ℝ₊", "θ   : ℤ").replace(
                "{0, θ} ⊂ ℤ", f"{{{expression}, 0}} ⊂ ℤ"
            ),
            "index-arithmetic.bl",
        )
        safe = copy_native(arithmetic).calibrate(
            {"θ": safe_parameter, "β": 0.9, "q": [20.75, 10.25]}
        )
        outside_profile = copy_native(arithmetic).calibrate(
            {"θ": parameter, "β": 0.9, "q": [20.75, 10.25]}
        )
        function = pushforward(arithmetic).compile_kernel()
        safe_values = pushforward(safe).kernel().parameter_values
        invalid_values = pushforward(outside_profile).kernel().parameter_values
        for evaluate in (function, numba.njit(function)):
            assert float(evaluate(safe_key, *safe_values)) == 20.75
            for key in {wrapped, 0}:
                with pytest.raises(ValueError):
                    evaluate(key, *invalid_values)
    # the binder of the policy, `jp : L_J`, lies in the index set by its name,
    # and an inclusion the terms do not decide is decided at calibration
    assert all(item.condition != "set-inclusion" for item in symbolic.obligations())
    listed = stage_from_text(POINTS.replace("(s : S_θ)", "(s : {0, 2} ⊂ ℤ)"), "points.bl")
    included = copy_native(listed).calibrate({"θ": 2, "β": 0.9, "q": [10.0, 20.0]})
    inclusions = [item for item in included.obligations() if item.condition == "set-inclusion"]
    assert [item.status for item in inclusions] == ["established"]
    with pytest.raises(ValueError, match="⊆"):
        copy_native(listed).calibrate({"θ": 1, "β": 0.9, "q": [10.0, 20.0]})
    # a set of functions on no finite index set, a literal bound that is no
    # integer and an infinite member are refused; a listed set with the set
    # its members lie in stands before the arrow
    with pytest.raises(ConstructionError, match="no finite index set") as scalar_domain:
        stage_from_text(LOCATION.replace("δ   : L_J → ℝ", "δ   : ℝ → ℝ"), "location.bl")
    assert scalar_domain.value.rule == "readable-form"
    with pytest.raises(ConstructionError, match="2.5") as fractional_bound:
        stage_from_text(LOCATION.replace("L_J := {1, …, J}", "L_J := {1, …, 2.5}"), "location.bl")
    assert fractional_bound.value.rule == "readable-form"
    # Undefined, non-real and infinite arithmetic cannot name a bound or a
    # numerical member, even when the expression reads no parameter.
    for expression in ("1/0", "0/0", "(-1)^0.5", "10.0^1000"):
        texts = (
            POINTS.replace("{0, θ} ⊂ ℤ", f"{{0, {expression}}} ⊂ ℝ"),
            LOCATION.replace("L_J := {1, …, J}", f"L_J := {{1, …, {expression}}}"),
            LOCATION.replace("L_J := {1, …, J}", f"L_J := {{{expression}, …, J}}"),
        )
        for text in texts:
            with pytest.raises(ConstructionError) as invalid_constant:
                stage_from_text(text, "invalid-index.bl")
            assert invalid_constant.value.rule == "readable-form"
            assert invalid_constant.value.address is not None
            assert expression in invalid_constant.value.message
    # Closed noninteger members are refused both as a named set and where
    # the source writes an index domain or a selector's declared set.
    for member in ("1/3", "2.5"):
        texts = (
            POINTS.replace("{0, θ} ⊂ ℤ", f"{{0, {member}}} ⊂ ℤ"),
            POINTS.replace("q   : S_θ → ℝ₊", f"q   : {{0, {member}}} ⊂ ℝ → ℝ₊"),
            POINTS.replace("(s : S_θ)", f"(s : {{0, {member}}} ⊂ ℝ)"),
        )
        for text in texts:
            with pytest.raises(ConstructionError) as noninteger:
                stage_from_text(text, "noninteger-index.bl")
            assert noninteger.value.rule == "readable-form"
            assert noninteger.value.address is not None
            assert member in noninteger.value.message
    # Parameter-defined integer members are checked in function and
    # correspondence parameter sets as well as in a named stage set.
    for declaration in (
        "f(i : {0, κ} ⊂ ℝ) := i",
        "Λ(i : {0, κ} ⊂ ℝ) := [0, i]",
    ):
        text = POINTS.replace("β   : (0,1)", "κ : ℝ₊\n" + declaration + "\nβ   : (0,1)")
        function_domain = stage_from_text(text, "function-domain.bl")
        values = {"θ": 2, "κ": 2, "β": 0.9, "q": [10.25, 20.75]}
        assert copy_native(function_domain).calibrate(values).par["κ"].value == 2
        with pytest.raises(ValueError, match="κ"):
            copy_native(function_domain).calibrate({**values, "κ": 2.5})
    # The integer-valued expression is valid symbolically, but compilation
    # refuses unsupported parameter-dependent division rather than rounding.
    divided = stage_from_text(
        POINTS.replace("{0, θ} ⊂ ℤ", "{0, θ/2 + θ/2} ⊂ ℤ"), "divided-index.bl"
    )
    with pytest.raises(ConstructionError) as division:
        pushforward(divided).compile_kernel()
    assert division.value.rule == "kernel-form"
    reciprocal = stage_from_text(POINTS.replace("{0, θ} ⊂ ℤ", "{0, 1/θ} ⊂ ℤ"), "points.bl")
    assert reciprocal.bindings.calibration is None
    assert copy_native(reciprocal).calibrate({"θ": 1, "β": 0.9, "q": [10.25, 20.75]}).par[
        "q"
    ].value == (
        10.25,
        20.75,
    )
    for member in (2, 0):
        with pytest.raises(ValueError, match="1/θ"):
            copy_native(reciprocal).calibrate({"θ": member, "β": 0.9, "q": [10.25, 20.75]})
    inline = stage_from_text(
        POINTS.replace("q   : S_θ → ℝ₊", "q   : {0, θ} ⊂ ℤ → ℝ₊"), "points.bl"
    )
    assert copy_native(inline).calibrate({"θ": 2, "β": 0.9, "q": [10.25, 20.75]}).par[
        "q"
    ].value == (
        10.25,
        20.75,
    )
    with pytest.raises(ConstructionError, match="ℝ₊") as unbounded_key:
        stage_from_text(POINTS.replace("(s : S_θ)", "(s : ℝ₊)"), "points.bl")
    assert unbounded_key.value.rule == "family-selection"
    with pytest.raises(ConstructionError, match="{a, b}") as labelled_key:
        stage_from_text(POINTS.replace("(s : S_θ)", "(s : {a, b})"), "points.bl")
    assert labelled_key.value.rule == "family-selection"
    # a bound or a member is a number or arithmetic of declared parameters
    with pytest.raises(ConstructionError, match="g\\(J\\)") as applied_bound:
        stage_from_text(
            LOCATION.replace("L_J := {1, …, J}", "g(x : ℕ) := x + 1\nL_J := {1, …, g(J)}"),
            "location.bl",
        )
    assert applied_bound.value.rule == "readable-form"
    with pytest.raises(ConstructionError, match="'b'") as undeclared_member:
        stage_from_text(POINTS.replace("{0, θ} ⊂ ℤ", "{θ, b} ⊂ ℝ"), "points.bl")
    assert undeclared_member.value.rule == "name-in-scope"
    with pytest.raises(ValueError) as mapping_key:
        stage_from_text(POINTS, "points.bl").calibrate(
            {"θ": 2, "β": 0.9, "q": {0: 10.25, 2.5: 20.75}}
        )
    assert "q" in str(mapping_key.value) and "key" in str(mapping_key.value)
    named_carrier = stage_from_text(
        POINTS.replace("θ   : ℝ₊", "θ   : ℝ").replace(
            "S_θ := {0, θ} ⊂ ℤ", "A := ℝ₊\nS_θ := {0, θ} ⊂ A"
        ),
        "points.bl",
    )
    with pytest.raises(ValueError, match="θ ∈ A"):
        copy_native(named_carrier).calibrate({"θ": -1.0, "β": 0.9, "q": [10.0, 20.0]})
    extended = stage_from_text(POINTS.replace("θ   : ℝ₊", "θ   : ℝ̄"), "points.bl")
    with pytest.raises(ValueError, match="inf"):
        copy_native(extended).calibrate({"θ": float("inf"), "β": 0.9, "q": [10.0, 20.0]})


def test_item_5_labels_and_positions_keep_their_meaning_and_a_fractional_position_is_refused(
    text_of, elaborate_text
):
    """Label selection, product positions, and their refusals remain distinct.

    Benhabib's ten-label wage vector retains its supplied values and refuses
    a short vector. Algan–Ragot's named transition rows must sum to one.
    Product selection uses a whole-number position and refuses `x[2.5]`.
    Complete Benhabib encoding equality is checked by the corpus recording.
    """
    source = (
        ROOT / "applications/benhabib-2019/declaration/stages/benhabib_bellman/benhabib_bellman.bl"
    )
    benhabib = elaborate_text(
        source.read_text(encoding="utf-8"),
        "applications/benhabib-2019/declaration/stages/benhabib_bellman/benhabib_bellman.bl",
    )
    law = pushforward(benhabib, "dcsn_to_cntn")
    assert "np.asarray(tau) == 'q1'" in law.kernel().python
    # a fixed product is read one entry per factor: a wage vector of two
    # entries for ten factors is refused, an intended change
    values = {
        "β": 0.96,
        "σ": 2.0,
        "μ": 0.0,
        "A": 1.0,
        "tau": "q1",
        "r_type": "r1",
        "R_vec": [1.0, 1.02, 1.04, 1.06, 1.08],
        "wage_fn": [9.760, 19.95, 26.85, 33.05, 39.02, 45.05, 51.40, 59.16, 70.33, 100.3],
    }
    assert benhabib.calibrate(values).par["wage_fn"].value[9] == 100.3
    with pytest.raises(ValueError) as short:
        benhabib.calibrate({**values, "wage_fn": [9.760, 19.95]})
    assert "wage_fn" in str(short.value) and "10" in str(short.value)
    returns = (ROOT / "packages/bellman/tests/corpus/AlganRagotMoney/returns.bl").read_text(
        encoding="utf-8"
    )
    algan = elaborate_text(returns, "packages/bellman/tests/corpus/AlganRagotMoney/returns.bl")
    assert any("each row of" in item.explanation for item in algan.obligations())
    # a named row that does not sum to one is refused at calibration, an
    # intended change: the base commit admitted it
    with pytest.raises(ConstructionError, match="sums to 1.6") as row:
        algan.calibrate(
            {
                "r": 0.02,
                "Π": 1.02,
                "Q_h": [0.8, 0.6, 0.2],
                "Q_m": [0.1, 0.8, 0.1],
                "Q_l": [0.05, 0.15, 0.8],
            }
        )
    assert row.value.rule == "distribution-domain"

    pair = """@stage: pair
x : ℝ × ℝ
[id=arvl_to_dcsn, (a : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = a + x[2]
}
"""
    second = elaborate_text(pair, "pair.bl").calibrate({"x": [1.0, 5.0]})
    law = pushforward(second)
    assert float(law.compile_kernel()(1.0, *law.kernel().parameter_values)) == 6.0
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(pair.replace("x[2]", "x[2.5]"), "pair.bl")
    assert refused.value.rule == "syntax" and "2.5" in refused.value.message


# A stage whose law of motion selects a component of a pair by a label, the
# draw of a shock on a declared set of two labels: the resources are
#     m = R·k + θ  where j = emp,   m = R·k + ξ_u  where j = unemp.
LABELLED = """@stage: labelled
Emp := {emp, unemp}
R   : ℝ₊₊
ξ_u : ℝ₊
p   : [0,1)
θ : ℝ₊₊
θ ~ LogNormal(0, 1)
j : Emp
j ~ Bernoulli(p)

[id=arvl_to_dcsn, (k : ℝ₊, θ, j) : !arvl -> (m : ℝ₊₊) : !dcsn] {
    m = R*k + (θ, ξ_u)[j]    :: [id=resources]
}
"""


class _Unconverted:
    """A value NumPy cannot convert and arithmetic carries, as a value that
    JAX is tracing is: it holds a number, `np.asarray` of it raises
    `TypeError`, and its sum with a number is another such value."""

    __array_ufunc__ = None

    def __init__(self, held):
        self.held = held

    def __array__(self, dtype=None, copy=None):
        raise TypeError("this value has no array")

    def __add__(self, other):
        return _Unconverted(self.held + getattr(other, "held", other))

    __radd__ = __add__


def test_a_selection_by_one_label_is_made_where_numpy_refuses_an_operand():
    """The law of motion of `LABELLED` selects by the label `j`, and its text
    writes each label through the inner function `where_label`. Every operand
    NumPy takes gives what `np.where` gives: with R = 1.02 and ξ_u = 0.3,
    m(1, 0.9, emp) = 1.02 + 0.9 = 1.92 and m(1, 0.9, unemp) = 1.02 + 0.3 =
    1.32; a label of neither name gives no value; a component not selected
    still gives the result its shape, so three values of θ at the label
    `unemp` give three resources of 1.32; and an array of labels selects at
    each point, (1.02 + 0.8, 2.04 + 0.3) = (1.82, 2.34). Where an operand is
    a value NumPy cannot convert and the key is one label, the component the
    label selects is returned as it is, so the kernel carries such a value
    through, as it carries a value JAX is tracing; with an array of labels
    NumPy's refusal stands."""
    stage = stage_from_text(LABELLED, "labelled.bl").calibrate({"R": 1.02, "ξ_u": 0.3, "p": 0.05})
    law = pushforward(stage)
    record = law.kernel()
    written = (
        "where_label(np.asarray(j) == 'emp', θ, "
        "where_label(np.asarray(j) == 'unemp', ξ_u, np.nan))"
    )
    assert written in record.python
    function, values = law.compile_kernel(), record.parameter_values
    assert values == (1.02, 0.3)
    assert float(function(1.0, 0.9, "emp", *values)) == pytest.approx(1.92)
    assert float(function(1.0, 0.9, "unemp", *values)) == pytest.approx(1.32)
    assert np.isnan(function(1.0, 0.9, "neither", *values))
    unemployed = function(1.0, np.array([0.8, 1.0, 1.2]), "unemp", *values)
    assert isinstance(unemployed, np.ndarray) and unemployed.shape == (3,)
    np.testing.assert_allclose(unemployed, 1.32)
    np.testing.assert_allclose(
        function(np.array([1.0, 2.0]), np.array([0.8, 1.2]), np.array(["emp", "unemp"]), *values),
        [1.82, 2.34],
    )
    # a value NumPy cannot convert: with one label the selected component is
    # returned as it is, the employed draw itself and the unemployed income
    carried = function(1.0, _Unconverted(0.9), "emp", *values)
    assert isinstance(carried, _Unconverted) and carried.held == pytest.approx(1.92)
    assert float(function(1.0, _Unconverted(0.9), "unemp", *values)) == pytest.approx(1.32)
    assert np.isnan(function(1.0, _Unconverted(0.9), "neither", *values))
    with pytest.raises(TypeError, match="no array"):
        function(1.0, _Unconverted(0.9), np.array(["emp", "unemp"]), *values)
    # a selection by an integer key is written with `np.where` as before, so
    # that Numba compiles it
    points = stage_from_text(POINTS, "points.bl")
    assert "where_label" not in pushforward(points).kernel().python


def test_a_kernel_that_selects_by_a_fixed_label_is_traced_by_jax():
    """With JAX installed, which the package does not require, the law of
    motion of `LABELLED` is traced with the label fixed: mapped over three
    values of θ it gives NumPy's numbers at either label, it compiles, and
    its derivative in θ is one where the label selects θ and zero where it
    selects ξ_u. Without JAX the test is skipped."""
    jax = pytest.importorskip("jax")
    stage = stage_from_text(LABELLED, "labelled.bl").calibrate({"R": 1.02, "ξ_u": 0.3, "p": 0.05})
    law = pushforward(stage)
    function, values = law.compile_kernel(), law.kernel().parameter_values
    draws = np.array([0.8, 1.0, 1.2])
    for label in ("emp", "unemp"):
        np.testing.assert_allclose(
            jax.vmap(lambda draw, label=label: function(1.0, draw, label, *values))(draws),
            function(1.0, draws, label, *values),
            rtol=1e-6,
        )
    compiled = jax.jit(lambda k, draw: function(k, draw, "emp", *values))
    assert float(compiled(1.0, 0.9)) == pytest.approx(1.92)
    assert float(jax.grad(lambda draw: function(1.0, draw, "emp", *values))(0.9)) == 1.0
    assert float(jax.grad(lambda draw: function(1.0, draw, "unemp", *values))(0.9)) == 0.0
