"""The connections between the stages of a trellis: the pairs that connectors
author and that equal names infer, their endpoints, the candidates and their
cycles and disputes, the routes, the joins and the order of a period, the
fields that no join reaches, and the connection report of a trellis whose
connections are unfinished.

An endpoint that names no field or several, a continuation field that two
entries map and an authored cycle each stay on the trellis that the
construction returns, with a diagnostic. The forward order of a period
refuses a field that two entries map and an authored cycle, and the route
of a connector with an unresolved entry, or of a field that two entries
map, is not certified. Where a test gives the calibrations as mappings, it
calls the selector `select_connections` directly. A field use is a state
field of a stage occurrence at its arrival perch or at its continuation
perch."""

import re
from copy import deepcopy

import pytest
from application_files import PORTFOLIO
from model_explorer_views import needs_viewer
from stage_builders import stage_from_text
from stage_texts import BOUNDED, TWO_FIELDS, UNCHANGED, renamed
from trellises import (
    candidate_groups,
    declarations_copy,
    one_route,
    period_record,
    port_cons_vfi_trellis_file_without_connectors,
    printed_pairs,
    rejected_pairs,
    selection_of_periods,
)

from bellman.factory.connections import select_connections
from bellman.factory.joins import checked_selection, forward_order, period_joins
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    accrete,
    connection_report,
    diagram_trellis,
    elaborate_trellis,
    inter_period_joins,
    load_trellis,
    specify_trellis,
    to_model_explorer,
    unjoined_fields,
    unpaired_joins,
)

# the connector that maps the two fields of S to the two fields of T crossed,
# `a` to `b` and `b` to `a`
CROSSED_CONNECTOR = {"S.a": "T.b", "S.b": "T.a"}


def trellis_of(*periods, inter_connectors=()):
    """The elaborated trellis of the periods given, `periods[0]` first."""
    return elaborate_trellis(
        {"periods": list(periods), "inter_connectors": list(inter_connectors)}
    )


def port_attributes(view, direction):
    """The attributes of every port of the graph `direction` of a view that
    a join names, by the port's id."""
    (graph,) = [graph for graph in view.graphs if graph.id == direction]
    found = {}
    for node in graph.nodes:
        for port in (*node.inputsMetadata, *node.outputsMetadata):
            attributes = {attribute.key: attribute.value for attribute in port.attrs}
            if "join" in attributes:
                found[port.id] = attributes
    return found


def relay_text(name, arrivals, continuations):
    """The text of a stage named `name` that arrives at the state fields
    `arrivals`, sums them into its decision state and continues to each of
    `continuations`, every field in ℝ₊, its value discounted."""
    ins = ", ".join(f"{a} : ℝ₊" for a in arrivals)
    outs = ", ".join(f"{c} : ℝ₊" for c in continuations)
    lines = "\n".join(f"    {c} = s" for c in continuations)
    return (
        f"@stage: {name}\nβ : (0,1)\n"
        f"[id=arvl_to_dcsn, ({ins}) : !arvl -> (s : ℝ₊) : !dcsn] {{\n"
        f"    s = {' + '.join(arrivals)}\n}}\n"
        f"[id=dcsn_to_cntn, (s) : !dcsn -> ({outs}) : !cntn] {{\n{lines}\n}}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = β*V[>]\n}\n"
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
        "    V[<] = V\n}\n"
    )


@pytest.fixture(scope="module")
def renamed_two_fields():
    """The two-field stage named `two_t`, so that the two occurrences of a
    crossed connector hold stages of different names."""
    return stage_from_text(renamed(TWO_FIELDS, "two_t"), "two_t.bl")


@pytest.fixture(scope="module")
def crossed_trellis(two_state_identity_stage, renamed_two_fields):
    """A trellis of one period whose connector maps `S`'s two fields to
    `T`'s crossed."""
    return trellis_of(
        period_record(
            {"S": two_state_identity_stage, "T": renamed_two_fields}, [CROSSED_CONNECTOR]
        )
    )


@pytest.fixture(scope="module")
def crossed_report(crossed_trellis):
    """The connection report of the crossed trellis."""
    return connection_report(crossed_trellis)


@pytest.fixture(scope="module")
def crossed_view(crossed_trellis):
    """The view of the crossed trellis in Model Explorer."""
    return to_model_explorer(crossed_trellis)


@pytest.fixture(scope="module")
def unfinished_trellis(two_state_identity_stage, renamed_two_fields, identity_stage):
    """A trellis of two periods whose later period holds the crossed
    connector, whose earlier period's connector `{a: q}` names two
    continuation fields and no arrival field, and whose inter-period
    connector `{a: a, b: b}` names several fields on each side."""
    later = period_record(
        {"S": two_state_identity_stage, "T": renamed_two_fields}, [CROSSED_CONNECTOR]
    )
    earlier = period_record({"S": two_state_identity_stage, "U": identity_stage}, [{"a": "q"}])
    return trellis_of(later, earlier, inter_connectors=[{"a": "a", "b": "b"}])


@pytest.fixture(scope="module")
def unfinished_report(unfinished_trellis):
    """The connection report of the unfinished trellis."""
    return connection_report(unfinished_trellis)


@pytest.fixture(scope="module")
def unfinished_restricted_report(unfinished_trellis):
    """The connection report of the unfinished trellis restricted to its
    earlier period, `periods[1]`."""
    return connection_report(unfinished_trellis, periods=[1])


@pytest.fixture(scope="module")
def unfinished_periods(unfinished_trellis):
    """The two periods of the unfinished trellis, the later one first."""
    return unfinished_trellis["periods"]


@pytest.fixture(scope="module")
def incompatible_pair_trellis(identity_stage):
    """A trellis of one period whose connector maps `S`'s field `a` in ℝ₊ to
    the field `a` in ℝ₊₊ of `T`, a stage named `positive`."""
    positive = stage_from_text(renamed(UNCHANGED.replace("ℝ₊", "ℝ₊₊"), "positive"), "positive.bl")
    return trellis_of(period_record({"S": identity_stage, "T": positive}, [{"S.a": "T.a"}]))


@pytest.fixture(scope="module")
def incompatible_pair_report(incompatible_pair_trellis):
    """The connection report of the trellis of the incompatible pair."""
    return connection_report(incompatible_pair_trellis)


@pytest.fixture(scope="module")
def three_arrivals_at_a(identity_stage, disc_with_k_next):
    """The stage occurrences of a period in which `S` carries `a` unchanged
    and the discounting stages `T` and `U` arrive at `a`, so that three
    stages arrive at `a` and `S` alone continues to it."""
    return {"S": identity_stage, "T": disc_with_k_next, "U": disc_with_k_next}


@pytest.fixture(scope="module")
def duplicate_claim_trellis(identity_stage):
    """A trellis of one period of three stages that carry `a` unchanged,
    whose two connectors both map `S`'s field `a`, written `S.a` in each."""
    return trellis_of(
        period_record(
            {"S": identity_stage, "T": identity_stage, "U": identity_stage},
            [{"S.a": "T.a"}, {"S.a": "U.a"}],
        )
    )


@pytest.fixture(scope="module")
def bare_and_keyed_claim_trellis(three_arrivals_at_a):
    """A trellis of one period where three stages arrive at `a`, whose bare
    connector `{a: T.a}` and connector in the keyed form from `S` to `U`
    both map `S`'s field `a`."""
    return trellis_of(
        period_record(
            three_arrivals_at_a,
            [{"a": "T.a"}, {"from": "S", "to": "U", "fields": {"a": "a"}}],
        )
    )


@pytest.fixture(scope="module")
def authored_cycle_trellis(identity_stage):
    """A trellis of one period of two stages that carry `a` unchanged, whose
    connectors join `S` to `T` and `T` to `S`."""
    return trellis_of(
        period_record(
            {"S": identity_stage, "T": identity_stage},
            [{"S.a": "T.a"}, {"T.a": "S.a"}],
        )
    )


@pytest.fixture(scope="module")
def self_pair_trellis(two_state_identity_stage):
    """A trellis of one period of the two-field stage `S`, whose connector
    maps its continuation field `a` to its own arrival field `b`."""
    return trellis_of(period_record({"S": two_state_identity_stage}, [{"S.a": "S.b"}]))


@pytest.fixture(scope="module")
def self_field_trellis(three_arrivals_at_a):
    """A trellis of one period where three stages arrive at `a`, whose
    connector maps `S`'s continuation field `a` to its own arrival field
    `a`."""
    return trellis_of(period_record(three_arrivals_at_a, [{"S.a": "S.a"}]))


@pytest.fixture(scope="module")
def three_unchanged_periods(identity_stage):
    """Three periods of stages that carry `a` unchanged: `T` and `U` in the
    terminal period, `S` alone in each of the two earlier ones."""
    return (
        period_record({"T": identity_stage, "U": identity_stage}),
        period_record({"S": identity_stage}),
        period_record({"S": identity_stage}),
    )


@pytest.fixture(scope="module")
def shared_connector_trellis(three_unchanged_periods):
    """The trellis of the three periods whose two inter-period connectors
    are both `{a: a}`."""
    return trellis_of(*three_unchanged_periods, inter_connectors=[{"a": "a"}, {"a": "a"}])


@pytest.fixture(scope="module")
def shared_connector_report(shared_connector_trellis):
    """The connection report of the trellis of the shared connector."""
    return connection_report(shared_connector_trellis)


@pytest.fixture(scope="module")
def shared_connector_periods(shared_connector_trellis):
    """The three periods of the trellis of the shared connector, the
    terminal one first."""
    return shared_connector_trellis["periods"]


@pytest.fixture(scope="module")
def qualified_connector_trellis(three_unchanged_periods):
    """The trellis of the three periods whose inter-period connector into
    the terminal period is `{a: T.a}` and whose other one is `{a: a}`."""
    return trellis_of(*three_unchanged_periods, inter_connectors=[{"a": "T.a"}, {"a": "a"}])


@pytest.fixture(scope="module")
def portfolio_disc():
    """The discounting stage of the portfolio-choice model, which continues
    to `a`, as the consumption stage does."""
    return elaborate_stage(load_stage(str(PORTFOLIO / "stages/disc/disc.bl")))


@pytest.fixture(scope="module")
def cons_port_period(cons, port, portfolio_disc):
    """A period of the stages `port`, `cons` and `disc`, whose connector
    joins `port`'s `m_next` to `cons`'s `m`."""
    return period_record({"port": port, "cons": cons, "disc": portfolio_disc}, [{"m_next": "m"}])


@pytest.fixture(scope="module")
def cons_port_period_twice(cons_port_period):
    """The cons-port period twice, as the later and the earlier period of a
    trellis."""
    return [cons_port_period, cons_port_period]


@pytest.fixture(scope="module")
def cons_port_trellis(cons_port_period):
    """The trellis of two cons-port periods, appended one after the other,
    whose inter-period connector is `{disc.a: k}`."""
    empty = {"periods": [], "inter_connectors": []}
    return accrete(accrete(empty, cons_port_period), cons_port_period, {"disc.a": "k"})


@pytest.fixture(scope="module")
def unresolved_cons_port_trellis(cons_port_trellis):
    """The trellis of two cons-port periods with the connector of
    `periods[1]` replaced by `{q: m}`, whose field `q` no stage continues
    to."""
    trellis = cons_port_trellis
    earlier = {**trellis["periods"][1], "connectors": [{"q": "m"}]}
    return {**trellis, "periods": [trellis["periods"][0], earlier]}


@pytest.fixture(scope="module")
def unproved_report():
    """The connection report, restricted to the terminal period, of a trellis
    of two periods: `S` continues to `a` in `[a_min, inf)` and `T`, which
    arrives at `a` in ℝ₊, continues to `y`, as `U` of the earlier period
    does."""
    bounded = stage_from_text(
        BOUNDED.replace("(a : [a_min, inf)) : !arvl", "(x : [a_min, inf)) : !arvl").replace(
            "a_d = a\n", "a_d = x\n"
        ),
        "bounded.bl",
    )
    other = stage_from_text(
        UNCHANGED.replace("(a : ℝ₊) : !cntn", "(y : ℝ₊) : !cntn").replace(
            "    a = a_d\n", "    y = a_d\n"
        ),
        "unchanged.bl",
    )
    trellis = elaborate_trellis(
        {
            "periods": [period_record({"S": bounded, "T": other}), period_record({"U": other})],
            "inter_connectors": [{}],
        }
    )
    return connection_report(trellis, periods=[0])


@pytest.fixture(
    scope="module",
    params=[("S.b", "T.q"), ("S.q", "T.b"), ("S.b", "b"), ("b", "T.b")],
    ids=[
        "arrival-names-no-field",
        "continuation-names-no-field",
        "arrival-names-two-fields",
        "continuation-names-two-fields",
    ],
)
def failed_second_entry_selection(request, two_state_identity_stage):
    """The selection of a period of two two-field stages whose connector maps
    `S.a` to `T.a` and holds a second entry, one side of which fails."""
    source, target = request.param
    stages = {"S": two_state_identity_stage, "T": two_state_identity_stage}
    return selection_of_periods([period_record(stages, [{"S.a": "T.a", source: target}])])


@pytest.fixture(scope="module")
def three_stage_cycle_selection(two_state_identity_stage, identity_stage):
    """The selection of a period whose connectors join `S` to `T`, `T` to the
    two-field stage `W` and `W` to `S`, all by the field `a`."""
    stages = {"S": identity_stage, "T": identity_stage, "W": two_state_identity_stage}
    connectors = [{"S.a": "T.a"}, {"W.a": "S.a"}, {"T.a": "W.a"}]
    return select_connections([period_record(stages, connectors)], [])


@pytest.fixture(scope="module")
def lone_stage_selection(two_state_identity_stage):
    """The selection of a period that holds the two-field stage `W` alone."""
    return selection_of_periods([period_record({"W": two_state_identity_stage})])


@pytest.fixture(scope="module")
def pension_selection(pension_trellis_with_arrival_builders):
    """The selection of the pension trellis."""
    return connection_report(pension_trellis_with_arrival_builders).selection


@pytest.fixture(scope="module")
def relay_stages():
    """The relay stages `A`, `B` and `C`, whose fields pair `A → B`, `B → C`,
    `C → A` and `A → C` by equal names."""
    return {
        "A": stage_from_text(relay_text("relay_a", ["ca"], ["ab", "ac"]), "relay_a.bl"),
        "B": stage_from_text(relay_text("relay_b", ["ab"], ["bc"]), "relay_b.bl"),
        "C": stage_from_text(relay_text("relay_c", ["ac", "bc"], ["ca"]), "relay_c.bl"),
    }


@pytest.fixture(scope="module")
def relay_with_authored_pair(relay_stages):
    """The selection of the period of the relay stages whose connector maps
    `A.ab` to `B.ab`."""
    return selection_of_periods([period_record(relay_stages, [{"A.ab": "B.ab"}])])


@pytest.fixture(scope="module")
def competing_stages(identity_stage, strictly_positive_identity_stage, bounded_identity_stage):
    """The stage occurrences of a period in which `T` arrives at `a` in ℝ₊,
    `S` continues to `a` in ℝ₊₊ and `U` continues to `a` in `[a_min, inf)`."""
    return {
        "S": strictly_positive_identity_stage,
        "T": identity_stage,
        "U": bounded_identity_stage,
    }


# Authored pairs and their endpoints


def test_the_pairs_of_a_crossed_connector_are_its_two_authored_pairs_alone(crossed_report):
    """The report of the crossed trellis holds the connector's two authored
    pairs, with no candidate, no diagnostic and no inferred pair."""
    assert [
        (str(p.writing), str(p.reading), p.origin, p.address) for p in crossed_report.pairs
    ] == [
        ("periods[0].S.a", "periods[0].T.b", "authored", "periods[0].connectors[0]"),
        ("periods[0].S.b", "periods[0].T.a", "authored", "periods[0].connectors[0]"),
    ]
    assert crossed_report.diagnostics == () and crossed_report.selection.candidates == ()
    assert crossed_report.counts["inferred"] == 0


@pytest.mark.parametrize(
    "connector, pairs",
    [
        pytest.param(
            {"a": "T.a"},
            [("periods[0].S.a", "periods[0].T.a", "periods[0].connectors[0]")],
            id="arrival-after-its-stage-key",
        ),
        pytest.param(
            {"from": "S", "to": "U", "fields": {"a": "a"}},
            [("periods[0].S.a", "periods[0].U.a", "periods[0].connectors[0]")],
            id="keyed-form",
        ),
    ],
)
def test_an_endpoint_after_its_stage_key_or_in_the_keyed_form_resolves_to_one_authored_pair(
    three_arrivals_at_a, connector, pairs
):
    """Where three stages arrive at `a`, the connector `{a: T.a}` and the
    connector in the keyed form from `S` to `U` each resolve to one authored
    pair."""
    selection = selection_of_periods([period_record(three_arrivals_at_a, [connector])])
    assert printed_pairs(selection) == pairs
    assert all(pair.origin == "authored" for pair in selection.pairs)


def test_the_stage_key_of_an_endpoint_is_all_that_stands_before_its_last_dot(
    two_state_identity_stage, identity_stage, disc_with_k_next
):
    """The endpoint `foo.bar.a` names the field `a` of the occurrence keyed
    `foo.bar`, beside the occurrence keyed `foo`, while `bar.a`, whose prefix
    is no key, resolves to nothing."""
    dotted = trellis_of(
        period_record(
            {"foo.bar": identity_stage, "foo": identity_stage, "T": two_state_identity_stage},
            [{"foo.bar.a": "T.a"}, {"foo.a": "T.b"}],
        )
    )
    assert period_joins(dotted["periods"][0], "periods[0]")["joins"] == [
        {"from": ("foo", "a"), "to": ("T", "b")},
        {"from": ("foo.bar", "a"), "to": ("T", "a")},
    ]
    # each source supplies one of T's two arrival fields, so that the routes
    # are incomplete, and no endpoint is diagnosed
    assert [d.rule for d in connection_report(dotted).diagnostics] == ["route-incomplete"] * 2
    missing = selection_of_periods(
        [period_record({"foo.bar": identity_stage, "T": disc_with_k_next}, [{"bar.a": "T.a"}])]
    )
    assert [d.rule for d in missing.diagnostics] == ["endpoint-unresolved"]


def test_a_bare_endpoint_that_three_stages_arrive_at_makes_no_pair_and_is_diagnosed(
    three_arrivals_at_a,
):
    """The connector `{a: a}` makes no pair where three stages arrive at
    `a`, and its diagnostic lists the three arrival fields and advises
    writing the stage key before the field."""
    ambiguous = selection_of_periods([period_record(three_arrivals_at_a, [{"a": "a"}])])
    assert printed_pairs(ambiguous) == []
    (diagnostic,) = ambiguous.diagnostics
    assert (diagnostic.rule, diagnostic.address) == (
        "endpoint-ambiguous",
        "periods[0].connectors[0]",
    )
    assert [str(use) for use in diagnostic.candidates] == [
        "periods[0].S.a",
        "periods[0].T.a",
        "periods[0].U.a",
    ]
    assert "S.a, T.a, U.a" in diagnostic.message and "`<key>.<field>`" in diagnostic.message


def test_an_endpoint_that_names_no_arrival_field_is_diagnosed_with_the_fields_there(
    three_arrivals_at_a,
):
    """The connector `{a: q}` is diagnosed as unresolved, its message saying
    that `q` names no arrival state field and listing the period's arrival
    field `a`."""
    absent = selection_of_periods([period_record(three_arrivals_at_a, [{"a": "q"}])])
    (diagnostic,) = absent.diagnostics
    assert (
        diagnostic.rule == "endpoint-unresolved"
        and "'q' names no arrival state field" in diagnostic.message
    )
    assert diagnostic.message.endswith("the arrival state fields there are a")


def test_an_authored_endpoint_whose_other_endpoint_fails_is_joined_by_no_inferred_pair(
    failed_second_entry_selection,
):
    """Where one side of the connector's second entry names no field or
    several, the selection keeps the authored pair of `a` alone, no inferred
    pair of `b` taking the place of the failed entry."""
    pairs = [
        (str(p.writing), str(p.reading), p.origin) for p in failed_second_entry_selection.pairs
    ]
    assert pairs == [("periods[0].S.a", "periods[0].T.a", "authored")]
    assert failed_second_entry_selection.diagnostics[0].rule in (
        "endpoint-unresolved",
        "endpoint-ambiguous",
    )


def test_the_route_of_a_connector_whose_second_entry_fails_is_incomplete_and_uncertified(
    failed_second_entry_selection,
):
    """The route from `S` to `T`, whose field `b` the failed entry leaves
    unmapped, is incomplete and uncertified."""
    assert failed_second_entry_selection.routes[0].state == "incomplete"
    assert failed_second_entry_selection.routes[0].status == "uncertified"


@pytest.mark.parametrize(
    "trellis, entries",
    [
        pytest.param(
            "duplicate_claim_trellis",
            (
                ("periods[0].connectors[0]", "S.a", "T.a"),
                ("periods[0].connectors[1]", "S.a", "U.a"),
            ),
            id="two-qualified-entries",
        ),
        pytest.param(
            "bare_and_keyed_claim_trellis",
            (
                ("periods[0].connectors[0]", "a", "T.a"),
                ("periods[0].connectors[1].fields", "a", "a"),
            ),
            id="a-bare-entry-and-the-keyed-form",
        ),
    ],
)
def test_a_continuation_field_that_two_entries_map_is_diagnosed_with_both_entries(
    request, trellis, entries
):
    """A continuation field of `S` that two connector entries map is
    diagnosed at the second entry as claimed twice, with both entries as
    written."""
    diagnostic = connection_report(request.getfixturevalue(trellis)).diagnostics[0]
    assert (diagnostic.rule, diagnostic.address) == (
        "use-claimed-twice",
        "periods[0].connectors[1]",
    )
    assert "both map the continuation field 'a' of S" in diagnostic.message
    assert diagnostic.source_entries == entries


def test_an_authored_chain_stands_and_excludes_each_inference_against_it(identity_stage):
    """With `S → T` and `T → U` authored on the field `a`, the two authored
    pairs stand and no candidate remains, the reverse inferences `T → S`,
    `U → T` and `U → S` all excluded."""
    stages = {"S": identity_stage, "T": identity_stage, "U": identity_stage}
    chain = selection_of_periods([period_record(stages, [{"S.a": "T.a"}, {"T.a": "U.a"}])])
    assert printed_pairs(chain) == [
        ("periods[0].S.a", "periods[0].T.a", "periods[0].connectors[0]"),
        ("periods[0].T.a", "periods[0].U.a", "periods[0].connectors[1]"),
    ]
    assert (
        candidate_groups(chain) == {}
        and chain.counts["cycles"] == 0
        and chain.counts["excluded"] >= 3
    )


# Authored cycles


@pytest.mark.parametrize(
    "trellis",
    [
        pytest.param("self_pair_trellis", id="to-another-field-of-the-stage"),
        pytest.param("self_field_trellis", id="to-the-same-field"),
    ],
)
def test_a_connector_from_a_stage_to_itself_is_diagnosed_as_an_authored_cycle(request, trellis):
    """A connector from a continuation field of a stage to an arrival field
    of the same stage is diagnosed as an authored cycle, since a stage
    cannot take a field it produces."""
    diagnostic = connection_report(request.getfixturevalue(trellis)).diagnostics[0]
    assert diagnostic.rule == "authored-cycle"
    assert "a stage cannot take a field it produces" in diagnostic.message


def test_two_connectors_in_opposite_directions_are_diagnosed_as_an_authored_cycle(
    authored_cycle_trellis,
):
    """The authored pairs from `S` to `T` and from `T` to `S` are diagnosed
    as an authored cycle."""
    report = connection_report(authored_cycle_trellis)
    assert "authored-cycle" in [d.rule for d in report.diagnostics]


def test_the_selector_keeps_the_three_pairs_of_an_authored_cycle_and_counts_one_cycle(
    three_stage_cycle_selection,
):
    """The selection of the three connectors that join `S` to `T`, `T` to
    `W` and `W` to `S` keeps the three authored pairs and counts one
    cycle."""
    selection = three_stage_cycle_selection
    assert len(selection.pairs) == 3 and selection.counts["cycles"] == 1


@pytest.mark.parametrize(
    "trellis, rule, address, phrase",
    [
        pytest.param(
            "duplicate_claim_trellis",
            "connector-names-no-field",
            "periods[0].connectors[1]",
            "both map the continuation field 'a' of S",
            id="a-field-that-two-entries-map",
        ),
        pytest.param(
            "authored_cycle_trellis",
            "period-join-cycle",
            "periods[0]",
            "S continues to 'a' and T arrives at 'a'; T continues to 'a' and S arrives at 'a'",
            id="two-stages-in-opposite-directions",
        ),
        pytest.param(
            "self_pair_trellis",
            "period-join-cycle",
            "periods[0].connectors[0]",
            "a stage cannot take a field it produces",
            id="a-stage-to-itself",
        ),
    ],
)
def test_the_forward_order_refuses_a_period_whose_connectors_it_cannot_order(
    request, trellis, rule, address, phrase
):
    """The forward order of a period whose connectors map one continuation
    field twice or form a cycle is refused, though the trellis holds the
    period, the phrase standing in the message and in the printed
    refusal."""
    period = request.getfixturevalue(trellis)["periods"][0]
    with pytest.raises(FactoryError, match=re.escape(phrase)) as refused:
        forward_order(period, "periods[0]")
    assert (refused.value.rule, refused.value.address) == (rule, address)
    assert phrase in refused.value.message


# Inferred pairs and candidates


def test_two_stages_that_carry_one_field_compete_in_both_directions_and_make_no_pair(
    identity_stage,
):
    """Two occurrences of a stage that carries `a` unchanged, with no
    connector, give one candidate in each direction, both rejected as a
    cycle, so that the name alone settles no direction and no diagnostic
    stands."""
    selection = selection_of_periods([period_record({"S": identity_stage, "T": identity_stage})])
    assert printed_pairs(selection) == []
    assert candidate_groups(selection) == {
        (0, "S"): {(0, "T"): [("a", "a", None)]},
        (0, "T"): {(0, "S"): [("a", "a", None)]},
    }
    assert (
        selection.diagnostics == () and selection.counts["cycles"] == 0 and selection.routes == ()
    )
    assert rejected_pairs(selection) == [
        ("periods[0].S.a", "periods[0].T.a", "inference-cycle"),
        ("periods[0].T.a", "periods[0].S.a", "inference-cycle"),
    ]


def test_two_stages_that_carry_one_field_with_no_connector_are_ordered_by_key(identity_stage):
    """The forward order of a period of two stages that carry `a` unchanged,
    with no connector, lists the stages by key, refusing nothing."""
    period = period_record({"T": identity_stage, "U": identity_stage})
    # the period joins neither stage to the other
    assert period_joins(period, "periods[0]")["joins"] == []
    assert forward_order(period, "periods[0]") == ["T", "U"]


def test_the_two_coordinates_that_one_source_offers_a_destination_form_one_candidate(
    pension_selection,
):
    """In the pension trellis, the candidates of `retire_choice` in
    `periods[1]` are one candidate of `worker_saving`, which continues to
    both `y_f` and `y_p`, with both coordinates; `retiree_saving`, whose
    continuation fields bear other names, offers none."""
    assert candidate_groups(pension_selection)[(1, "retire_choice")] == {
        (1, "worker_saving"): [("y_f", "y_f", None), ("y_p", "y_p", None)]
    }


def test_a_unique_compatible_candidate_is_selected_as_one_certified_route_of_inferred_pairs(
    pension_selection,
):
    """The candidate of `worker_saving` into `retire_choice` is selected as
    one certified route whose two pairs are inferred, with no source
    entry."""
    # the arguments: the selection, the source, its branch, None for a stage
    # that writes no branches, and the destination
    route = one_route(pension_selection, (1, "worker_saving"), None, (1, "retire_choice"))
    assert route.status == "certified" and [p.origin for p in route.pairs] == ["inferred"] * 2
    assert all(
        (p.source_address, p.source_key, p.source_value) == (None, None, None) for p in route.pairs
    )


def test_the_selection_of_the_pension_trellis_rejects_no_candidate(pension_selection):
    """The selection of the pension trellis rejects no candidate."""
    assert pension_selection.rejected == ()


@pytest.mark.parametrize(
    "order",
    [pytest.param(("A", "B", "C"), id="A-B-C"), pytest.param(("C", "B", "A"), id="C-B-A")],
)
def test_the_inferred_pairs_of_overlapping_cycles_are_all_withdrawn_in_either_order(
    relay_stages, order
):
    """The four pairs that equal names infer among the relay stages all lie
    on cycles among the three stages and are withdrawn, the message naming
    the three stages, whichever order the period lists them in."""
    selection = selection_of_periods([period_record({key: relay_stages[key] for key in order})])
    assert (
        selection.pairs == ()
        and selection.routes == ()
        and rejected_pairs(selection)
        == [
            ("periods[0].A.ab", "periods[0].B.ab", "inference-cycle"),
            ("periods[0].A.ac", "periods[0].C.ac", "inference-cycle"),
            ("periods[0].B.bc", "periods[0].C.bc", "inference-cycle"),
            ("periods[0].C.ca", "periods[0].A.ca", "inference-cycle"),
        ]
    )
    assert all("among the stages A, B, C" in r.message for r in selection.rejected)


def test_an_authored_pair_on_overlapping_cycles_stands_while_the_inferred_pairs_are_withdrawn(
    relay_with_authored_pair,
):
    """With `A.ab` mapped to `B.ab`, the authored pair stands and the three
    inferred pairs, which still lie on cycles, are withdrawn."""
    selection = relay_with_authored_pair
    assert printed_pairs(selection) == [
        ("periods[0].A.ab", "periods[0].B.ab", "periods[0].connectors[0]")
    ]
    assert (
        rejected_pairs(selection)
        == [
            ("periods[0].A.ac", "periods[0].C.ac", "inference-cycle"),
            ("periods[0].B.bc", "periods[0].C.bc", "inference-cycle"),
            ("periods[0].C.ca", "periods[0].A.ca", "inference-cycle"),
        ]
        and selection.counts["cycles"] == 0
    )


def test_a_route_that_maps_one_of_two_continuation_fields_is_incomplete_and_uncertified(
    relay_with_authored_pair,
):
    """The route of the authored pair, which maps one of `A`'s two
    continuation fields onto `B`'s one arrival field, is incomplete and
    uncertified, its obligations naming the field `ac` that it leaves
    unmapped."""
    (route,) = relay_with_authored_pair.routes
    assert (route.state, route.status, route.permutation) == ("incomplete", "uncertified", ())
    assert any(
        "the continuation coordinate ac of periods[0].A is mapped to no arrival coordinate" in said
        for said in route.obligations
    )


def test_a_bound_without_a_value_leaves_both_candidates_into_one_arrival_disputed(
    competing_stages,
):
    """Read with no value of `a_min`, neither `S`'s nor `U`'s candidate into
    `T` is selected: both are rejected as disputed, the message naming the
    bound that has no value."""
    selection = selection_of_periods([period_record(competing_stages)])
    assert selection.pairs == ()
    disputed = [
        (str(r.writing), str(r.reading), r.rule)
        for r in selection.rejected
        if r.reading.key == "T"
    ]
    assert sorted(disputed) == [
        ("periods[0].S.a", "periods[0].T.a", "inference-disputed"),
        ("periods[0].U.a", "periods[0].T.a", "inference-disputed"),
    ]
    (message,) = {r.message for r in selection.rejected if r.reading.key == "T"}
    assert "periods[0].U.a (not established: " in message and "a_min of periods[0].U" in message


def test_a_value_of_the_bound_that_makes_both_candidates_compatible_leaves_them_disputed(
    competing_stages,
):
    """At `a_min = 0`, where `U`'s field lies in ℝ₊ as `T`'s does, the two
    candidates still compete, and neither is selected."""
    valued = select_connections([period_record(competing_stages)], [], {(0, "U"): {"a_min": 0.0}})
    assert valued.pairs == () and all(
        r.rule == "inference-disputed" for r in valued.rejected if r.reading.key == "T"
    )


def test_a_value_of_the_bound_that_makes_a_candidate_incompatible_selects_the_other(
    competing_stages,
):
    """At `a_min = -1`, where `U`'s field may be negative, `S`'s candidate
    alone remains, and it is selected and certified."""
    excluded = select_connections(
        [period_record(competing_stages)], [], {(0, "U"): {"a_min": -1.0}}
    )
    assert [(str(p.writing), str(p.reading)) for p in excluded.pairs] == [
        ("periods[0].S.a", "periods[0].T.a")
    ]
    assert excluded.counts["certified"] == 1


def test_a_candidate_that_a_symbolic_bound_leaves_unproved_is_rejected_naming_the_bound(
    unproved_report,
):
    """The candidate from `S`'s field in `[a_min, inf)` to `T`'s in ℝ₊,
    which is not established while `a_min` has no value, is rejected as not
    established, its message naming `a_min`, and no pair or diagnostic
    stands."""
    assert unproved_report.pairs == () and unproved_report.diagnostics == ()
    assert [(r.rule, str(r.writing), str(r.reading)) for r in unproved_report.rejected] == [
        ("candidate-not-established", "periods[0].S.a", "periods[0].T.a")
    ]
    assert "a_min" in unproved_report.rejected[0].message


def test_the_printed_report_names_its_rejected_inferences(unproved_report):
    """The printed connection report holds a line on its rejected
    inferences."""
    assert "rejected inference" in str(unproved_report)


@pytest.mark.parametrize(
    "selection",
    [
        pytest.param("three_stage_cycle_selection", id="in-an-authored-cycle"),
        pytest.param("lone_stage_selection", id="alone-in-its-period"),
    ],
)
def test_each_field_of_a_stage_is_listed_twice_among_the_uses_of_the_selection(request, selection):
    """The uses of a selection list each of the fields `a` and `b` of the
    stage `W` twice, whether `W` is joined in a cycle or alone in its
    period."""
    uses = request.getfixturevalue(selection).uses
    assert [str(use) for use in uses if use.key == "W"] == [
        "periods[0].W.a",
        "periods[0].W.b",
        "periods[0].W.a",
        "periods[0].W.b",
    ]


def test_a_stage_alone_in_its_period_makes_no_pair_no_candidate_and_no_diagnostic(
    lone_stage_selection,
):
    """A stage that no other stage joins is no fault of the selection: it
    makes no pair, no candidate and no diagnostic."""
    selection = lone_stage_selection
    assert selection.pairs == () and selection.candidates == () and selection.diagnostics == ()


# The records of the selection


def test_the_selection_records_a_digest_of_each_calibration_given_and_none_where_none_is(
    identity_stage,
):
    """The selection records under `bindings`, by position, a digest of 64
    characters for each calibration given, or None for a position given
    none, and records nothing where no calibration is given."""
    periods = [period_record({"S": identity_stage, "T": identity_stage}, [{"S.a": "T.a"}])]
    # the calibration of S gives β a value in its set (0, 1); T is given none
    selection = select_connections(periods, [], {(0, "S"): {"β": 0.9}, (0, "T"): None})
    assert set(selection.bindings) == {(0, "S"), (0, "T")}
    assert selection.bindings[(0, "T")] is None and len(selection.bindings[(0, "S")]) == 64
    assert select_connections(periods, []).bindings == {}


def test_the_selection_changes_none_of_the_periods_that_it_is_given(identity_stage):
    """The selection leaves the periods it is given, their stages and their
    connectors, as they were."""
    periods = [period_record({"S": identity_stage, "T": identity_stage}, [{"S.a": "T.a"}])]
    before = deepcopy(periods)
    select_connections(periods, [], {(0, "S"): {"β": 0.9}, (0, "T"): None})
    assert periods == before


# The joins and the order of a period


def test_the_joins_of_a_period_are_the_pairs_of_its_crossed_connector(crossed_trellis):
    """The joins of the crossed period run along the connector's two crossed
    pairs, the continuation fields of `T` leaving the period."""
    assert period_joins(crossed_trellis["periods"][0], "periods[0]") == {
        "joins": [
            {"from": ("S", "a"), "to": ("T", "b")},
            {"from": ("S", "b"), "to": ("T", "a")},
        ],
        "outputs": [("T", "a"), ("T", "b")],
    }


def test_a_period_whose_connector_resolves_to_no_pair_has_no_join(unfinished_trellis):
    """The earlier period of the unfinished trellis, whose one connector
    resolves to no pair, has no join, so that each of its continuation
    fields leaves it."""
    assert period_joins(unfinished_trellis["periods"][1], "periods[1]") == {
        "joins": [],
        "outputs": [("S", "a"), ("S", "b"), ("U", "a")],
    }


# each inter-period connector `inter_connectors[h]`, the fixture of the
# periods that it joins, `h`, and the joins that it makes; the connector names
# continuation fields of `periods[h + 1]` and arrival fields of `periods[h]`
INTER_PERIOD_JOINS = [
    pytest.param(
        {"a": "k"}, "cons_port_period_twice", 0, [], id="a-name-that-two-stages-continue-to"
    ),
    pytest.param(
        {"disc.a": "k"},
        "cons_port_period_twice",
        0,
        [{"from": ("disc", "a"), "to": ("port", "k")}],
        id="the-same-name-after-its-stage-key",
    ),
    pytest.param(
        {"a": "a"}, "shared_connector_periods", 0, [], id="a-name-that-two-stages-arrive-at"
    ),
    pytest.param(
        {"a": "a"},
        "shared_connector_periods",
        1,
        [{"from": ("S", "a"), "to": ("S", "a")}],
        id="a-name-that-one-stage-arrives-at",
    ),
    pytest.param(
        {"a": "a", "b": "b"},
        "unfinished_periods",
        0,
        [],
        id="names-that-two-stages-continue-to-and-arrive-at",
    ),
]


@pytest.mark.parametrize("connector, periods, h, joins", INTER_PERIOD_JOINS)
def test_an_inter_period_connector_joins_a_name_only_where_it_names_one_field_on_each_side(
    request, connector, periods, h, joins
):
    """An inter-period connector joins a field only where its name, bare or
    after its stage key, names one continuation field of the earlier period
    and one arrival field of the later one."""
    held = request.getfixturevalue(periods)
    address = f"inter_connectors[{h}]"
    assert inter_period_joins(connector, held[h + 1], held[h], address) == joins


def test_a_connector_shared_by_each_pair_of_periods_is_diagnosed_where_its_name_is_ambiguous(
    shared_connector_report,
):
    """The inter-period connector `{a: a}`, written for each pair of adjacent
    periods, is diagnosed at the pair whose later period holds two stages
    that arrive at `a`, the message naming that pair and both fields."""
    (diagnostic,) = shared_connector_report.diagnostics
    assert (diagnostic.rule, diagnostic.address) == ("endpoint-ambiguous", "inter_connectors[0]")
    assert "periods[1] → periods[0]" in diagnostic.message and "T.a, U.a" in diagnostic.message


def test_a_connector_shared_by_each_pair_of_periods_makes_its_pair_where_its_name_is_unique(
    shared_connector_report,
):
    """The same connector makes the one pair from `S` to `S` between the two
    earlier periods, where one stage arrives at `a`."""
    assert [(str(p.writing), str(p.reading)) for p in shared_connector_report.pairs] == [
        ("periods[2].S.a", "periods[1].S.a")
    ]


def test_a_connector_qualified_where_its_name_was_ambiguous_leaves_one_inferred_pair(
    qualified_connector_trellis,
):
    """With the inter-period connector into the terminal period written
    `{a: T.a}`, both inter-period connectors make their pairs, and `T`'s
    arrival field, now authored, leaves the pair from `T` to `U` the one
    candidate within the terminal period, inferred, the three routes
    certified with no diagnostic."""
    qualified = connection_report(qualified_connector_trellis)
    assert [(str(p.writing), str(p.reading), p.origin) for p in qualified.pairs] == [
        ("periods[1].S.a", "periods[0].T.a", "authored"),
        ("periods[2].S.a", "periods[1].S.a", "authored"),
        ("periods[0].T.a", "periods[0].U.a", "inferred"),
    ]
    assert qualified.diagnostics == () and qualified.counts["certified"] == 3


def test_a_field_mapped_both_in_its_period_and_by_an_inter_period_connector_is_claimed_twice(
    cons_port_period,
):
    """The field `m_next` of `port`, which the period's connector maps, makes
    no join when an inter-period connector maps it too, and the strict
    selection refuses that second claim."""
    period = cons_port_period
    assert inter_period_joins({"m_next": "m"}, period, period, "inter_connectors[0]") == []
    # the arguments: the periods, the terminal one first, the inter-period
    # connectors, and the index of the first period
    with pytest.raises(FactoryError) as refused:
        checked_selection([period, period], [{"m_next": "m"}], 0)
    assert (refused.value.rule, refused.value.address) == (
        "connector-names-no-field",
        "inter_connectors[0]",
    )
    assert (
        "periods[1].connectors[0] and inter_connectors[0] both map the continuation field "
        "'m_next' of port" in refused.value.message
    )


def test_the_drawing_of_a_trellis_names_its_inter_period_connector_once(cons_port_trellis):
    """The drawing of the trellis of two cons-port periods names the address
    of its one inter-period connector once."""
    assert diagram_trellis(cons_port_trellis).source.count("inter_connectors[0]") == 1


# Routes


def test_the_route_of_a_crossed_connector_is_certified_with_the_permutation_of_its_fields(
    crossed_report,
):
    """The one route of the crossed connector, from `S` to `T`, is certified
    with the permutation `(1, 0)`, which is its own inverse, and carries the
    measure at `S`'s continuation perch as its law."""
    (route,) = crossed_report.routes
    assert (route.source, route.destination, route.status) == ((0, "S"), (0, "T"), "certified")
    assert route.permutation == (1, 0) and route.inverse == (1, 0)
    assert route.law == "two_fields:measure:cntn"
    assert crossed_report.counts["certified"] == 1


def test_a_crossed_route_leaves_no_join_unpaired(crossed_trellis):
    """No join of the backward graph of the crossed trellis leaves a wire
    unpaired."""
    assert unpaired_joins(crossed_trellis) == ()


def test_the_route_of_a_continuation_field_that_two_entries_map_is_not_certified(
    duplicate_claim_trellis,
):
    """The route from `S`, whose field `a` two entries map, stands
    uncertified."""
    route = connection_report(duplicate_claim_trellis).routes[0]
    assert route.source == (0, "S")
    assert route.status == "uncertified"


def test_an_authored_pair_into_a_narrower_set_stands_incompatible_with_its_reason(
    incompatible_pair_report,
):
    """An authored pair from a field in ℝ₊ into a field in ℝ₊₊ stands,
    marked incompatible, with the reason that ℝ₊ does not lie in ℝ₊₊."""
    (pair,) = incompatible_pair_report.pairs
    assert (pair.compatibility, pair.origin) == ("incompatible", "authored")
    assert "ℝ₊, does not lie in" in pair.reason


def test_an_incompatible_authored_pair_is_diagnosed_for_the_pair_and_for_its_route(
    incompatible_pair_report,
):
    """The report diagnoses the incompatible authored pair once for the pair
    and once for its route."""
    assert [d.rule for d in incompatible_pair_report.diagnostics] == [
        "pair-incompatible",
        "route-incompatible",
    ]


# The report of an unfinished trellis


def test_the_report_of_an_unfinished_trellis_lists_each_endpoint_that_does_not_resolve(
    unfinished_report,
):
    """The report of the unfinished trellis lists, at each entry's address,
    one diagnostic for each endpoint that names several fields or none."""
    assert [(d.rule, d.address) for d in unfinished_report.diagnostics] == [
        ("endpoint-ambiguous", "periods[1].connectors[0]"),
        ("endpoint-unresolved", "periods[1].connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
    ]


def test_an_endpoint_that_two_stages_continue_to_is_diagnosed_with_both_candidate_uses(
    unfinished_report,
):
    """The diagnostic of the bare name `a`, which both stages of the earlier
    period continue to, lists both uses as candidates."""
    ambiguous = unfinished_report.diagnostics[0]
    assert [str(use) for use in ambiguous.candidates] == ["periods[1].S.a", "periods[1].U.a"]


def test_both_diagnostics_of_one_connector_entry_keep_the_entry_as_written(unfinished_report):
    """The two diagnostics of the connector `{a: q}` each keep that entry, at
    its address, as written."""
    ambiguous, unresolved = unfinished_report.diagnostics[:2]
    assert (
        ambiguous.source_entries
        == unresolved.source_entries
        == (("periods[1].connectors[0]", "a", "q"),)
    )


def test_an_endpoint_that_names_no_field_is_diagnosed_in_a_sentence_naming_its_period(
    unfinished_report,
):
    """The diagnostic of `q` says that it names no arrival state field of
    `periods[1]`."""
    unresolved = unfinished_report.diagnostics[1]
    assert "'q' names no arrival state field of periods[1]" in unresolved.message


def test_an_ambiguous_inter_period_connector_is_diagnosed_naming_its_pair_of_periods(
    unfinished_report,
):
    """The diagnostic of the inter-period connector names the pair of
    periods that it joins."""
    assert "the pair periods[1] → periods[0]" in unfinished_report.diagnostics[2].message


def test_an_unfinished_trellis_keeps_the_pairs_and_the_route_of_its_resolved_connector(
    unfinished_report,
):
    """The unfinished trellis keeps the two pairs and the one route of the
    crossed connector of its later period."""
    assert len(unfinished_report.pairs) == 2 and len(unfinished_report.routes) == 1


def test_a_report_restricted_to_a_period_is_read_from_the_selection_of_the_whole_trellis(
    unfinished_report, unfinished_restricted_report
):
    """The report restricted to the earlier period has the counts and the
    selection of the report of the whole trellis."""
    restricted = unfinished_restricted_report
    assert restricted.counts == unfinished_report.counts
    assert restricted.selection == unfinished_report.selection


def test_a_report_restricted_to_a_period_holds_the_pairs_and_diagnostics_that_reach_it(
    unfinished_restricted_report,
):
    """The report restricted to the earlier period holds none of the pairs of
    the later period and each of the five diagnostics, which all stand at
    the earlier period or at the inter-period connector that leaves it."""
    restricted = unfinished_restricted_report
    assert restricted.pairs == () and len(restricted.diagnostics) == 5


# each restricted report and its open fields on each side, the continuation
# fields that no join reads and the arrival fields that no join reaches; the
# whole trellis holds open fields of other periods
@pytest.mark.parametrize(
    "report, fields",
    [
        pytest.param(
            "unfinished_restricted_report",
            {
                "writing": [(1, "S", "a"), (1, "S", "b"), (1, "U", "a")],
                "reading": [(1, "S", "a"), (1, "S", "b"), (1, "U", "a")],
            },
            id="unfinished-trellis-at-its-earlier-period",
        ),
        pytest.param(
            "unproved_report",
            {
                "writing": [(0, "S", "a"), (0, "T", "y")],
                "reading": [(0, "S", "x"), (0, "T", "a")],
            },
            id="unproved-candidate-at-the-terminal-period",
        ),
    ],
)
def test_a_report_restricted_to_a_period_holds_only_the_unjoined_fields_of_that_period(
    request, report, fields
):
    """The open fields of a report restricted to one period, on each side,
    are those of that period alone."""
    unjoined = request.getfixturevalue(report).unjoined
    held = {
        side: sorted(field for scope in unjoined.values() for field in scope[side])
        for side in ("writing", "reading")
    }
    assert held == fields


def test_the_report_places_an_open_field_of_an_earlier_period_inside_and_at_the_exterior(
    unfinished_report,
):
    """The report counts the continuation field `a` of `U`, which the later
    period could read, as an internal open field, and its arrival field, in
    the earliest period, as an exterior one."""
    assert (1, "U", "a") in unfinished_report.unjoined["internal"]["writing"]
    assert (1, "U", "a") in unfinished_report.unjoined["exterior"]["reading"]


def test_the_report_tells_an_open_field_inside_the_trellis_from_one_at_its_exterior(
    unproved_report,
):
    """The arrival field `a` of `T`, which the earlier period could reach,
    is an internal open field, and the continuation field `a` of `S` in the
    terminal period an exterior one."""
    assert (0, "T", "a") in unproved_report.unjoined["internal"]["reading"]
    assert (0, "S", "a") in unproved_report.unjoined["exterior"]["writing"]


@pytest.mark.parametrize(
    "connectors",
    [
        pytest.param(
            [{"from": "S", "to": "T", "fields": {"a": "b"}, "label": "x"}],
            id="keyed-form-with-a-key-that-it-does-not-admit",
        ),
        pytest.param(["S.a: T.a"], id="text-in-place-of-a-mapping"),
    ],
)
def test_a_connector_of_no_admitted_shape_refuses_the_construction(
    two_state_identity_stage, renamed_two_fields, connectors
):
    """A connector that is neither a flat mapping of endpoints nor in the
    keyed form of the admitted keys refuses the construction of the trellis
    under the rule `connector-names-no-field`."""
    with pytest.raises(FactoryError) as refused:
        trellis_of(
            period_record({"S": two_state_identity_stage, "T": renamed_two_fields}, connectors)
        )
    assert refused.value.rule == "connector-names-no-field"


def test_a_period_whose_stage_text_does_not_parse_refuses_the_construction():
    """A period whose stage text does not parse refuses the construction of
    the trellis under the rule `syntax`."""
    record = {"stage": {"text": "@stage: bad\n[id=x", "origin": "bad.bl"}}
    with pytest.raises(ConstructionError) as refused:
        trellis_of(
            period_record({"bad": {**record, "calibration": {}, "settings": {}, "methods": {}}})
        )
    assert refused.value.rule == "syntax"


def test_an_unfinished_trellis_is_drawn_with_a_box_for_each_occurrence(unfinished_trellis):
    """The drawing of the unfinished trellis of two periods of two stages
    holds four boxes."""
    assert repr(diagram_trellis(unfinished_trellis)) == "Drawing of 4 boxes"


def test_a_connector_that_names_no_field_is_drawn_with_as_many_boxes_as_the_trellis(
    cons_port_trellis, unresolved_cons_port_trellis
):
    """The trellis of two cons-port periods whose connector of `periods[1]`
    names no field is drawn, refusing nothing, with as many boxes as the
    trellis whose connector resolves."""
    assert repr(diagram_trellis(unresolved_cons_port_trellis)) == repr(
        diagram_trellis(cons_port_trellis)
    )


def test_the_report_lists_a_connector_endpoint_that_names_no_field_at_its_address(
    unresolved_cons_port_trellis,
):
    """The report of the trellis of two cons-port periods whose connector of
    `periods[1]` names no field lists the unresolved endpoint at that
    connector's address, beside the incomplete route of the connector of
    `periods[0]`."""
    diagnostics = connection_report(unresolved_cons_port_trellis).diagnostics
    assert [(item.rule, item.address) for item in diagnostics] == [
        ("endpoint-unresolved", "periods[1].connectors[0]"),
        ("route-incomplete", "periods[0].connectors[0]"),
    ]


# The view in Model Explorer


@needs_viewer
def test_the_backward_value_port_of_a_crossed_route_names_its_joins_and_its_pairing_rule(
    crossed_view,
):
    """The port of `S`'s continuation value in the backward graph names the
    two crossed joins and the rule of equal names, which pairs `V` before
    any wire is paired as the one left on each side, and no compatibility,
    since the route is compatible."""
    backward = port_attributes(crossed_view, "backward")["periods[0]/S/two_fields:function:cntn:V"]
    assert (backward["join"], backward["paired by"]) == ("a → b; b → a", "equal name")
    assert "compatibility" not in backward


@needs_viewer
def test_the_forward_measure_port_of_a_crossed_route_names_its_joins(crossed_view):
    """The port of `T`'s arrival measure in the forward graph names the two
    crossed joins."""
    forward = port_attributes(crossed_view, "forward")
    assert forward["periods[0]/T/two_t:measure:arvl"]["join"] == "a → b; b → a"


@needs_viewer
def test_the_arrival_measure_port_of_an_incompatible_route_shows_that_it_is_incompatible(
    incompatible_pair_trellis,
):
    """The port of the arrival measure that the incompatible route reaches,
    in the forward graph, shows the compatibility `incompatible`."""
    measure = port_attributes(to_model_explorer(incompatible_pair_trellis), "forward")
    assert measure["periods[0]/T/positive:measure:arvl"]["compatibility"] == "incompatible"


@needs_viewer
def test_each_graph_of_the_view_of_an_unfinished_trellis_is_drawn(unfinished_trellis):
    """Each graph of the view of the unfinished trellis, drawn with its
    unjoined fields, holds more than one node, where a refused graph holds
    one."""
    view = to_model_explorer(unfinished_trellis, unjoined=True)
    assert all(len(graph.nodes) > 1 for graph in view.graphs)


# The fields that no join reaches


def test_a_field_that_a_failed_connector_leaves_open_is_unjoined_on_both_sides(
    unfinished_trellis,
):
    """The field `a` of `U` in the earlier period of the unfinished trellis,
    which the failed connector leaves open, is among both the continuation
    and the arrival fields that no join reaches."""
    unjoined = unjoined_fields(unfinished_trellis)
    assert (1, "U", "a") in unjoined["writing"] and (1, "U", "a") in unjoined["reading"]


def test_each_arrival_field_that_a_join_reaches_keeps_the_address_of_its_connector(
    unfinished_trellis,
):
    """In the unfinished trellis, each arrival field that a join reaches
    keeps the address of the connector that writes the join."""
    assert unjoined_fields(unfinished_trellis)["sources"] == {
        (0, "T", "a"): ("periods[0].connectors[0]",),
        (0, "T", "b"): ("periods[0].connectors[0]",),
    }


def test_unjoined_fields_names_the_ends_of_the_cons_port_trellis_and_the_source_of_each_join(
    tmp_path,
):
    """In the trellis of `trellis.port-cons-vfi.yml`, no join reads `disc`'s
    continuation field `a` in the terminal period or reaches `port`'s
    arrival field `k` in the earliest, and each other arrival field keeps
    the address of the entry that writes its join: `cons`'s `m` the
    period's connector, `port`'s `k` the inter-period connector, and
    `disc`'s `a`, joined by equal names, none."""
    _, complete = declarations_copy(tmp_path / "complete")
    # the trellis has six periods, `periods[0]` to `periods[5]`, and five
    # inter-period connectors between them
    assert unjoined_fields(specify_trellis(load_trellis(complete))) == {
        "writing": [(0, "disc", "a")],
        "reading": [(5, "port", "k")],
        "sources": {
            **{(h, "cons", "m"): (f"periods[{h}].connectors[0]",) for h in range(6)},
            **{(h, "disc", "a"): (None,) for h in range(6)},
            **{(h, "port", "k"): (f"inter_connectors[{h}]",) for h in range(5)},
        },
    }


def test_with_its_connector_and_inter_period_connector_emptied_each_period_leaves_four_fields(
    tmp_path,
):
    """With the connector `{w: m}` and the inter-period connector
    `{disc.a: k}` emptied, every period leaves `disc`'s `a` and `port`'s `w`
    unread and `cons`'s `m` and `port`'s `k` unreached, and `disc`'s `a`
    alone is reached, by equal names."""
    emptied = specify_trellis(
        load_trellis(port_cons_vfi_trellis_file_without_connectors(tmp_path / "emptied"))
    )
    # the trellis has six periods, `periods[0]` to `periods[5]`
    assert unjoined_fields(emptied) == {
        "writing": sorted(
            (h, key, field) for h in range(6) for key, field in (("disc", "a"), ("port", "w"))
        ),
        "reading": sorted(
            (h, key, field) for h in range(6) for key, field in (("cons", "m"), ("port", "k"))
        ),
        "sources": {(h, "disc", "a"): (None,) for h in range(6)},
    }
