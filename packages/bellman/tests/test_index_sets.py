"""Finite index sets: the integer ranges and the listed sets of integers that
a stage declares, how the stage prints them, the collections and the shocks
on them, the calibration of those collections and its refusals, and the
connections of a collection on a listed set between periods. The kernels
that select an entry by a key or by a label are tested in
test_kernels_on_index_sets.py."""

import json
import re
from fractions import Fraction

import numpy as np
import pytest
from application_files import COPIED_FILES_FOLDER
from stage_builders import stage_from_file, stage_from_text
from stage_graphs import aggregation_box, pushforward_box
from stage_texts import (
    ADJACENT_CALIBRATION,
    ADJACENT_MEMBERS_TEXT,
    CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW,
    CHAIN_TEXT,
    LOCATION_CALIBRATION_J2,
    LOCATION_CALIBRATION_J3,
    LOCATION_TEXT,
    POINTS_TEXT,
    points_calibration,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.trellis import calibrate_trellis, connection_report, elaborate_trellis

# The location stage whose state also takes the outside option 0,
# I_J = {0, …, J}, while the distance is declared on pairs of city locations
# alone: the selection `dist[j][i_d]` reads the table at a key that its
# declaration does not admit, unless a condition establishes that both
# locations are in the city.
LOCATION_WITH_OUTSIDE_OPTION = LOCATION_TEXT.replace(
    "L_J := {1, …, J}\n", "I_J := {0, …, J}\nL_J := {1, …, J}\n"
).replace("(i : L_J) : !arvl -> (i_d : L_J) : !dcsn", "(i : I_J) : !arvl -> (i_d : I_J) : !dcsn")


# five calibrations of the location stage that a calibration refuses: two
# entries of δ at J = 3, a surplus key 3 of the distance table at J = 2, a
# negative distance, a bound J that is no integer, and the empty range at
# J = 0
MISSING_ENTRY = {**LOCATION_CALIBRATION_J3, "δ": [1.0, 2.0]}
SURPLUS_KEY = {
    **LOCATION_CALIBRATION_J2,
    "dist": {1: {1: 0.0, 2: 1.5}, 2: {1: 1.5, 2: 0.0}, 3: {1: 4.0}},
}
NEGATIVE_DISTANCE = {**LOCATION_CALIBRATION_J2, "dist": [[0.0, -1.5], [1.5, 0.0]]}
FRACTIONAL_BOUND = {**LOCATION_CALIBRATION_J2, "J": 2.5}
EMPTY_RANGE = {**LOCATION_CALIBRATION_J2, "J": 0, "δ": [], "dist": []}


# the points stage whose listed set lies in a named set A = ℝ₊, θ being
# declared real
NAMED_CARRIER = POINTS_TEXT.replace("θ   : ℝ₊", "θ   : ℝ").replace(
    "S_θ := {0, θ} ⊂ ℤ", "A := ℝ₊\nS_θ := {0, θ} ⊂ A"
)


# the points stage whose θ is declared on the extended reals ℝ̄
EXTENDED = POINTS_TEXT.replace("θ   : ℝ₊", "θ   : ℝ̄")


# The points stage that also passes the collection q from the continuation
# perch to the arrival perch of the next period, as the field v, which the
# arrival builder reads in place of q; and the same stage with its two
# members listed in the other order.
POINTS_PASSING_Q = POINTS_TEXT.replace(
    "(w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = w - c",
    "(w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊, v : S_θ → ℝ₊) : !cntn] {\n"
    "    v = q    :: [id=keep]\n    a = w - c",
).replace(
    "(s : S_θ) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = q[s]",
    "(s : S_θ, v : S_θ → ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = v[s]",
)
POINTS_PASSING_Q_REORDERED = POINTS_PASSING_Q.replace("S_θ := {0, θ} ⊂ ℤ", "S_θ := {θ, 0} ⊂ ℤ")


# the calibration of the chain at J = 1 (two states), with a stochastic matrix
# and a correlated covariance; `CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW` is
# the calibration at J = 2
CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW = {
    "J": 1,
    "β": 0.9,
    "Π": [[0.9, 0.1], [0.2, 0.8]],
    "μ_ε": [0.0, 1.0],
    "Σ_ε": [[1.0, 0.5], [0.5, 2.0]],
}


# the stage of the returns in the corpus copy of the application
# AlganRagotMoney, whose transition matrix is written as three rows, each a
# parameter of its own
RETURNS = f"{COPIED_FILES_FOLDER}/AlganRagotMoney/returns.bl"


def printed_rows(table):
    """The rows of a printed table by the text of their first cell, each the
    list of its cells, which the printing separates by two spaces or more."""
    rows = (re.split(r" {2,}", line.strip()) for line in str(table).splitlines())
    return {cells[0]: cells for cells in rows}


def stage_record(text, theta):
    """The record of a points stage text, calibrated at θ = `theta` with
    β = 0.9 and the entries 10 and 20 of q."""
    return {
        "stage": {"text": text, "origin": "points.bl"},
        "methods": {},
        "settings": {},
        "calibration": {"θ": theta, "β": 0.9, "q": [10.0, 20.0]},
    }


def connection_compatibility(later, earlier):
    """The compatibility and its reason of the connection from the field v of
    the stage record `later`, in the second period, to the field v of the
    stage record `earlier`, in the first, in a calibrated trellis."""
    syntactic = {
        "periods": [
            {"stages": {"A": earlier}, "connectors": []},
            {"stages": {"B": later}, "connectors": []},
        ],
        "inter_connectors": [{"B.v": "v"}],
    }
    trellis = calibrate_trellis(elaborate_trellis(syntactic), syntactic)
    (pair,) = [p for p in connection_report(trellis).pairs if str(p.reading) == "periods[0].A.v"]
    return pair.compatibility, pair.reason


@pytest.fixture(scope="module")
def points_stage(read_only_stage_from_text):
    """The symbolic points stage, read from `read_only_stage_from_text`."""
    return read_only_stage_from_text(POINTS_TEXT)


@pytest.fixture(scope="module")
def chain_stage(read_only_stage_from_text):
    """The symbolic chain stage, read from `read_only_stage_from_text`."""
    return read_only_stage_from_text(CHAIN_TEXT)


@pytest.fixture(scope="module")
def returns_stage():
    """The symbolic stage of the returns of the corpus copy of the
    application AlganRagotMoney, which the tests read and do not bind."""
    return stage_from_file(RETURNS)


@pytest.mark.parametrize(
    ("stage", "name", "domain"),
    [
        pytest.param("location_stage", "δ", "L_J → ℝ", id="a collection on a range"),
        pytest.param(
            "location_stage", "dist", "L_J × L_J → ℝ₊", id="a table on the pairs of a range"
        ),
        pytest.param("points_stage", "q", "S_θ → ℝ₊", id="a collection on a listed set"),
    ],
)
def test_the_parameter_table_prints_each_collection_on_the_functions_from_its_index_set(
    request, stage, name, domain
):
    """The parameter table of a symbolic stage prints as the set of a
    collection the functions from its index set to the set of its entries."""
    printed = printed_rows(request.getfixturevalue(stage).par)
    assert printed[name][1] == domain


@pytest.mark.parametrize(
    ("stage", "field", "values"),
    [
        pytest.param("location_stage", "location:arvl:i", "in L_J", id="a state on a range"),
        pytest.param("location_stage", "location:dcsn:j", "in L_J", id="a control on a range"),
        pytest.param(
            "chain_stage", "chain:shck:ε", "in I_J → ℝ", id="a shock of a component per key"
        ),
    ],
)
def test_the_field_table_prints_the_index_set_that_a_field_lies_in(request, stage, field, values):
    """The field table of a symbolic stage prints a field declared on an
    index set, or on the functions from one, as lying in that set."""
    printed = printed_rows(request.getfixturevalue(stage).fields())
    assert printed[field][-1] == values


@pytest.mark.parametrize(
    ("stage", "definition"),
    [
        pytest.param("location_stage", "L_J := {1, …, J}", id="a range"),
        pytest.param("points_stage", "S_θ := {0, θ} ⊂ ℤ", id="a listed set"),
    ],
)
def test_the_view_of_a_stage_prints_the_definition_of_its_index_set(request, stage, definition):
    """The view of a symbolic stage prints the definition of an index set as
    the stage file writes it."""
    assert definition in str(request.getfixturevalue(stage).view())


def test_two_calibrated_copies_of_one_stage_hold_their_own_values_of_j(location_stage):
    """Two copies of the symbolic location stage, calibrated at J = 2 and at
    J = 3, each hold the value of J of their own calibration."""
    at_2 = copy_native(location_stage).calibrate(LOCATION_CALIBRATION_J2)
    at_3 = copy_native(location_stage).calibrate(LOCATION_CALIBRATION_J3)
    assert at_2.par["J"].value == 2 and at_3.par["J"].value == 3


@pytest.mark.parametrize(
    ("stage", "calibration", "name", "rows"),
    [
        pytest.param(
            "location_stage",
            LOCATION_CALIBRATION_J2,
            "dist",
            ((0.0, 1.5), (1.5, 0.0)),
            id="a distance table at J = 2",
        ),
        pytest.param(
            "chain_stage",
            CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW,
            "Π",
            ((0.9, 0.1), (0.2, 0.8)),
            id="a transition matrix at J = 1",
        ),
        pytest.param(
            "chain_stage",
            CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW,
            "Σ_ε",
            ((1.0, 0.5, 0.0), (0.5, 2.0, 0.5), (0.0, 0.5, 3.0)),
            id="a covariance at J = 2",
        ),
    ],
)
def test_a_calibrated_table_on_pairs_of_keys_holds_one_row_for_each_key(
    request, stage, calibration, name, rows
):
    """A calibrated table on the pairs of keys of an index set holds one
    tuple of entries for each key, as many as the calibration gives the
    index set."""
    version = copy_native(request.getfixturevalue(stage)).calibrate(calibration)
    assert version.par[name].value == rows


def test_calibrating_copies_of_a_symbolic_stage_leaves_it_unbound():
    """After two copies of the location stage are calibrated, the symbolic
    stage still prints J as unbound and holds none of the established
    conditions of a calibrated copy."""
    symbolic = stage_from_text(LOCATION_TEXT, "location.bl")
    at_2 = copy_native(symbolic).calibrate(LOCATION_CALIBRATION_J2)
    copy_native(symbolic).calibrate(LOCATION_CALIBRATION_J3)
    # a calibration establishes conditions, such as the integer bounds of L_J
    assert any(item.status == "established" for item in at_2.obligations())
    assert str(symbolic.par["J"]) == "J : ℕ, unbound"
    # the comparison leaves out the condition range-compatibility, that the
    # set of the binder jp lies in the declared set of the control j
    established = [
        item.condition
        for item in symbolic.obligations()
        if item.status == "established" and item.condition != "range-compatibility"
    ]
    assert established == []


def test_the_encoding_of_a_stage_with_index_sets_validates_against_the_schema(
    location_stage, encoding_validator
):
    """The encoding of the symbolic location stage validates against the
    schema of the encoding: the validator raises where it does not."""
    encoding_validator.validate(json.loads(json.dumps(location_stage.encoding())))


def test_the_term_of_a_stage_with_index_sets_is_read_back_from_its_json():
    """The term that the parser makes of the text of the location stage,
    written as JSON and read back, is the same term."""
    term, _ = parse_with_spans(LOCATION_TEXT, "location.bl")
    assert from_json(json.loads(json.dumps(to_json(term)))) == term


def test_a_mapping_from_keys_to_entries_is_held_in_the_order_of_the_members(points_stage):
    """A calibration of q by the mapping {5: 20.75, 0: 10.25} holds the
    entries in the order of the members 0 and θ = 5, so that the key 5
    selects 20.75."""
    function = pushforward_box(points_stage).compile_kernel()
    mapped = copy_native(points_stage).calibrate({"θ": 5, "β": 0.9, "q": {5: 20.75, 0: 10.25}})
    values = pushforward_box(mapped).kernel().parameter_values
    assert mapped.par["q"].value == (10.25, 20.75)
    assert (float(function(5, *values)), float(function(0, *values))) == (20.75, 10.25)


def test_two_orders_of_one_mapping_from_keys_beyond_double_precision_give_one_calibration(
    read_only_stage_from_text,
):
    """A mapping from the keys 2**53 + 1 and 2**53, which are equal as
    doubles, gives in either order the entries in the order of the members
    and the same recorded source of the calibration."""
    exact = read_only_stage_from_text(ADJACENT_MEMBERS_TEXT)
    values = ADJACENT_CALIBRATION
    first = copy_native(exact).calibrate(values)
    second = copy_native(exact).calibrate(
        {**values, "q": dict(reversed(tuple(values["q"].items())))}
    )
    assert first.par["q"].value == second.par["q"].value == (20.75, 10.25)
    # the source of a calibrated version is that of its calibration
    assert first.provenance["source"]["sha256"] == second.provenance["source"]["sha256"]


def test_a_repeated_member_is_refused_where_equal_entries_of_distinct_members_are_accepted(
    points_stage,
):
    """Equal entries of q at the distinct members 0 and 5 are accepted, and
    θ = 0, which repeats the member 0, is refused with a message that names
    the set S_θ and gives the value θ = 0 and the condition that 0 and θ
    differ."""
    function = pushforward_box(points_stage).compile_kernel()
    equal_entries = copy_native(points_stage).calibrate({"θ": 5, "β": 0.9, "q": [0.375, 0.375]})
    values = pushforward_box(equal_entries).kernel().parameter_values
    assert function(np.array([0, 5]), *values).tolist() == [0.375, 0.375]
    with pytest.raises(ValueError) as duplicate:
        copy_native(points_stage).calibrate({"θ": 0, "β": 0.9, "q": [10.25, 20.75]})
    phrases = ("points:set:S_θ", "calibration θ = 0", "¬(0 = θ)")
    assert [phrase for phrase in phrases if phrase not in str(duplicate.value)] == []


# each row: a stage text, a calibration whose value of θ the package refuses,
# and the phrases of the refusal; a member of a listed set must be an integer
# of the set that the listed set names, ℤ or A, and the check of the declared
# set ℝ₊ of θ refuses a value given as an exact fraction, Fraction(1, 3)
@pytest.mark.parametrize(
    ("text", "calibration", "phrases"),
    [
        pytest.param(
            POINTS_TEXT,
            points_calibration(2.5),
            ("calibration θ = 2.5", "θ ∈ ℤ"),
            id="a member that is no integer",
        ),
        pytest.param(
            POINTS_TEXT,
            points_calibration(Fraction(1, 3)),
            ("parameter 'θ'", "the value Fraction(1, 3) lies outside the declared set ℝ₊"),
            id="an exact fraction, which the check of the declared set refuses",
        ),
        pytest.param(
            NAMED_CARRIER,
            points_calibration(-1.0, (10.0, 20.0)),
            ("calibration θ = -1.0", "θ ∈ A"),
            id="a member outside the named set",
        ),
        pytest.param(
            EXTENDED,
            points_calibration(float("inf"), (10.0, 20.0)),
            ("calibration θ = inf", "θ ∈ ℤ"),
            id="an infinite member",
        ),
    ],
)
def test_a_refused_value_of_theta_is_named_with_the_condition_or_the_set_that_refuses_it(
    read_only_stage_from_text, text, calibration, phrases
):
    """A calibration whose θ makes the member θ of {0, θ} no integer of the
    set that the listed set names, or whose θ the check of the declared set
    of θ refuses, as it refuses an exact fraction, is refused with a message
    that gives the value of θ and the condition or the set that refuses it."""
    with pytest.raises(ValueError) as refusal:
        copy_native(read_only_stage_from_text(text)).calibrate(calibration)
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


@pytest.mark.parametrize(
    "refused",
    [
        pytest.param(2.5, id="theta 2.5"),
        pytest.param(Fraction(1, 3), id="theta one third"),
        pytest.param(0, id="theta 0, a repeated member"),
    ],
)
def test_a_refused_calibration_of_a_copy_leaves_the_other_points_versions_as_they_were(refused):
    """After the calibration of a third copy of the points stage is refused,
    the copies calibrated at θ = 2 and θ = 5 keep their values of θ and the
    symbolic stage stays unbound."""
    symbolic = stage_from_text(POINTS_TEXT, "points.bl")
    versions = [copy_native(symbolic).calibrate(points_calibration(member)) for member in (2, 5)]
    with pytest.raises(ValueError):
        copy_native(symbolic).calibrate(points_calibration(refused))
    assert [version.par["θ"].value for version in versions] == [2, 5]
    assert symbolic.bindings.calibration is None


@pytest.mark.parametrize(
    ("stage", "phrase"),
    [
        pytest.param("chain_stage", "each row of Π", id="a matrix on the pairs of a range"),
        pytest.param(
            "returns_stage", "each row of (Q_h, Q_m, Q_l)", id="a matrix written as three rows"
        ),
    ],
)
def test_a_symbolic_stage_keeps_the_condition_that_each_row_of_its_transition_matrix_sums_to_one(
    request, stage, phrase
):
    """The symbolic stage of a categorical shock drawn from a row of a
    transition matrix keeps, until calibration, the condition that each row
    is a probability vector."""
    obligations = request.getfixturevalue(stage).obligations()
    assert any(phrase in item.explanation for item in obligations)


@pytest.mark.parametrize(
    ("stage", "calibration", "phrases"),
    [
        pytest.param(
            "location_stage",
            MISSING_ENTRY,
            ("parameter 'δ'", "has 2 entries", "has 3 members"),
            id="two entries of a collection at J = 3",
        ),
        pytest.param(
            "chain_stage",
            {
                **CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW,
                "Π": CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW["Π"],
            },
            ("parameter 'Π'", "has 2 entries", "has 3 members"),
            id="two rows of a table at J = 2",
        ),
    ],
)
def test_a_collection_with_a_wrong_count_of_entries_is_refused_naming_it_and_the_count(
    request, stage, calibration, phrases
):
    """A calibration that gives a collection fewer entries than its index
    set has members is refused with a message that names the collection and
    gives both counts."""
    with pytest.raises(ValueError) as refusal:
        copy_native(request.getfixturevalue(stage)).calibrate(calibration)
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


def test_the_parameters_of_a_shock_law_of_the_size_of_a_smaller_index_set_are_refused(chain_stage):
    """At J = 2 a calibration that gives μ_ε and Σ_ε their values of J = 1
    is refused with a message that names one of the two."""
    with pytest.raises(ValueError) as old_size:
        copy_native(chain_stage).calibrate(
            {
                **CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW,
                "Σ_ε": CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW["Σ_ε"],
                "μ_ε": CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW["μ_ε"],
            }
        )
    message = str(old_size.value)
    assert "parameter 'Σ_ε'" in message or "parameter 'μ_ε'" in message


def test_a_covariance_that_is_not_symmetric_is_refused(chain_stage):
    """A calibrated covariance of the normal law of ε that is not symmetric
    is refused under `distribution-domain`, with a message that gives the two
    entries that differ."""
    with pytest.raises(ConstructionError) as asymmetric:
        copy_native(chain_stage).calibrate(
            {**CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW, "Σ_ε": [[1.0, 0.5], [0.4, 2.0]]}
        )
    phrase = "is not symmetric: entry (1, 2) is 0.5 and entry (2, 1) is 0.4"
    assert asymmetric.value.rule == "distribution-domain" and phrase in str(asymmetric.value)


def test_numbers_do_not_supply_the_normal_law_of_a_shock_with_a_component_per_key():
    """Where μ_ε and Σ_ε are declared as numbers, the calibration at J = 1,
    where ε has two components, is refused under `distribution-domain` with
    a message that names both parameters in their roles and with an
    address."""
    scalar_law = stage_from_text(
        CHAIN_TEXT.replace("μ_ε : I_J → ℝ", "μ_ε : ℝ").replace("Σ_ε : I_J × I_J → ℝ", "Σ_ε : ℝ"),
        "chain.bl",
    )
    with pytest.raises(ConstructionError) as scalar_parameters:
        copy_native(scalar_law).calibrate(
            {**CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW, "μ_ε": 0.0, "Σ_ε": 1.0}
        )
    assert scalar_parameters.value.rule == "distribution-domain"
    message = scalar_parameters.value.message
    assert "μ_ε as its mean vector" in message and "Σ_ε as its covariance matrix" in message
    assert scalar_parameters.value.address is not None


@pytest.mark.parametrize(
    ("text", "phrase"),
    [
        pytest.param(
            CHAIN_TEXT.replace("ε   ~ N(μ_ε, Σ_ε)", "ε   ~ N((0, 1), ((1, 0.5), (0.5, 2)))"),
            "ε has 3 components",
            id="a normal law",
        ),
        pytest.param(
            CHAIN_TEXT.replace("e_n ~ Categorical(Π[e_c])", "e_n ~ Categorical((0.5, 0.5))"),
            "2 weights",
            id="a categorical law",
        ),
    ],
)
def test_a_law_written_for_two_members_is_accepted_at_two_and_refused_at_three(text, phrase):
    """A shock law that the stage file writes out for two members of I_J is
    accepted at J = 1, where I_J has two, and refused under
    `distribution-domain` at J = 2, where it has three."""
    written = stage_from_text(text, "chain.bl")
    assert (
        copy_native(written).calibrate(CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW).par["J"].value
        == 1
    )
    with pytest.raises(ConstructionError) as refusal:
        copy_native(written).calibrate(CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW)
    assert refusal.value.rule == "distribution-domain"
    assert phrase in str(refusal.value)


@pytest.mark.parametrize(
    ("stage", "calibration", "phrases"),
    [
        pytest.param(
            "chain_stage",
            {**CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW, "Π": [[0.9, 0.2], [0.2, 0.8]]},
            ("the row at position 1 of Π", "not to one"),
            id="a matrix given as rows",
        ),
        pytest.param(
            "chain_stage",
            {
                **CHAIN_CALIBRATION_J1_WITH_JOINT_NORMAL_LAW,
                "Π": {0: {0: 0.9, 1: 0.2}, 1: {0: 0.2, 1: 0.8}},
            },
            ("sums to 1.1",),
            id="a matrix given as a mapping",
        ),
        pytest.param(
            "returns_stage",
            {
                "r": 0.02,
                "Π": 1.02,
                "Q_h": [0.8, 0.6, 0.2],
                "Q_m": [0.1, 0.8, 0.1],
                "Q_l": [0.05, 0.15, 0.8],
            },
            ("sums to 1.6",),
            id="a matrix written as three rows",
        ),
    ],
)
def test_a_row_of_a_transition_matrix_that_does_not_sum_to_one_is_refused_at_calibration(
    request, stage, calibration, phrases
):
    """A row of a transition matrix whose entries do not sum to one is
    refused at calibration under `distribution-domain`, with a message that
    names the matrix or gives the sum."""
    with pytest.raises(ConstructionError) as row:
        copy_native(request.getfixturevalue(stage)).calibrate(calibration)
    assert row.value.rule == "distribution-domain"
    assert [phrase for phrase in phrases if phrase not in str(row.value)] == []


@pytest.mark.parametrize(
    ("later", "earlier", "expected", "phrases"),
    [
        pytest.param(
            (POINTS_PASSING_Q, 2),
            (POINTS_PASSING_Q, 2),
            "compatible",
            (),
            id="the same members in the same order",
        ),
        pytest.param(
            (POINTS_PASSING_Q_REORDERED, 2),
            (POINTS_PASSING_Q, 2),
            "incompatible",
            ("the same members in another order",),
            id="the members in the other order",
        ),
        pytest.param(
            (POINTS_PASSING_Q, 5),
            (POINTS_PASSING_Q, 2),
            "incompatible",
            ("θ = 5 of periods[1].B", "θ = 2 of periods[0].A"),
            id="two values of theta",
        ),
        pytest.param(
            (POINTS_PASSING_Q, 2**53 + 1),
            (POINTS_PASSING_Q, 2**53),
            "incompatible",
            ("θ = 9007199254740993 of periods[1].B", "θ = 9007199254740992 of periods[0].A"),
            id="two values of theta that are equal as doubles",
        ),
    ],
)
def test_a_connection_between_periods_compares_the_members_of_a_listed_set_at_their_values(
    later, earlier, expected, phrases
):
    """A connection of a field on the listed set {0, θ} between the stages of
    two periods is compatible where the two sets have the same members in the
    same order at the values of their own calibrations, and incompatible
    where the order or the members differ, with a reason that says why."""
    status, reason = connection_compatibility(stage_record(*later), stage_record(*earlier))
    assert status == expected, reason
    assert [phrase for phrase in phrases if phrase not in reason] == []


@pytest.mark.parametrize(
    ("text", "phrases"),
    [
        pytest.param(
            LOCATION_WITH_OUTSIDE_OPTION,
            ("declared in {0, …, J}", "the index set {1, …, J}"),
            id="a key declared on a larger range",
        ),
        pytest.param(
            LOCATION_TEXT.replace("dist : L_J × L_J → ℝ₊", "dist : ℝ₊"),
            ("selects from dist, which is written as no tuple",),
            id="a selection from a number",
        ),
        pytest.param(
            LOCATION_TEXT.replace("δ[j] - m_0", "δ[1] - m_0"),
            ("the selection δ[1] selects the position 1 of δ",),
            id="a position on a collection",
        ),
        pytest.param(
            POINTS_TEXT.replace("(s : S_θ)", "(s : ℝ₊)"),
            ("declared in ℝ₊",),
            id="a key declared on an interval",
        ),
        pytest.param(
            POINTS_TEXT.replace("(s : S_θ)", "(s : {a, b})"),
            ("declared in {a, b}",),
            id="a key declared on a set of labels",
        ),
    ],
)
def test_a_selection_that_the_declaration_of_its_collection_does_not_admit_is_refused(
    text, phrases
):
    """A selection by a key whose declared set does not lie in the index set
    of the collection, a selection from a parameter that is no collection,
    and a selection by a position are refused under `family-selection`, with
    a message that names the key, the sets or the selection."""
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(text)
    assert refusal.value.rule == "family-selection"
    assert [phrase for phrase in phrases if phrase not in refusal.value.message] == []


@pytest.mark.parametrize(
    ("text", "phrase"),
    [
        pytest.param(
            LOCATION_TEXT.replace("δ   : L_J → ℝ", "δ   : ℝ → ℝ"),
            "no finite index set",
            id="a collection on an interval",
        ),
        pytest.param(
            LOCATION_TEXT.replace("L_J := {1, …, J}", "L_J := {1, …, 2.5}"),
            "has the bound 2.5, which is no integer",
            id="a bound that is no integer",
        ),
        pytest.param(
            LOCATION_TEXT.replace("L_J := {1, …, J}", "g(x : ℕ) := x + 1\nL_J := {1, …, g(J)}"),
            "reads g(J), which is no number",
            id="a bound that applies a function",
        ),
    ],
)
def test_an_index_set_in_a_form_that_the_language_does_not_admit_is_refused(text, phrase):
    """A collection on a set that is no finite index set, and a range whose
    bound is no integer or applies a function, are refused under
    `readable-form`, with a message that names the written form."""
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(text, "location.bl")
    assert refusal.value.rule == "readable-form"
    assert phrase in str(refusal.value)


@pytest.mark.parametrize(
    ("text", "expression"),
    [
        pytest.param(text, expression, id=f"{expression} as {place}")
        for expression in ("1/0", "0/0", "(-1)^0.5", "10.0^1000")
        for place, text in (
            ("a member", POINTS_TEXT.replace("{0, θ} ⊂ ℤ", f"{{0, {expression}}} ⊂ ℝ")),
            (
                "an upper bound",
                LOCATION_TEXT.replace("L_J := {1, …, J}", f"L_J := {{1, …, {expression}}}"),
            ),
            (
                "a lower bound",
                LOCATION_TEXT.replace("L_J := {1, …, J}", f"L_J := {{{expression}, …, J}}"),
            ),
        )
    ],
)
def test_undefined_non_real_or_infinite_arithmetic_in_a_bound_or_a_member_is_refused(
    text, expression
):
    """A bound of a range or a listed member written as arithmetic that is
    undefined, not real or infinite is refused under `readable-form`, with
    an address and a message that names the arithmetic, although it reads no
    parameter."""
    with pytest.raises(ConstructionError) as invalid_constant:
        stage_from_text(text, "invalid-index.bl")
    assert invalid_constant.value.rule == "readable-form"
    assert invalid_constant.value.address is not None
    assert f"{expression}, which is no finite real number" in invalid_constant.value.message


@pytest.mark.parametrize(
    ("text", "member"),
    [
        pytest.param(text, member, id=f"{member} in {place}")
        for member in ("1/3", "2.5")
        for place, text in (
            ("a named set", POINTS_TEXT.replace("{0, θ} ⊂ ℤ", f"{{0, {member}}} ⊂ ℤ")),
            (
                "the index set of a parameter",
                POINTS_TEXT.replace("q   : S_θ → ℝ₊", f"q   : {{0, {member}}} ⊂ ℝ → ℝ₊"),
            ),
            ("the set of a key", POINTS_TEXT.replace("(s : S_θ)", f"(s : {{0, {member}}} ⊂ ℝ)")),
        )
    ],
)
def test_a_written_member_that_is_no_integer_is_refused(text, member):
    """A listed member written as a number that is no integer is refused
    under `readable-form`, with an address and a message that names it, in a
    named set, in the index set of a parameter and in the set of a key."""
    with pytest.raises(ConstructionError) as noninteger:
        stage_from_text(text, "noninteger-index.bl")
    assert noninteger.value.rule == "readable-form"
    assert noninteger.value.address is not None
    assert f"lists {member}, which is no integer" in noninteger.value.message


# the points stage whose key s lies in {0, 2}, which the declarations do not
# place within the index set {0, θ} of q
KEY_ON_TWO_MEMBERS = POINTS_TEXT.replace("(s : S_θ)", "(s : {0, 2} ⊂ ℤ)")


@pytest.mark.parametrize(
    ("text", "statuses"),
    [
        pytest.param(
            LOCATION_TEXT, [], id="keys and a binder declared on the index set by its name"
        ),
        pytest.param(
            KEY_ON_TWO_MEMBERS, ["required"], id="a key on {0, 2} for the index set {0, theta}"
        ),
    ],
)
def test_a_stage_records_an_inclusion_condition_where_its_declarations_do_not_decide_it(
    read_only_stage_from_text, text, statuses
):
    """A symbolic stage records the condition that the set of a key lies in
    the index set that it selects from exactly where the declarations do not
    decide it: none for the location stage, whose keys and binder `jp` are
    declared on L_J by its name, and one, still required, for the key s on
    {0, 2} that selects from {0, θ}."""
    obligations = read_only_stage_from_text(text).obligations()
    inclusions = [item for item in obligations if item.condition == "set-inclusion"]
    assert [item.status for item in inclusions] == statuses


def test_an_inclusion_condition_is_established_or_refused_at_calibration(
    read_only_stage_from_text,
):
    """The inclusion of the set {0, 2} of the key s in the listed set {0, θ}
    is established at θ = 2 and refused at θ = 1, with a message that gives
    the value of θ and the inclusion."""
    listed = read_only_stage_from_text(KEY_ON_TWO_MEMBERS)
    included = copy_native(listed).calibrate({"θ": 2, "β": 0.9, "q": [10.0, 20.0]})
    inclusions = [item for item in included.obligations() if item.condition == "set-inclusion"]
    assert [item.status for item in inclusions] == ["established"]
    with pytest.raises(ValueError) as refusal:
        copy_native(listed).calibrate({"θ": 1, "β": 0.9, "q": [10.0, 20.0]})
    assert "calibration θ = 1 makes {0, 2} ⊂ ℤ ⊆ {0, θ} ⊂ ℤ false" in str(refusal.value)


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("f(i : {0, κ} ⊂ ℝ) := i", id="a function"),
        pytest.param("Λ(i : {0, κ} ⊂ ℝ) := [0, i]", id="a correspondence"),
    ],
)
def test_a_member_of_the_set_of_the_argument_of_a_function_must_be_an_integer(declaration):
    """A function or a correspondence whose argument lies in the listed set
    {0, κ} is accepted at κ = 2 and refused at κ = 2.5, with a message that
    gives that value of κ."""
    text = POINTS_TEXT.replace("β   : (0,1)", "κ : ℝ₊\n" + declaration + "\nβ   : (0,1)")
    function_domain = stage_from_text(text, "function-domain.bl")
    values = {"θ": 2, "κ": 2, "β": 0.9, "q": [10.25, 20.75]}
    assert copy_native(function_domain).calibrate(values).par["κ"].value == 2
    with pytest.raises(ValueError, match="calibration κ = 2.5 makes κ ∈ ℤ"):
        copy_native(function_domain).calibrate({**values, "κ": 2.5})


@pytest.mark.parametrize("member", [pytest.param(2, id="theta 2"), pytest.param(0, id="theta 0")])
def test_a_member_written_as_one_over_theta_must_be_an_integer_at_calibration(member):
    """The symbolic stage keeps the condition that the listed member 1/θ is
    an integer, a calibration at θ = 1 is accepted, and a calibration at
    which 1/θ is no integer or is not defined is refused with a message that
    gives the value of θ and the condition on 1/θ."""
    reciprocal = stage_from_text(POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{0, 1/θ} ⊂ ℤ"), "points.bl")
    members = [item for item in reciprocal.obligations() if item.condition == "index-set-members"]
    assert [item.status for item in members] == ["required"]
    assert copy_native(reciprocal).calibrate({"θ": 1, "β": 0.9, "q": [10.25, 20.75]}).par[
        "q"
    ].value == (
        10.25,
        20.75,
    )
    with pytest.raises(ValueError, match=f"calibration θ = {member} makes 1/θ ∈ ℤ"):
        copy_native(reciprocal).calibrate({"θ": member, "β": 0.9, "q": [10.25, 20.75]})


def test_a_collection_on_a_listed_set_written_in_its_declaration_takes_an_entry_per_member():
    """A parameter declared on the listed set {0, θ} written in its own
    declaration takes at θ = 2 its two entries in the order of the members."""
    inline = stage_from_text(
        POINTS_TEXT.replace("q   : S_θ → ℝ₊", "q   : {0, θ} ⊂ ℤ → ℝ₊"), "points.bl"
    )
    assert copy_native(inline).calibrate({"θ": 2, "β": 0.9, "q": [10.25, 20.75]}).par[
        "q"
    ].value == (
        10.25,
        20.75,
    )


def test_a_member_that_reads_an_undeclared_name_is_refused():
    """The listed set {θ, b}, whose member b the stage does not declare, is
    refused under `name-in-scope`, with a message that names b."""
    phrase = "reads the name 'b', which the stage does not declare"
    with pytest.raises(ConstructionError, match=phrase) as undeclared_member:
        stage_from_text(POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{θ, b} ⊂ ℝ"), "points.bl")
    assert undeclared_member.value.rule == "name-in-scope"


@pytest.mark.parametrize(
    ("stage", "calibration", "phrases"),
    [
        pytest.param(
            "location_stage",
            SURPLUS_KEY,
            ("parameter 'dist'", "an entry at the key 3, which is no member"),
            id="a key beyond the range",
        ),
        pytest.param(
            "points_stage",
            {"θ": 2, "β": 0.9, "q": {0: 10.25, 2.5: 20.75}},
            ("parameter 'q'", "no entry at the key 2"),
            id="a key that is no integer",
        ),
    ],
)
def test_a_mapping_with_a_key_that_is_no_member_is_refused_naming_the_collection_and_the_key(
    request, stage, calibration, phrases
):
    """A calibration of a collection by a mapping whose keys are not the
    members of its index set is refused with a message that names the
    collection and the key that is no member or the member that has no
    entry."""
    with pytest.raises(ValueError) as refusal:
        copy_native(request.getfixturevalue(stage)).calibrate(calibration)
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


def test_an_entry_outside_the_set_of_the_entries_is_refused_naming_its_pair_of_keys(
    location_stage,
):
    """A negative distance in a table on ℝ₊ is refused with a message that
    names the table, the pair of keys (1, 2) and the entry -1.5."""
    with pytest.raises(ValueError) as entry:
        copy_native(location_stage).calibrate(NEGATIVE_DISTANCE)
    message = str(entry.value)
    assert "parameter 'dist'" in message and "the entry at (1, 2) -1.5" in message


@pytest.mark.parametrize(
    ("text", "calibration", "phrases"),
    [
        pytest.param(
            LOCATION_TEXT,
            FRACTIONAL_BOUND,
            ("parameter 'J'", "the value 2.5 lies outside the declared set ℕ"),
            id="a bound that is no integer",
        ),
        pytest.param(
            LOCATION_TEXT, EMPTY_RANGE, ("calibration J = 0", "1 <= J"), id="an empty range"
        ),
        pytest.param(
            LOCATION_TEXT.replace("J   : ℕ", "J   : ℕ\nK : ℕ").replace(
                "L_J := {1, …, J}", "L_J := {J, …, K}"
            ),
            {**LOCATION_CALIBRATION_J2, "J": 2**53 + 1, "K": float(2**53), "δ": [], "dist": []},
            ("calibration J = 9007199254740993, K = 9007199254740992.0", "J <= K"),
            id="a lower bound above an upper bound that rounds to it",
        ),
    ],
)
def test_a_bound_of_a_range_that_is_no_integer_or_leaves_the_range_empty_is_refused(
    read_only_stage_from_text, text, calibration, phrases
):
    """A calibration that gives a bound of a range a value that is no
    integer, or that leaves the range empty, is refused with a message that
    gives the values of the bounds and the condition they miss; a lower bound
    above the upper bound is not rounded to the upper bound to make one
    member."""
    with pytest.raises(ValueError) as refusal:
        copy_native(read_only_stage_from_text(text)).calibrate(calibration)
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


@pytest.mark.parametrize(
    "refused",
    [
        pytest.param(MISSING_ENTRY, id="a missing entry"),
        pytest.param(SURPLUS_KEY, id="a surplus key"),
        pytest.param(NEGATIVE_DISTANCE, id="a negative entry"),
        pytest.param(FRACTIONAL_BOUND, id="a bound that is no integer"),
        pytest.param(EMPTY_RANGE, id="an empty range"),
    ],
)
def test_a_refused_calibration_of_a_copy_leaves_the_other_location_versions_as_they_were(
    refused,
):
    """After the calibration of a third copy of the location stage is
    refused, the versions of the stage are as they were: the copies
    calibrated at J = 2 and J = 3 keep their values, a fourth copy
    calibrated at J = 2 holds the distance table of the first, and the
    symbolic stage stays unbound."""
    symbolic = stage_from_text(LOCATION_TEXT, "location.bl")
    at_2 = copy_native(symbolic).calibrate(LOCATION_CALIBRATION_J2)
    at_3 = copy_native(symbolic).calibrate(LOCATION_CALIBRATION_J3)
    with pytest.raises(ValueError):
        copy_native(symbolic).calibrate(refused)
    # the first parameter value of the value line is J, as the parameters
    # stand in the order of their declarations
    assert aggregation_box(at_2).kernel().parameter_values[0] == 2
    assert aggregation_box(at_3).kernel().parameter_values[0] == 3
    assert at_2.par["δ"].value == (1.0, 2.0) and at_3.par["δ"].value == (1.0, 2.0, 3.0)
    again = copy_native(symbolic).calibrate(LOCATION_CALIBRATION_J2)
    assert again.par["dist"].value == at_2.par["dist"].value
    assert symbolic.bindings.calibration is None


def test_a_table_on_the_ages_and_ten_labels_takes_a_row_for_each_age_and_refuses_two_rows(
    benhabib_stage,
):
    """The wage of the stage file of the application benhabib-2019, a table
    on its 37 ages and the ten labels of Tau, takes one row of ten entries for
    each age, and a calibration of two rows is refused with a message that
    names the wage and the 37 members of its set of ages."""
    # one row for each age from 25 to 61, each with one entry for each label
    # q1 to q10: the row of the last age holds the earnings of the ten
    # deciles, and every other row zeros
    table = [[0.0] * 10] * 36 + [
        [9.760, 19.95, 26.85, 33.05, 39.02, 45.05, 51.40, 59.16, 70.33, 100.3]
    ]
    values = {
        "β": 0.96,
        "σ": 2.0,
        "μ": 0.0,
        "A": 1.0,
        "tau": "q1",
        "r_type": "r1",
        "R_vec": [1.0, 1.02, 1.04, 1.06, 1.08],
        "wage_fn": table,
    }
    assert benhabib_stage.calibrate(values).par["wage_fn"].value[36][9] == 100.3
    with pytest.raises(ValueError) as short:
        benhabib_stage.calibrate({**values, "wage_fn": table[:2]})
    message = str(short.value)
    assert "parameter 'wage_fn'" in message and "has 37 members" in message


def test_a_parameter_on_a_product_of_five_factors_takes_five_entries_and_refuses_two(
    benhabib_stage,
):
    """The return vector of the stage file of the application benhabib-2019,
    a parameter on a product of five factors, takes five entries, one for
    each factor, and a calibration of two entries is refused with a message
    that names the return vector and its 5 coordinates."""
    values = {
        "β": 0.96,
        "σ": 2.0,
        "μ": 0.0,
        "A": 1.0,
        "tau": "q1",
        "r_type": "r1",
        "R_vec": [1.0, 1.02, 1.04, 1.06, 1.08],
        "wage_fn": [[0.0] * 10] * 37,
    }
    assert benhabib_stage.calibrate(values).par["R_vec"].value[4] == 1.08
    with pytest.raises(ValueError) as short:
        benhabib_stage.calibrate({**values, "R_vec": [1.0, 1.02]})
    message = str(short.value)
    assert "parameter 'R_vec'" in message and "has 5 coordinates" in message
