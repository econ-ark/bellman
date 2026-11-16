"""The compatibility of a pair between two stages: whether the continuation set
of its writing field lies in the arrival set of its reading field, decided from
the declarations of the two stages or at the values that the calibrations of
their periods bind, and the bindings that a decision names.

Where the bindings of the periods are given as mappings, a test calls the
selection of the connections, `select_connections`, directly.
"""

import pytest
from application_files import BUFFER_STOCK_BASELINE_CALIBRATION
from stage_builders import stage_from_text
from stage_texts import (
    BOUNDED,
    BUFFER_STOCK_ARRIVAL_K_DECLARATION,
    BUFFER_STOCK_CONTINUATION_A_DECLARATION,
    BUFFER_STOCK_XA_DEFINITION,
    UNCHANGED,
    buffer_stock_text_with_changes,
    renamed,
)
from trellises import (
    connection_between,
    period_record,
    printed_pairs,
    rejected_pairs,
    selection_of_periods,
    write_files,
)

from bellman.factory import connections
from bellman.factory.connections import select_connections
from bellman.native.hypergraphs import copy_native
from bellman.native.provenance import source_description
from bellman.refusals import FactoryError
from bellman.trellis import (
    calibrate_trellis,
    connection_report,
    elaborate_trellis,
    load_recipe,
    specify_trellis,
)

# the files of a model folder of two periods: the later period `p1` holds one
# occurrence `b1` of the bounded stage, whose state lies in `[a_min, inf)`;
# the earlier period `p2` holds a second occurrence `b2` beside an occurrence
# of the unchanged stage, which carries `a` unchanged from its arrival perch
# to its continuation perch and shares `β` with `b2`; `a_min` is one
# parameter of each period, bound to 0 in `p1` and to 1 in `p2`, and the
# slots `$b2_fill` and `$u_fill` take a further calibration source
BOUNDED_MODEL_FILES = {
    "stages/b1/b1.bl": renamed(BOUNDED, "b1"),
    "stages/b2/b2.bl": renamed(BOUNDED, "b2"),
    "stages/u2/u2.bl": renamed(UNCHANGED, "u2"),
    "calibration/one.yml": "calibration:\n  a_min: 0.0\n  β: 0.9\n",
    "calibration/two.yml": "calibration:\n  a_min: 1.0\n  β: 0.9\n",
    "calibration/u.yml": "calibration:\n  β: 0.9\n",
    "p1.yml": "name: p1\nstages: [b1]\nconnectors: []\n",
    "p2.yml": "name: p2\nstages: [b2, u2]\nconnectors: []\n",
    "trellis.yml": "periods:\n  - {template: p1.yml}\n  - {template: p2.yml}\n"
    "inter_connectors:\n  - {b2.a: a}\n",
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n"
        "  b1: {stage: stages/b1/b1.bl, calibration: {all: [calibration/one]}}\n"
        "  b2: {stage: stages/b2/b2.bl, calibration: {all: [calibration/two, $b2_fill]}}\n"
        "  u2: {stage: stages/u2/u2.bl, calibration: {all: [calibration/u, $u_fill]}}\n"
    ),
}


def pair_and_route(text, calibration=None):
    """The one pair and the one route of the connection report of two
    periods of the stage text `text` joined by `{a: k}`, each period
    calibrated with `calibration` where one is given."""
    report = connection_between(text, text, calibration)
    (pair,), (route,) = report.pairs, report.routes
    return pair, route


def named_sets(continuation_set, arrival_set, declarations=""):
    """The text of the buffer-stock stage file with its continuation field `a`
    declared in the named set `Xa := continuation_set` and its arrival field
    `k` in a second named set `Xk := arrival_set`, after the further
    `declarations`."""
    return buffer_stock_text_with_changes(
        (
            BUFFER_STOCK_XA_DEFINITION,
            f"{declarations}Xa := {continuation_set}\nXk := {arrival_set}\n",
        ),
        (BUFFER_STOCK_ARRIVAL_K_DECLARATION, "(k : Xk, ψ, ξ)"),
    )


def listed_sets(continuation_set, arrival_set, declarations=""):
    """The text of the buffer-stock stage file with the set of `a`,
    `continuation_set`, and the set of `k`, `arrival_set`, written in the
    lists of the block headers, after the further `declarations`."""
    return buffer_stock_text_with_changes(
        (BUFFER_STOCK_XA_DEFINITION, BUFFER_STOCK_XA_DEFINITION + declarations),
        (BUFFER_STOCK_ARRIVAL_K_DECLARATION, f"(k : {arrival_set}, ψ, ξ)"),
        (BUFFER_STOCK_CONTINUATION_A_DECLARATION, f"(a : {continuation_set})"),
    )


def calibration_digests(trellis):
    """The digest of the calibration that each stage occurrence of the
    trellis `trellis` binds, by its position `(h, key)`."""
    return {
        (h, key): source_description(dict(stage.bindings.calibration))["sha256"]
        for h, period in enumerate(trellis["periods"])
        for key, stage in period["stages"].items()
    }


def three_bounded_periods(stages):
    """The trellis of three periods of one occurrence `B` each, holding the
    stages `stages` from `periods[0]` on, joined by `{a: a}` between each two
    periods."""
    return {
        "periods": [period_record({"B": stage}) for stage in stages],
        "inter_connectors": [{"a": "a"}, {"a": "a"}],
    }


@pytest.fixture(scope="module")
def bounded_folder(tmp_path_factory):
    """The model folder of `BOUNDED_MODEL_FILES`, written once for the
    module."""
    return write_files(tmp_path_factory.mktemp("bounded"), BOUNDED_MODEL_FILES)


@pytest.fixture(scope="module")
def bounded_trellis(bounded_folder):
    """The specified trellis of the recipe `spec.yml` of the bounded model
    folder, which the tests read and do not bind."""
    return specify_trellis(load_recipe(bounded_folder, "spec.yml"))


@pytest.fixture(scope="module")
def bounded_report(bounded_trellis):
    return connection_report(bounded_trellis)


@pytest.fixture(scope="module")
def lowered_report(bounded_folder, bounded_trellis):
    """The connection report of the bounded trellis calibrated again, with
    `a_min` bound to -1 in the earlier period."""
    lowered = load_recipe(bounded_folder, "spec.yml", b2_fill={"a_min": -1.0})
    return connection_report(calibrate_trellis(bounded_trellis, lowered))


@pytest.fixture(scope="module")
def inclusion_selection(identity_stage, strictly_positive_identity_stage):
    """The selection of one period of an occurrence S of the unchanged stage
    with its state in ℝ₊₊ and an occurrence T with its state in ℝ₊, under no
    connector."""
    return selection_of_periods(
        [period_record({"S": strictly_positive_identity_stage, "T": identity_stage})]
    )


@pytest.fixture(scope="module")
def label_stages():
    """Two copies of the unchanged stage, by the finite set of labels in which
    their state lies."""
    return {
        labels: stage_from_text(UNCHANGED.replace("ℝ₊", labels), f"{name}.bl")
        for labels, name in (("{low, high}", "finite"), ("{low, high, mid}", "wider"))
    }


@pytest.fixture(scope="module")
def bounded_periods(bounded_identity_stage):
    """Two periods of one occurrence each of the bounded stage: T in the later
    period, `periods[0]`, and S in the earlier, `periods[1]`."""
    return [
        period_record({"T": bounded_identity_stage}),
        period_record({"S": bounded_identity_stage}),
    ]


@pytest.fixture(scope="module")
def bounded_at(bounded_identity_stage):
    """Two calibrated copies of the bounded stage, by the value of `a_min`; a
    calibration binds the stage that it is called on, so that each binds a
    copy of its own."""
    return {
        bound: copy_native(bounded_identity_stage).calibrate({"a_min": bound, "β": 0.9})
        for bound in (0.0, 1.0)
    }


# the basis of a pair decided at values: for each side, its period, its stage
# key and the digest of the calibration that the comparison read
def test_a_pair_between_two_periods_is_decided_at_the_bound_that_each_period_binds(
    bounded_trellis, bounded_report
):
    """The pair from the earlier period, which binds `a_min` to 1, into the
    later, which binds it to 0, is compatible at those values, its basis
    naming the calibration of the writing and of the reading occurrence."""
    stage_digests = calibration_digests(bounded_trellis)
    (pair,) = bounded_report.pairs
    assert (str(pair.writing), str(pair.reading), pair.compatibility) == (
        "periods[1].b2.a",
        "periods[0].b1.a",
        "compatible",
    )
    assert "[1, inf) against [0, inf)" in pair.reason
    assert pair.basis == (
        (1, "b2", stage_digests[1, "b2"]),
        (0, "b1", stage_digests[0, "b1"]),
    )


def test_the_connection_report_names_the_digest_of_the_calibration_of_each_position(
    bounded_trellis, bounded_report
):
    """The bindings of the connection report give, for each stage occurrence,
    the digest of the calibration that it binds."""
    assert dict(bounded_report.bindings) == calibration_digests(bounded_trellis)


def test_the_route_of_a_pair_decided_at_values_is_certified_on_its_basis_with_no_diagnostic(
    bounded_report,
):
    """The route between the two periods is certified on the basis of its
    pair, with no diagnostic in the connection report."""
    (pair,) = bounded_report.pairs
    (route,) = bounded_report.routes
    assert route.status == "certified" and route.basis == pair.basis
    assert bounded_report.diagnostics == ()


def test_an_elaborated_trellis_reads_no_value_of_the_calibrations_that_its_recipe_names(
    bounded_folder,
):
    """Before the calibration, the bound `a_min` of each period has no value,
    so that the pair between the periods is not established, its reason
    naming the two bounds without a value, and has no basis."""
    trellis = elaborate_trellis(load_recipe(bounded_folder, "spec.yml"))
    (pair,) = connection_report(trellis).pairs
    assert pair.compatibility == "not-established" and pair.basis == ()
    assert (
        "the bounds a_min of periods[0].b1 and a_min of periods[1].b2 have no finite value in "
        "the bindings given" in pair.reason
    )


def test_a_second_calibration_with_the_earlier_bound_below_the_later_makes_the_pair_incompatible(
    bounded_trellis, lowered_report
):
    """Calibrated again with `a_min` bound to -1 in the earlier period, below
    the 0 of the later, the pair between the periods is incompatible, its
    route uncertified, under a new digest for the earlier period and the same
    digest for the later."""
    stage_digests = calibration_digests(bounded_trellis)
    changed, _ = lowered_report.pairs
    assert changed.compatibility == "incompatible"
    assert "[-1, inf) against [0, inf)" in changed.reason
    # the third entry of each side of a basis is the digest of its calibration
    assert changed.basis[0][2] != stage_digests[1, "b2"]
    assert changed.basis[1] == (0, "b1", stage_digests[0, "b1"])
    (between,) = [route for route in lowered_report.routes if route.destination == (0, "b1")]
    assert between.status == "uncertified"


def test_a_lower_bound_of_the_earlier_period_admits_the_pair_from_its_unchanged_stage(
    bounded_report, lowered_report
):
    """The pair from the unchanged stage, whose state lies in ℝ₊, into the
    bounded stage of the earlier period, rejected while `a_min` is 1, is
    inferred once `a_min` is -1."""
    assert [
        (str(rejection.writing), str(rejection.reading)) for rejection in bounded_report.rejected
    ] == [("periods[1].u2.a", "periods[1].b2.a")]
    _, inferred = lowered_report.pairs
    assert (str(inferred.writing), str(inferred.reading), inferred.origin) == (
        "periods[1].u2.a",
        "periods[1].b2.a",
        "inferred",
    )


def test_a_specified_trellis_keeps_its_bindings_and_pairs_after_a_calibration_and_a_refused_one(
    bounded_folder,
):
    """After a calibration of a specified trellis, and after one that a period
    refuses, since it gives the unchanged stage a `β` other than the bounded
    stage's, the specified trellis keeps its bindings and its pairs and names
    no digest of the request."""
    specified = specify_trellis(load_recipe(bounded_folder, "spec.yml"))
    report = connection_report(specified)
    stage_digests = calibration_digests(specified)
    calibrate_trellis(specified, load_recipe(bounded_folder, "spec.yml", b2_fill={"a_min": -1.0}))
    requested = load_recipe(bounded_folder, "spec.yml", u_fill={"β": 0.5})
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(specified, requested)
    assert refused.value.rule == "period-parameter-agreement"
    again = connection_report(specified)
    assert dict(again.bindings) == stage_digests and again.pairs == report.pairs
    digests = set(again.bindings.values())
    assert source_description({"β": 0.5})["sha256"] not in digests
    assert source_description({"a_min": 1.0, "β": 0.5})["sha256"] not in digests


def test_of_two_state_sets_the_pair_into_the_larger_is_inferred_and_the_other_rejected(
    inclusion_selection,
):
    """Of the two directions between occurrences whose states lie in ℝ₊₊ and
    in ℝ₊, the pair from the smaller set into the larger is inferred as
    compatible, and the reverse is rejected as incompatible."""
    assert printed_pairs(inclusion_selection) == [
        ("periods[0].S.a", "periods[0].T.a", "periods[0]")
    ]
    (pair,) = inclusion_selection.pairs
    assert pair.origin == "inferred" and pair.compatibility == "compatible"
    assert "ℝ₊₊, lies in" in pair.reason and pair.reason.endswith("ℝ₊")
    assert rejected_pairs(inclusion_selection) == [
        ("periods[0].T.a", "periods[0].S.a", "candidate-incompatible")
    ]


def test_a_pair_inferred_by_the_inclusion_of_state_sets_certifies_one_route_without_a_diagnostic(
    inclusion_selection,
):
    """The selection of the pair inferred from ℝ₊₊ into ℝ₊ certifies one
    route, with no diagnostic."""
    assert inclusion_selection.counts["certified"] == 1 and inclusion_selection.diagnostics == ()


def test_a_bare_endpoint_is_ambiguous_where_two_stages_write_the_field_whatever_their_sets(
    identity_stage, strictly_positive_identity_stage
):
    """The connector `{a: T.a}` names no stage for `a`, which S and U both
    write into a set that lies in the arrival set of T, so that it selects
    no pair and is diagnosed as ambiguous."""
    stages = {"S": strictly_positive_identity_stage, "T": identity_stage, "U": identity_stage}
    bare = selection_of_periods([period_record(stages, [{"a": "T.a"}])])
    assert bare.pairs == () and [diagnostic.rule for diagnostic in bare.diagnostics] == [
        "endpoint-ambiguous"
    ]


def test_a_named_set_is_read_through_the_definition_of_its_own_stage():
    """`X := ℝ₊` in the writing stage and `X := ℝ₊₊` in the reading stage are
    two sets, so that the authored pair between them is incompatible, with a
    diagnostic for the pair and for its route, which is uncertified."""
    named = UNCHANGED.replace("β : (0,1)\n", "β : (0,1)\nX := ℝ₊\n").replace("a : ℝ₊", "a : X")
    nonnegative = stage_from_text(named, "nonnegative.bl")
    strictly = stage_from_text(named.replace("X := ℝ₊\n", "X := ℝ₊₊\n"), "strictly.bl")
    authored = selection_of_periods(
        [period_record({"S": nonnegative, "T": strictly}, [{"S.a": "T.a"}])]
    )
    (pair,) = authored.pairs
    assert (
        pair.compatibility == "incompatible"
        and "ℝ₊, does not lie in" in pair.reason
        and pair.reason.endswith("ℝ₊₊")
    )
    assert [diagnostic.rule for diagnostic in authored.diagnostics] == [
        "pair-incompatible",
        "route-incompatible",
    ]
    assert authored.routes[0].status == "uncertified"


def test_one_finite_set_of_labels_written_on_both_sides_of_a_pair_is_one_set(label_stages):
    """An authored pair from a state in `{low, high}` into a state in the same
    set is compatible as one set, with no diagnostic."""
    finite = label_stages["{low, high}"]
    selection = selection_of_periods([period_record({"S": finite, "T": finite}, [{"S.a": "T.a"}])])
    (pair,) = selection.pairs
    assert pair.compatibility == "compatible" and "are one set, {low, high}" in pair.reason
    assert [diagnostic.rule for diagnostic in selection.diagnostics] == []


@pytest.mark.parametrize(
    ("writing", "reading", "compatibility", "phrase", "rules"),
    [
        pytest.param(
            "{low, high}",
            "{low, high, mid}",
            "compatible",
            "{low, high}, lies in",
            [],
            id="a set within a wider one",
        ),
        pytest.param(
            "{low, high, mid}",
            "{low, high}",
            "incompatible",
            "does not lie in",
            ["pair-incompatible", "route-incompatible"],
            id="a wider set into a narrower one",
        ),
    ],
)
def test_two_finite_sets_of_labels_are_compared_by_their_members(
    label_stages, writing, reading, compatibility, phrase, rules
):
    """An authored pair from a state in one finite set of labels into a state
    in another is compatible where each label of the writing set is a label
    of the reading set."""
    selection = selection_of_periods(
        [period_record({"S": label_stages[writing], "T": label_stages[reading]}, [{"S.a": "T.a"}])]
    )
    (pair,) = selection.pairs
    assert pair.compatibility == compatibility and phrase in pair.reason
    assert [diagnostic.rule for diagnostic in selection.diagnostics] == rules


def test_a_bound_shared_by_two_occurrences_in_one_period_certifies_their_route_without_a_value(
    bounded_identity_stage,
):
    """`a_min` is one parameter of the period that holds two occurrences of the
    bounded stage, so that their pair is compatible and its route certified
    without a value."""
    within = selection_of_periods(
        [
            period_record(
                {"S": bounded_identity_stage, "T": bounded_identity_stage}, [{"S.a": "T.a"}]
            )
        ]
    )
    (pair,) = within.pairs
    assert (
        pair.compatibility == "compatible"
        and pair.basis == ()
        and "a_min names one parameter of periods[0]" in pair.reason
    )
    assert within.counts["certified"] == 1


def test_one_spelling_of_a_bound_in_two_periods_names_two_parameters_without_a_value(
    bounded_periods,
):
    """In two periods `a_min` names two parameters, so that without values the
    pair between the periods is not established, with a diagnostic for the
    pair and for its route."""
    across = selection_of_periods(bounded_periods, [{"a": "a"}])
    (pair,) = across.pairs
    assert pair.compatibility == "not-established" and pair.basis == ()
    phrases = [
        "names two parameters",
        "a_min of periods[0].T and a_min of periods[1].S have no finite value",
    ]
    assert [phrase for phrase in phrases if phrase not in pair.reason] == []
    assert [diagnostic.rule for diagnostic in across.diagnostics] == [
        "pair-not-established",
        "route-not-established",
    ]


# the bindings of each row are given by position (h, key): the index of the
# period and the stage key of its occurrence; each row expects the
# compatibility of the pair and the status of its route
@pytest.mark.parametrize(
    ("bindings", "expected", "phrase"),
    [
        pytest.param(
            {(1, "S"): {"a_min": 1.0}, (0, "T"): {"a_min": 0.0}},
            ("compatible", "certified"),
            "[1, inf) against [0, inf)",
            id="the earlier bound above the later",
        ),
        pytest.param(
            {(1, "S"): {"a_min": 0.0}, (0, "T"): {"a_min": 1.0}},
            ("incompatible", "uncertified"),
            "[0, inf) against [1, inf)",
            id="the earlier bound below the later",
        ),
        pytest.param(
            {(1, "S"): {"a_min": 0.0}, (0, "T"): None},
            ("not-established", "uncertified"),
            "the bound a_min of periods[0].T has no finite value",
            id="no binding of the later period",
        ),
        pytest.param(
            {(1, "S"): {"a_min": -1.0}, (0, "T"): {"a_min": 0.0}},
            ("incompatible", "uncertified"),
            "[-1, inf) against [0, inf)",
            id="a negative earlier bound below the later",
        ),
        pytest.param(
            {(1, "S"): {"a_min": -1.0}, (0, "T"): {"a_min": -2.5}},
            ("compatible", "certified"),
            "[-2.5, inf)",
            id="a negative later bound with a fraction",
        ),
        pytest.param(
            {(1, "S"): {"a_min": float("-inf")}, (0, "T"): {"a_min": 0.0}},
            ("not-established", "uncertified"),
            "a_min of periods[1].S has no finite value",
            id="an infinite earlier bound",
        ),
    ],
)
def test_a_bound_in_two_periods_is_decided_at_the_binding_given_for_each_period(
    bounded_periods, bindings, expected, phrase
):
    """The selection of the connections, given the binding of each period as
    a mapping, decides the pair between the periods at the two values of
    `a_min`, its basis and its route's naming each position with the binding
    read for it, and leaves it not established, with no basis, where a value
    is missing or not finite."""
    # the periods, the inter-period mappings and the bindings by position
    selection = select_connections(bounded_periods, [{"a": "a"}], bindings)
    (pair,), (route,) = selection.pairs, selection.routes
    assert (pair.compatibility, route.status) == expected
    assert phrase in pair.reason
    sides = ((1, "S", selection.bindings[(1, "S")]), (0, "T", selection.bindings[(0, "T")]))
    assert pair.basis == (() if expected[0] == "not-established" else sides)
    assert route.basis == pair.basis


@pytest.mark.parametrize(
    "bounds",
    [
        pytest.param((0.0, 1.0, 0.0), id="periods bound at 0, 1 and 0"),
        pytest.param((1.0, 0.0, 1.0), id="periods bound at 1, 0 and 1"),
    ],
)
def test_a_selection_reads_the_fields_of_one_stage_text_twice_whatever_its_bindings(
    bounded_at, monkeypatch, bounds
):
    """The selection of three periods of one stage text, bound at two values
    of `a_min`, reads the fields of the stage twice, once to find the field
    uses and once to read their compatibility."""
    field_reads = []
    native_fields = connections.fields

    def counted_fields(stage):
        field_reads.append(stage.provenance["sha256"])
        return native_fields(stage)

    monkeypatch.setattr(connections, "fields", counted_fields)
    report = connection_report(three_bounded_periods([bounded_at[bound] for bound in bounds]))
    assert len(set(report.bindings.values())) == 2
    assert len(field_reads) == 2 and len(set(field_reads)) == 1


@pytest.mark.parametrize(
    ("bounds", "compatibilities"),
    [
        pytest.param(
            (0.0, 1.0, 0.0), ["compatible", "incompatible"], id="periods bound at 0, 1 and 0"
        ),
        pytest.param(
            (1.0, 0.0, 1.0), ["incompatible", "compatible"], id="periods bound at 1, 0 and 1"
        ),
    ],
)
def test_each_pair_of_three_periods_is_decided_at_the_bindings_of_its_own_two_periods(
    bounded_at, bounds, compatibilities
):
    """Each of the two pairs between three periods of one stage text is
    decided at the bindings of the two periods that it joins, which its basis
    names."""
    report = connection_report(three_bounded_periods([bounded_at[bound] for bound in bounds]))
    assert [pair.compatibility for pair in report.pairs] == compatibilities
    for pair in report.pairs:
        positions = ((pair.writing.h, "B"), (pair.reading.h, "B"))
        assert pair.basis == tuple(
            (*position, report.bindings[position]) for position in positions
        )
        assert pair.basis[0][2] != pair.basis[1][2]


@pytest.mark.parametrize(
    ("form", "continuation_set", "arrival_set", "expected"),
    [
        pytest.param(
            named_sets,
            "{x : ℝ | x > 0}",
            "{x : ℝ | x > -0.3}",
            ("compatible", "certified"),
            id="a condition within a lower bound",
        ),
        pytest.param(
            listed_sets,
            "(0, inf)",
            "(-0.3, inf)",
            ("compatible", "certified"),
            id="an interval within a lower bound",
        ),
        pytest.param(
            named_sets,
            "{x : ℝ | x > -0.5}",
            "{x : ℝ | x > -0.3}",
            ("incompatible", "uncertified"),
            id="a condition below a lower bound",
        ),
        pytest.param(
            listed_sets,
            "(-0.5, inf)",
            "(-0.3, inf)",
            ("incompatible", "uncertified"),
            id="an interval below a lower bound",
        ),
        pytest.param(
            named_sets,
            "{x : ℝ | x >= 0}",
            "{x : ℝ | x > 0}",
            ("incompatible", "uncertified"),
            id="a weak bound against a strict one at the same number",
        ),
        pytest.param(
            named_sets,
            "{x : ℝ₊ | x < 5}",
            "{x : ℝ | x >= 0}",
            ("compatible", "certified"),
            id="an upper bound within a set with a lower end of its own",
        ),
    ],
)
def test_an_interval_or_a_set_with_one_condition_on_its_variable_is_compared_by_its_bounds(
    form, continuation_set, arrival_set, expected
):
    """The continuation set of `a`, written as an interval in a block header
    or as a named set with one condition on its variable, is compared with
    the arrival set of `k` as the interval that its bound gives."""
    pair, route = pair_and_route(
        form(continuation_set, arrival_set), BUFFER_STOCK_BASELINE_CALIBRATION
    )
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == expected


def test_the_reason_of_a_pair_between_two_intervals_names_both_sets_and_their_perches():
    """The reason of the compatible pair from `{x : ℝ | x > 0}` into
    `{x : ℝ | x > -0.3}` names the continuation set and the arrival set, each
    as the interval that its condition gives."""
    text = named_sets("{x : ℝ | x > 0}", "{x : ℝ | x > -0.3}")
    pair, _ = pair_and_route(text, BUFFER_STOCK_BASELINE_CALIBRATION)
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert pair.reason == (
        "the continuation set of periods[1].bs.a, ℝ @ (0, inf), lies in the arrival set of "
        "periods[0].bs.k, ℝ @ (-0.3, inf)"
    )


def test_one_set_written_on_both_sides_of_a_pair_is_one_set_without_a_calibration():
    """The set `Xa := {x : ℝ | x > 0}` of both `a` and `k` makes the pair
    compatible and its route certified with no value bound."""
    pair, route = pair_and_route(
        buffer_stock_text_with_changes((BUFFER_STOCK_XA_DEFINITION, "Xa := {x : ℝ | x > 0}\n"))
    )
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == ("compatible", "certified")
    assert "are one set, ℝ @ (0, inf)" in pair.reason


@pytest.mark.parametrize(
    ("j", "compatibility", "phrase"),
    [
        pytest.param(
            -0.25,
            "compatible",
            "(0, inf) against (-0.25, inf)",
            id="the earlier bound above the later",
        ),
        pytest.param(
            0.25,
            "incompatible",
            "(0, inf) against (0.25, inf)",
            id="the earlier bound below the later",
        ),
    ],
)
def test_a_bound_that_names_a_parameter_is_read_at_the_value_of_the_parameter(
    j, compatibility, phrase
):
    """The bounds `l` of `a` and `j` of `k` are read at the values that the
    calibration of each period gives, `l` at 0."""
    text = named_sets("{x : ℝ | x > l}", "{x : ℝ | x > j}", "l : ℝ\nj : ℝ\n")
    calibration = {**BUFFER_STOCK_BASELINE_CALIBRATION, "l": 0.0, "j": j}
    pair, _ = pair_and_route(text, calibration)
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert pair.compatibility == compatibility and len(pair.basis) == 2
    assert phrase in pair.reason


@pytest.mark.parametrize(
    ("form", "continuation_set", "arrival_set", "derived", "compatibility", "status", "phrases"),
    [
        pytest.param(
            listed_sets,
            "(l, inf)",
            "(j, inf)",
            "j := l - 0.25",
            "compatible",
            "certified",
            [
                "at the values l = 0.0 of periods[1].bs, j = -0.25 of periods[0].bs",
                "(0, inf) against (-0.25, inf)",
            ],
            id="intervals, the earlier bound above the later",
        ),
        pytest.param(
            named_sets,
            "{x : ℝ | x > l}",
            "{x : ℝ | x > j}",
            "j := l - 0.25",
            "compatible",
            "certified",
            [
                "at the values l = 0.0 of periods[1].bs, j = -0.25 of periods[0].bs",
                "(0, inf) against (-0.25, inf)",
            ],
            id="conditions, the earlier bound above the later",
        ),
        pytest.param(
            listed_sets,
            "(l, inf)",
            "(j, inf)",
            "j := l + 0.25",
            "incompatible",
            "uncertified",
            ["(0, inf) against (0.25, inf)"],
            id="intervals, the earlier bound below the later",
        ),
    ],
)
def test_a_bound_that_is_a_derived_parameter_is_read_at_its_value(
    form, continuation_set, arrival_set, derived, compatibility, status, phrases
):
    """The bound `j`, derived from `l`, is read at the value that it takes at
    the calibration of each period, `l` at 0, and the pair names the
    calibration of each of the two periods that it read."""
    pair, route = pair_and_route(
        form(continuation_set, arrival_set, f"l : ℝ\n{derived}\n"),
        {**BUFFER_STOCK_BASELINE_CALIBRATION, "l": 0.0},
    )
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == (compatibility, status)
    assert [phrase for phrase in phrases if phrase not in pair.reason] == []
    assert [entry[:2] for entry in pair.basis] == [(1, "bs"), (0, "bs")]


def test_a_bound_that_is_a_derived_parameter_has_no_value_without_a_calibration():
    """Without a calibration the derived bound `j := l + 0.25` has no value,
    so that the pair is not established, its reason naming `j` and `l` as
    the bounds without a value, and has no basis."""
    pair, _ = pair_and_route(listed_sets("(l, inf)", "(j, inf)", "l : ℝ\nj := l + 0.25\n"))
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert pair.compatibility == "not-established" and pair.basis == ()
    assert (
        "the bounds j of periods[0].bs and l of periods[1].bs have no finite value in the "
        "bindings given" in pair.reason
    )


def test_two_bounds_without_values_leave_the_pair_undecided_naming_the_two_parameters():
    """Without a calibration the reason names the two parameters `l` and `j`
    as the bounds without a value, and not the variable `x`."""
    text = named_sets("{x : ℝ | x > l}", "{x : ℝ | x > j}", "l : ℝ\nj : ℝ\n")
    pair, route = pair_and_route(text)
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == ("not-established", "uncertified")
    assert pair.reason == (
        "the bounds j of periods[0].bs and l of periods[1].bs have no finite value in the "
        "bindings given, so the continuation set of periods[1].bs.a, ℝ @ (l, inf), against the "
        "arrival set of periods[0].bs.k, ℝ @ (j, inf), is not decided"
    )


@pytest.mark.parametrize(
    "continuation_set",
    [
        pytest.param("{x : ℝ | x*x > 2}", id="a condition on a product of the variable"),
        pytest.param("{x : ℝ | x > 0, x < 5}", id="two conditions"),
    ],
)
def test_a_set_of_a_form_that_the_package_does_not_compare_leaves_the_pair_undecided(
    continuation_set,
):
    """The reason of the pair from a set whose condition the package does not
    compare says that the form is not compared, and names no bound."""
    text = named_sets(continuation_set, "{x : ℝ | x > -0.3}")
    pair, route = pair_and_route(text, BUFFER_STOCK_BASELINE_CALIBRATION)
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == ("not-established", "uncertified")
    assert "is of a form the package does not compare against" in pair.reason
    assert "bound" not in pair.reason


def test_one_set_whose_condition_calls_a_function_of_a_parameter_is_not_taken_as_one_set():
    """The condition of `Xa` calls the function `𝑓`, which reads the parameter
    `l` that each period binds for itself, so that the set written on both
    sides of the pair is of a form that the package does not compare."""
    text = buffer_stock_text_with_changes(
        (BUFFER_STOCK_XA_DEFINITION, "l : ℝ\n𝑓(y : ℝ) := y + l\nXa := {x : ℝ | x >= 𝑓(0)}\n")
    )
    pair, route = pair_and_route(text, {**BUFFER_STOCK_BASELINE_CALIBRATION, "l": 0.0})
    assert (str(pair.writing), str(pair.reading)) == ("periods[1].bs.a", "periods[0].bs.k")
    assert (pair.compatibility, route.status) == ("not-established", "uncertified")
    assert "is of a form the package does not compare against" in pair.reason
    assert "bound" not in pair.reason
