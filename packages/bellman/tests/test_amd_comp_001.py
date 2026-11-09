"""The acceptance file of AMD-COMP-001 (stage-local names and connections),
six items through the public operations alone: `elaborate_trellis`,
`specify_trellis`, `calibrate_trellis` and `load_recipe`; the joins
`period_joins`, `forward_order`, `inter_period_joins` and `unjoined_fields`;
`connection_report` and the five transports; `diagram_trellis`,
`to_model_explorer` and `unpaired_joins`; and `connector_entry`. The stages
are the texts `conftest.py` writes for the amendment and registries written
under a temporary folder from them; no test reads a private helper. The
behaviour and refusal files hold the finer claims of runs 2 and 3 (the lean
implementation rule: one acceptance file per amendment, at most six items).
"""

from pathlib import Path

import pytest
from conftest import BOUNDED, DISC_TEXT, TWO_FIELDS, UNCHANGED, stage_from_text

import bellman.factory.connections as connections_module
import bellman.factory.file_entries as entries_module
import bellman.factory.joins as joins_module
import bellman.factory.trellis as trellis_module
from bellman.factory.file_entries import connector_entry
from bellman.factory.joins import forward_order, inter_period_joins, period_joins, unjoined_fields
from bellman.native.provenance import source_description
from bellman.refusals import ConstructionError, FactoryError
from bellman.trellis import (
    calibrate_trellis,
    connection_report,
    diagram_trellis,
    elaborate_trellis,
    load_recipe,
    pull_back,
    specify_trellis,
    to_model_explorer,
    transport_atoms,
    transport_hessian,
    transport_point,
    transport_vector,
    unpaired_joins,
)


def period(stages, connectors=()):
    """One period of the stage occurrences `stages`, by key, with its
    authored connectors."""
    return {"stages": dict(stages), "connectors": list(connectors)}


def trellis_of(*periods, inter_connectors=()):
    """The elaborated trellis of the periods given, `periods[0]` first."""
    return elaborate_trellis({"periods": list(periods), "inter_connectors": list(inter_connectors)})


def written(folder, files):
    """The files `files`, by relative path, written under `folder`, which is
    answered."""
    for relative, text in files.items():
        path = Path(folder) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return Path(folder)


def renamed(text, name):
    """The stage text `text` with its stage named `name`."""
    _, rest = text.split("\n", 1)
    return f"@stage: {name}\n{rest}"


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


@pytest.fixture(scope="module")
def two_fields():
    return stage_from_text(TWO_FIELDS, "two_fields.bl")


@pytest.fixture(scope="module")
def two_t():
    return stage_from_text(renamed(TWO_FIELDS, "two_t"), "two_t.bl")


@pytest.fixture(scope="module")
def unchanged():
    return stage_from_text(UNCHANGED, "unchanged.bl")


# the registry of the drags: three periods of a two-field stage `s`, the
# unchanged-field stage `u` and the discounting stage `d`, one empty
# connector in the period file and one empty inter-period mapping
REGISTRY = {
    "stages/s/s.bl": renamed(TWO_FIELDS, "s"),
    "stages/u/u.bl": renamed(UNCHANGED, "u"),
    "stages/d/d.bl": DISC_TEXT,
    "calibration/main.yml": "calibration:\n  β: 0.96\n",
    "period.yml": "name: p\nstages: [s, u, d]\nconnectors:\n  - {}\n",
    "trellis.yml": "periods:\n  - {template: period.yml, repeat: 3}\ninter_connectors:\n  - {}\n",
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n"
        "  s: {stage: stages/s/s.bl, calibration: {all: [calibration/main]}}\n"
        "  u: {stage: stages/u/u.bl, calibration: {all: [calibration/main]}}\n"
        "  d: {stage: stages/d/d.bl, calibration: {all: [calibration/main]}}\n"
    ),
}

# the registry of the bindings: a terminal period of one bounded stage `b1`
# and an earlier period of a second, `b2`, beside an unchanged-field stage
# `u2` that shares `β` with it; the bound `a_min` is one parameter of each
# period and two parameters of the trellis
BOUNDED_REGISTRY = {
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


def test_item_1_the_crossed_pairs_suppress_the_straight_inference_and_the_route_transports(
    two_fields, two_t
):
    """The simultaneous swap `{S.a: T.b, S.b: T.a}` (amendment §3.1, §5): the
    report of the elaborated trellis holds the two authored pairs and no
    inferred one, the straight same-name pairs claimed; the joins and the
    forward order follow them; the one route is certified with the
    permutation `(1, 0)`, and transports a point, the components a
    destination supplies, both indices of an authored Hessian, the atoms of
    a measure with their masses summed on one image, and the pullback of a
    function; the Model Explorer draws the backward value wire and the
    forward measure wire from that route, naming the joins and the rule."""
    swap = period({"S": two_fields, "T": two_t}, [{"S.a": "T.b", "S.b": "T.a"}])
    trellis = trellis_of(swap)
    report = connection_report(trellis)
    assert [(str(p.writing), str(p.reading), p.origin, p.address) for p in report.pairs] == [
        ("periods[0].S.a", "periods[0].T.b", "authored", "periods[0].connectors[0]"),
        ("periods[0].S.b", "periods[0].T.a", "authored", "periods[0].connectors[0]"),
    ]
    assert report.diagnostics == () and report.selection.candidates == ()
    assert report.counts["inferred"] == 0 and report.counts["certified"] == 1
    assert period_joins(trellis["periods"][0], "periods[0]") == {
        "joins": [
            {"from": ("S", "a"), "to": ("T", "b")},
            {"from": ("S", "b"), "to": ("T", "a")},
        ],
        "outputs": [("T", "a"), ("T", "b")],
    }
    assert forward_order(trellis["periods"][0], "periods[0]") == ["S", "T"]
    (route,) = report.routes
    assert (route.source, route.destination, route.status) == ((0, "S"), (0, "T"), "certified")
    assert route.permutation == (1, 0) and route.inverse == (1, 0)
    assert route.law == "two_fields:measure:cntn"
    assert transport_point(route, (1, 2)) == (2, 1)
    assert transport_vector(route, ("g_a", "g_b")) == ("g_b", "g_a")
    assert transport_hessian(route, ((2, 1), (1, 4))) == ((4, 1), (1, 2))
    atoms = (((1, 2), 0.25), ((2, 1), 0.5), ((3, 4), 0.25))
    assert transport_atoms(route, atoms) == (((2, 1), 0.25), ((1, 2), 0.5), ((4, 3), 0.25))
    assert transport_atoms(route, (((1, 2), 0.25), ((1, 2), 0.5))) == (((2, 1), 0.75),)
    assert pull_back(route, lambda a, b: a - 2 * b)(1, 2) == 0
    with pytest.raises(ValueError, match="has 2 entries; 1 given"):
        transport_point(route, (1,))
    view = to_model_explorer(trellis)
    backward = port_attributes(view, "backward")["periods[0]/S/two_fields:function:cntn:V"]
    assert (backward["join"], backward["paired by"]) == ("a → b; b → a", "one wire per role")
    assert "compatibility" not in backward
    forward = port_attributes(view, "forward")
    assert forward["periods[0]/T/two_t:measure:arvl"]["join"] == "a → b; b → a"
    assert unpaired_joins(trellis) == ()


def test_item_2_a_refused_authored_connector_leaves_a_drawable_draft_with_its_diagnostic(
    two_fields, two_t, unchanged
):
    """A connector whose endpoint names no field or several resolves to no
    pair and refuses nothing: the trellis is elaborated as a draft, its
    report names the diagnostic at the entry's address with the candidates,
    the joins, the unjoined fields, the trellis drawing and the Model
    Explorer view are answered from the same occurrences, and a pair that
    is incompatible stands uncertified with its reason. A connector of no
    admitted shape and a stage that does not parse still refuse construction.
    A duplicate claim or authored cycle remains on the draft; an operation
    requiring order still refuses it."""
    swap = period({"S": two_fields, "T": two_t}, [{"S.a": "T.b", "S.b": "T.a"}])
    faulty = period({"S": two_fields, "U": unchanged}, [{"a": "q"}])
    draft = trellis_of(swap, faulty, inter_connectors=[{"a": "a", "b": "b"}])
    report = connection_report(draft)
    assert [(d.rule, d.address) for d in report.diagnostics] == [
        ("endpoint-ambiguous", "periods[1].connectors[0]"),
        ("endpoint-unresolved", "periods[1].connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
        ("endpoint-ambiguous", "inter_connectors[0]"),
    ]
    ambiguous, unresolved = report.diagnostics[:2]
    assert [str(use) for use in ambiguous.candidates] == ["periods[1].S.a", "periods[1].U.a"]
    assert ambiguous.source_entries == unresolved.source_entries == (
        ("periods[1].connectors[0]", "a", "q"),
    )
    assert "'q' names no arrival state field of periods[1]" in unresolved.message
    assert "the pair periods[1] → periods[0]" in report.diagnostics[2].message
    assert len(report.pairs) == 2 and len(report.routes) == 1
    assert period_joins(draft["periods"][1], "periods[1]") == {
        "joins": [],
        "outputs": [("S", "a"), ("S", "b"), ("U", "a")],
    }
    assert (
        inter_period_joins(
            draft["inter_connectors"][0],
            draft["periods"][1],
            draft["periods"][0],
            "inter_connectors[0]",
        )
        == []
    )
    unjoined = unjoined_fields(draft)
    assert (1, "U", "a") in unjoined["writing"] and (1, "U", "a") in unjoined["reading"]
    assert (1, "U", "a") in report.unjoined["internal"]["writing"]
    assert (1, "U", "a") in report.unjoined["exterior"]["reading"]
    assert unjoined["sources"] == {
        (0, "T", "a"): ("periods[0].connectors[0]",),
        (0, "T", "b"): ("periods[0].connectors[0]",),
    }
    assert repr(diagram_trellis(draft)) == "Drawing of 4 boxes"
    view = to_model_explorer(draft, unjoined=True)
    assert all(len(graph.nodes) > 1 for graph in view.graphs)
    # the report of a restriction is taken from the one selection of the whole trellis
    chosen = connection_report(draft, periods=[1])
    assert chosen.pairs == () and len(chosen.diagnostics) == 5
    assert all(h == 1 for scope in chosen.unjoined.values()
               for fields in scope.values() for h, _, _ in fields)
    assert chosen.counts == report.counts and chosen.selection == report.selection
    # an authored pair from the nonnegative into the strictly positive set is incompatible,
    # stands uncertified and is drawn with its status on the reading port
    positive = stage_from_text(renamed(UNCHANGED.replace("ℝ₊", "ℝ₊₊"), "positive"), "positive.bl")
    narrowing = trellis_of(period({"S": unchanged, "T": positive}, [{"S.a": "T.a"}]))
    (pair,) = connection_report(narrowing).pairs
    assert (pair.compatibility, pair.origin) == ("incompatible", "authored")
    assert "ℝ₊, does not lie in" in pair.reason
    assert [d.rule for d in connection_report(narrowing).diagnostics] == [
        "pair-incompatible",
        "route-incompatible",
    ]
    measure = port_attributes(to_model_explorer(narrowing), "forward")
    assert measure["periods[0]/T/positive:measure:arvl"]["compatibility"] == "incompatible"
    for connectors, rule in (
        ([{"from": "S", "to": "T", "fields": {"a": "b"}, "label": "x"}], "connector-names-no-field"),
        (["S.a: T.a"], "connector-names-no-field"),
    ):
        with pytest.raises(FactoryError) as refused:
            trellis_of(period({"S": two_fields, "T": two_t}, connectors))
        assert refused.value.rule == rule
    duplicate = trellis_of(period(
        {"S": unchanged, "T": unchanged, "U": unchanged},
        [{"S.a": "T.a"}, {"S.a": "U.a"}],
    ))
    duplicate_report = connection_report(duplicate)
    assert "use-claimed-twice" in [d.rule for d in duplicate_report.diagnostics]
    assert duplicate_report.routes[0].source == (0, "S")
    assert duplicate_report.routes[0].status == "uncertified"
    assert duplicate_report.diagnostics[0].source_entries == (
        ("periods[0].connectors[0]", "S.a", "T.a"),
        ("periods[0].connectors[1]", "S.a", "U.a"),
    )
    with pytest.raises(ValueError, match="not certified"):
        transport_point(duplicate_report.routes[0], (1,))
    with pytest.raises(FactoryError, match="both map"):
        forward_order(duplicate["periods"][0], "periods[0]")
    cycle = trellis_of(period(
        {"S": unchanged, "T": unchanged},
        [{"S.a": "T.a"}, {"T.a": "S.a"}],
    ))
    cycle_report = connection_report(cycle)
    assert "authored-cycle" in [d.rule for d in cycle_report.diagnostics]
    assert cycle_report.counts["certified"] == 0
    assert all(route.status == "uncertified" for route in cycle_report.routes)
    with pytest.raises(ValueError, match="not certified"):
        transport_point(cycle_report.routes[0], (1,))
    with pytest.raises(FactoryError) as refused:
        forward_order(cycle["periods"][0], "periods[0]")
    assert refused.value.rule == "period-join-cycle"
    self_pair = trellis_of(period({"S": two_fields}, [{"S.a": "S.b"}]))
    assert "authored-cycle" in [d.rule for d in connection_report(self_pair).diagnostics]
    with pytest.raises(FactoryError) as refused:
        forward_order(self_pair["periods"][0], "periods[0]")
    assert refused.value.rule == "period-join-cycle"
    record = {"stage": {"text": "@stage: bad\n[id=x", "origin": "bad.bl"}}
    with pytest.raises(ConstructionError) as refused:
        trellis_of(period({"bad": {**record, "calibration": {}, "settings": {}, "methods": {}}}))
    assert refused.value.rule == "syntax"


def test_item_3_a_dotted_stage_key_and_a_shared_mapping_resolve_at_each_pair_separately(
    two_fields, unchanged
):
    """A stage key may hold a dot: `foo.bar.a` is the field `a` of the
    occurrence keyed `foo.bar`, split at the final dot (plan §Review focus
    item 1). A mapping repeated for every adjacent pair is resolved at each
    pair: `{a: a}` resolves where one stage of the later period arrives at
    `a` and is diagnosed at the pair whose later period holds two, naming
    that pair; qualified there, both pairs resolve, and the arrival then
    authored leaves one candidate within the terminal period, which is
    inferred and certified (amendment §3.1; plan §Review focus item 4)."""
    dotted = trellis_of(
        period(
            {"foo.bar": unchanged, "foo": unchanged, "T": two_fields},
            [{"foo.bar.a": "T.a"}, {"foo.a": "T.b"}],
        )
    )
    assert period_joins(dotted["periods"][0], "periods[0]")["joins"] == [
        {"from": ("foo", "a"), "to": ("T", "b")},
        {"from": ("foo.bar", "a"), "to": ("T", "a")},
    ]
    # each source supplies one of T's two coordinates: the routes are incomplete, the endpoints resolved
    assert [d.rule for d in connection_report(dotted).diagnostics] == ["route-incomplete"] * 2
    periods = (
        period({"T": unchanged, "U": unchanged}),
        period({"S": unchanged}),
        period({"S": unchanged}),
    )
    shared = trellis_of(*periods, inter_connectors=[{"a": "a"}, {"a": "a"}])
    report = connection_report(shared)
    (diagnostic,) = report.diagnostics
    assert (diagnostic.rule, diagnostic.address) == ("endpoint-ambiguous", "inter_connectors[0]")
    assert "periods[1] → periods[0]" in diagnostic.message and "T.a, U.a" in diagnostic.message
    assert [(str(p.writing), str(p.reading)) for p in report.pairs] == [
        ("periods[2].S.a", "periods[1].S.a")
    ]
    later, middle, terminal = shared["periods"][2], shared["periods"][1], shared["periods"][0]
    assert inter_period_joins({"a": "a"}, middle, terminal, "inter_connectors[0]") == []
    assert inter_period_joins({"a": "a"}, later, middle, "inter_connectors[1]") == [
        {"from": ("S", "a"), "to": ("S", "a")}
    ]
    resolved = trellis_of(*periods, inter_connectors=[{"a": "T.a"}, {"a": "a"}])
    qualified = connection_report(resolved)
    assert [(str(p.writing), str(p.reading), p.origin) for p in qualified.pairs] == [
        ("periods[1].S.a", "periods[0].T.a", "authored"),
        ("periods[2].S.a", "periods[1].S.a", "authored"),
        ("periods[0].T.a", "periods[0].U.a", "inferred"),
    ]
    assert qualified.diagnostics == () and qualified.counts["certified"] == 3
    assert forward_order(resolved["periods"][0], "periods[0]") == ["T", "U"]
    assert forward_order(shared["periods"][0], "periods[0]") == ["T", "U"]


def test_item_4_a_compatibility_read_at_values_names_its_bindings_and_a_refused_request_leaves_them(
    tmp_path,
):
    """The bound `a_min` of the bounded stage is one parameter of each
    period: the pair between the periods is read at the two bound values,
    compatible where the earlier period's bound is the higher, its basis
    naming the digest of each binding read, and `bindings` naming the
    digest each position holds; a recalibration that changes a value
    changes the answer under another digest; a requested calibration the
    period refuses leaves the trellis as it was bound, and its report names
    the retained digests and not the request's, so that the retained values
    certify nothing about the values requested (amendment §3.3; plan
    §Construction and performance constraints)."""
    registry = written(tmp_path / "bounded", BOUNDED_REGISTRY)
    specified = specify_trellis(load_recipe(registry, "spec.yml"))
    report = connection_report(specified)
    (pair,) = report.pairs
    assert (str(pair.writing), str(pair.reading), pair.compatibility) == (
        "periods[1].b2.a",
        "periods[0].b1.a",
        "compatible",
    )
    assert "[1, inf) against [0, inf)" in pair.reason
    held = {
        (h, key): source_description(dict(stage.bindings.calibration))["sha256"]
        for h, held_period in enumerate(specified["periods"])
        for key, stage in held_period["stages"].items()
    }
    assert dict(report.bindings) == held
    assert pair.basis == ((1, "b2", held[1, "b2"]), (0, "b1", held[0, "b1"]))
    (route,) = report.routes
    assert route.status == "certified" and route.basis == pair.basis
    assert report.diagnostics == ()
    # the symbolic reading of the same trellis reads no value
    (symbolic,) = connection_report(elaborate_trellis(load_recipe(registry, "spec.yml"))).pairs
    assert symbolic.compatibility == "not-established" and symbolic.basis == ()
    # a lower bound requested for the earlier period is bound and decides the other way
    lowered = calibrate_trellis(
        specified, load_recipe(registry, "spec.yml", b2_fill={"a_min": -1.0})
    )
    changed, inferred = connection_report(lowered).pairs
    assert changed.compatibility == "incompatible"
    assert "[-1, inf) against [0, inf)" in changed.reason
    assert changed.basis[0][2] != held[1, "b2"] and changed.basis[1] == (0, "b1", held[0, "b1"])
    # the lower bound admits the unchanged-field stage's ℝ₊ as well, so a pair the retained
    # value rejected is now inferred: the bound value changes the selection
    assert (str(inferred.writing), str(inferred.reading), inferred.origin) == (
        "periods[1].u2.a", "periods[1].b2.a", "inferred"
    )
    (between,) = [r for r in connection_report(lowered).routes if r.destination == (0, "b1")]
    assert between.status == "uncertified"
    # a request the period refuses, β of u2 against β of b2, binds nothing
    requested = load_recipe(registry, "spec.yml", u_fill={"β": 0.5})
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(specified, requested)
    assert refused.value.rule == "period-parameter-agreement"
    again = connection_report(specified)
    assert dict(again.bindings) == held and again.pairs == report.pairs
    digests = set(again.bindings.values())
    assert source_description({"β": 0.5})["sha256"] not in digests
    assert source_description({"a_min": 1.0, "β": 0.5})["sha256"] not in digests


def test_item_5_connector_entry_writes_the_shortest_spelling_that_resolves_back_to_the_pair(
    tmp_path,
):
    """A drag writes the shortest spelling that the reader resolves to the
    dragged pair at every period the entry reaches: bare where both names
    are unique there, the stage key before a colliding endpoint alone, in
    the first empty mapping of the period's connectors; a drag between two
    periods writes into the mapping, resolved at each adjacent pair; a pair
    the mapping cannot reach at every pair is `name-shared`, the fully
    qualified spelling not written. An existing keyed group from the same
    two stages takes a further bare key. The written source, read again,
    selects the pair at the entry's address (brief §Integrate one trellis
    reading)."""
    registry = written(tmp_path / "drags", REGISTRY)
    trellis = specify_trellis(load_recipe(registry, "spec.yml"))
    period_file, trellis_file = str(registry / "period.yml"), str(registry / "trellis.yml")
    three = (0, 1, 2)
    # s continues to a and b, u to a and d to k_next; s, u and d arrive at a
    for writing, reading, answer in (
        ((1, "s", "b"), (1, "u", "a"), (period_file, "connectors[0]", three, "{b: u.a}", None)),
        ((1, "u", "a"), (1, "d", "a"), (period_file, "connectors[0]", three, "{u.a: d.a}", None)),
        (
            (1, "d", "k_next"),
            (0, "u", "a"),
            (trellis_file, "inter_connectors[0]", three, "k_next: u.a", None),
        ),
        ((1, "s", "a"), (1, "s", "b"), (None, None, (), None, "not-adjacent")),
        ((2, "s", "a"), (0, "u", "a"), (None, None, (), None, "not-adjacent")),
    ):
        entry = connector_entry(trellis, writing, reading)
        assert entry[:5] == answer, (writing, reading)
    # the source written as the first drag answers, read again, selects that pair at the address
    text = (registry / "period.yml").read_text(encoding="utf-8")
    texts = {str((registry / "period.yml").resolve()): text.replace("- {}", "- {b: u.a}")}
    reopened = specify_trellis(load_recipe(registry, "spec.yml", texts))
    pairs = connection_report(reopened).pairs
    assert [(str(p.writing), str(p.reading), p.address) for p in pairs] == [
        (f"periods[{h}].s.b", f"periods[{h}].u.a", f"periods[{h}].connectors[0]") for h in three
    ]
    assert connector_entry(reopened, (1, "s", "b"), (1, "u", "a"), texts)[4] == "port-joined"
    # a keyed group from s to d takes the further key bare; its text is the fields entry
    keyed = text.replace("- {}", "- {from: s, to: d, fields: {a: a}}")
    texts = {str((registry / "period.yml").resolve()): keyed}
    grouped = specify_trellis(load_recipe(registry, "spec.yml", texts))
    entry = connector_entry(grouped, (1, "s", "b"), (1, "d", "a"), texts)
    assert entry[:5] == (period_file, "connectors[0].fields", three, "{b: a}", None)
    # the mapping stands for both adjacent pairs; a pair whose stage one of them lacks round-trips
    # at no spelling and is answered as name-shared with the spelling that was not written
    uneven = written(
        tmp_path / "uneven",
        {
            **REGISTRY,
            "other.yml": "name: q\nstages: [s, u]\nconnectors: []\n",
            "trellis.yml": "periods:\n  - {template: period.yml, repeat: 2}\n"
            "  - {template: other.yml}\ninter_connectors:\n  - {}\n",
        },
    )
    partial = specify_trellis(load_recipe(uneven, "spec.yml"))
    entry = connector_entry(partial, (1, "d", "k_next"), (0, "u", "a"))
    assert entry[:5] == (
        str(uneven / "trellis.yml"),
        "inter_connectors[0]",
        three,
        "d.k_next: u.a",
        "name-shared",
    )


def test_item_6_one_reading_selects_once_and_constructs_each_text_once(tmp_path, monkeypatch):
    """The construction selects the connections on the symbolic occurrences
    and again under the bound values, two calls for `specify_trellis` and
    one for `elaborate_trellis`; a view, a drawing, a report and the
    unpaired joins each select once, a restriction of the view as well, and
    no query elaborates a second trellis: each distinct stage text is
    constructed once for a reading, however many positions hold it (plan
    §Construction and performance constraints)."""
    calls, constructions = [], []
    for module in (joins_module, connections_module, entries_module):
        if not hasattr(module, "select_connections"):
            continue
        function = module.select_connections

        def counted(*arguments, _function=function, **keywords):
            calls.append(_function.__module__)
            return _function(*arguments, **keywords)

        monkeypatch.setattr(module, "select_connections", counted)
    construct = trellis_module.construct_stage
    monkeypatch.setattr(
        trellis_module,
        "construct_stage",
        lambda text, origin, additions=(): constructions.append(origin)
        or construct(text, origin, additions),
    )
    registry = written(tmp_path / "once", REGISTRY)
    syntactic = load_recipe(registry, "spec.yml")
    elaborated = elaborate_trellis(syntactic)
    assert len(calls) == 1
    assert sorted(Path(o).name for o in constructions) == ["d.bl", "s.bl", "u.bl"]
    specified = specify_trellis(syntactic)
    assert len(calls) == 3 and len(constructions) == 6
    for query in (
        lambda: to_model_explorer(specified),
        lambda: to_model_explorer(specified, periods=[0], unjoined=True),
        lambda: connection_report(specified),
        lambda: diagram_trellis(specified),
        lambda: unpaired_joins(specified),
        lambda: unjoined_fields(specified),
    ):
        before = len(calls)
        query()
        assert len(calls) == before + 1, query
    report = connection_report(specified)
    before = len(calls)
    assert connection_report(specified, periods=[0], selection=report.selection).selection is report.selection
    to_model_explorer(specified, periods=[0], unjoined=True, selection=report.selection)
    unpaired_joins(specified, periods=[0], selection=report.selection)
    assert len(calls) == before
    with monkeypatch.context() as guard:
        guard.setattr(
            joins_module, "fields",
            lambda stage: pytest.fail("a supplied selection already holds the state fields"),
        )
        restricted = connection_report(
            specified, periods=[0], selection=report.selection
        )
        assert restricted.unjoined["exterior"]["writing"] == tuple(
            field for field in report.unjoined["exterior"]["writing"] if field[0] == 0
        )
    before = len(calls)
    connector_entry(specified, (1, "u", "a"), (1, "d", "a"))
    # One selection supplies the eligible uses for every spelling tried.
    assert len(calls) == before + 1
    assert len(constructions) == 6 and len(elaborated["periods"]) == 3
