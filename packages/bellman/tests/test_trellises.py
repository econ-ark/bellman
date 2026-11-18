"""A trellis read and elaborated: what load_recipe and load_trellis read,
elaborate_trellis with and without a previous trellis, accrete, and a
parameter that two stages of one period declare."""

import hashlib
import pickle
from pathlib import Path

import pytest
import yaml
from application_files import CONS_METHODS, DURABLES, DURABLES_RECIPE_WITHOUT_TENURE
from stage_builders import differing_graph_triples, without_addresses
from stage_texts import DISC_WITH_K_NEXT_TEXT, corpus_text
from trellises import BEQUEST_CONNECTOR

import bellman.factory.trellis as trellis_module
from bellman.factory.joins import forward_order, period_joins
from bellman.factory.trellis import already_bound, positions
from bellman.refusal_examples import TWO_NODES, write_registry
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    accrete,
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    connection_report,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    respecify_trellis,
    specify_trellis,
)

# a record of the stage text `@stage: t`, which declares nothing, with no
# bindings
RECORD_OF_A_STAGE_TEXT = {
    "stage": {"text": "@stage: t\n", "origin": "t.bl"},
    "calibration": {},
    "settings": {},
    "methods": {},
}


# a registry of a period of two stages that both declare the parameter β,
# written over the files of the small registry of `bellman.refusal_examples`,
# `REGISTRY_FILES`: the two-node stage `two_nodes` of that registry
# (`bellman.refusal_examples.TWO_NODES`) declares β in ℝ₊₊ and its
# calibration file supplies it; the discounting stage DISC_TEXT declares β in
# (0,1) and its calibration list holds a slot alone; the two-node stage
# continues to `a`, at which the discounting stage arrives, and the
# discounting stage's `k_next` is the next period's `k`
SHARED_BETA_REGISTRY = {
    "stages/disc/disc.bl": DISC_WITH_K_NEXT_TEXT,
    "period.yml": "name: two_stages\nstages: [two_nodes, disc]\nconnectors: []\n",
    "trellis.yml": "periods:\n  - {template: period.yml, repeat: 2}\n"
    "inter_connectors:\n  - {k_next: k}\n",
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n  two_nodes:\n"
        "    stage: stages/two_nodes/two_nodes.bl\n"
        "    calibration: {all: [calibration/main, $fill]}\n"
        "    settings: {all: [settings/main, $fill]}\n"
        "    methods: {all: [stages/two_nodes/methods.bl]}\n"
        "  disc:\n    stage: stages/disc/disc.bl\n"
        "    calibration: {all: [$disc_fill]}\n"
    ),
}


def without_provenance(trellis):
    """A syntactic trellis reduced to each record's `stage`, `calibration`,
    `settings` and `methods`, each period's connectors and the inter-period
    mappings, without the registry, the provenance of the trellis and the
    provenance of each record."""
    return {
        "periods": [
            {
                "stages": {
                    key: {
                        name: record[name]
                        for name in ("stage", "calibration", "settings", "methods")
                    }
                    for key, record in period["stages"].items()
                },
                "connectors": period["connectors"],
            }
            for period in trellis["periods"]
        ],
        "inter_connectors": trellis["inter_connectors"],
    }


def registry_declaring_beta(folder, two_nodes_line, disc_line):
    """The files of SHARED_BETA_REGISTRY written under `folder`, the two-node
    stage declaring β by `two_nodes_line` and the discounting stage by
    `disc_line`. A stage text that does not hold its declaration of β once
    is refused with a ValueError, since the replacement reads it."""
    declared, shared = "β : ℝ₊₊\n", "β : (0,1)"
    discounting = SHARED_BETA_REGISTRY["stages/disc/disc.bl"]
    if TWO_NODES.count(declared) != 1 or discounting.count(shared) != 1:
        raise ValueError("a stage text does not declare β once as the replacement reads it")
    files = {
        **SHARED_BETA_REGISTRY,
        "stages/two_nodes/two_nodes.bl": TWO_NODES.replace(declared, two_nodes_line + "\n"),
        "stages/disc/disc.bl": discounting.replace(shared, disc_line),
    }
    return write_registry(folder, files)


def cons_then_port(cons, port):
    """A trellis of the stage cons alone, and the trellis that accrete
    answers when it appends to it a period of the stage port, joined by the
    inter-period mapping from port's m_next to cons's m."""
    trellis = accrete(
        {"periods": [], "inter_connectors": []}, {"stages": {"cons": cons}, "connectors": []}
    )
    later = accrete(trellis, {"stages": {"port": port}, "connectors": []}, {"m_next": "m"})
    return trellis, later


@pytest.fixture(scope="module")
def cons_record(corpus_path):
    """The record that load_stage reads from the stage file of cons."""
    return load_stage(corpus_path("cons"))


@pytest.fixture(scope="module")
def one_record_trellis():
    """The text of the stage file of cons and the elaborated trellis of one
    period that holds a record of that text under the key cons, with no
    bindings and no connectors."""
    text = corpus_text("cons")
    occurrence = {
        "stage": {"text": text, "origin": "cons.bl"},
        "methods": {},
        "settings": {},
        "calibration": {},
    }
    trellis = {
        "periods": [{"stages": {"cons": occurrence}, "connectors": []}],
        "inter_connectors": [],
    }
    return text, elaborate_trellis(trellis)


@pytest.fixture(scope="module")
def records_and_a_placed_stage(cons_record, cons):
    """A trellis whose terminal period holds two records of the stage file of
    cons, under the keys first and second, and whose next period holds the
    stage cons itself under the key held, with an inter-period mapping, a
    list of solutions and a registry; and the trellis that elaborate_trellis
    answers for it."""
    trellis = {
        "periods": [
            {"stages": {"first": cons_record, "second": dict(cons_record)}, "connectors": []},
            {"stages": {"held": cons}, "connectors": []},
        ],
        "inter_connectors": [{"a": "m"}],
        "solutions": [],
        "registry": {"calibration": {"first_age": 20}},
    }
    return trellis, elaborate_trellis(trellis)


@pytest.fixture(scope="module")
def written_out_folder(tmp_path_factory, corpus_path):
    """A folder of trellis files: trellis.yml writes out its terminal period,
    which names a calibration file, inline settings and the methods file of
    cons, and repeats twice the template period.yml, whose record names no
    methods, with one inter-period mapping; one.yml repeats the template
    once with that mapping; and no-periods.yml writes no periods."""
    folder = tmp_path_factory.mktemp("written-out")
    stage = str(corpus_path("cons"))
    (folder / "ρ.yml").write_text("calibration:\n  ρ: 4.0\n", encoding="utf-8")
    (folder / "period.yml").write_text(
        "stages:\n  cons: {stage: " + stage + ", calibration: ρ.yml, settings: {n_m: 10}}\n"
        "connectors: []\n",
        encoding="utf-8",
    )
    (folder / "trellis.yml").write_text(
        "periods:\n  - stages:\n      cons:\n        stage: " + stage + "\n"
        "        calibration: ρ.yml\n        settings: {n_m: 10}\n"
        "        methods: [" + str(CONS_METHODS) + "]\n"
        "    connectors: []\n  - {template: period.yml, repeat: 2}\n"
        "inter_connectors:\n  - {a: m}\n",
        encoding="utf-8",
    )
    (folder / "one.yml").write_text(
        "periods:\n  - {template: period.yml, repeat: 1}\ninter_connectors:\n  - {a: m}\n",
        encoding="utf-8",
    )
    (folder / "no-periods.yml").write_text("stages: []\n", encoding="utf-8")
    return folder


@pytest.fixture(scope="module")
def written_out(written_out_folder):
    """The syntactic trellis that load_trellis reads from the file
    trellis.yml of `written_out_folder`."""
    return load_trellis(written_out_folder / "trellis.yml")


@pytest.fixture(scope="module")
def methods_folder(tmp_path_factory, corpus_path):
    """A folder of three trellis files of one period of cons, whose record
    names its methods as a list of the methods file of cons in trellis.yml,
    as that one path in one.yml, and as a mapping in inline.yml."""
    folder = tmp_path_factory.mktemp("methods")
    head = (
        "!trellis\nperiods:\n  - stages:\n      cons:\n        stage: "
        + str(corpus_path("cons"))
        + "\n        calibration: {}\n        settings: {}\n"
    )
    tail = "    connectors: []\ninter_connectors: []\n"
    methods = {
        "trellis.yml": "        methods: [" + str(CONS_METHODS) + "]\n",
        "one.yml": "        methods: " + str(CONS_METHODS) + "\n",
        "inline.yml": "        methods:\n          stage: cons\n          methods:\n"
        "            - on: policy\n              method: !egm\n",
    }
    for name, written in methods.items():
        (folder / name).write_text(head + written + tail, encoding="utf-8")
    return folder


@pytest.fixture(scope="module")
def methods_list_record(methods_folder):
    """The record of cons that load_trellis reads from the file whose record
    names a list of one methods file."""
    return load_trellis(methods_folder / "trellis.yml")["periods"][0]["stages"]["cons"]


@pytest.fixture(scope="module")
def durables_recipe():
    """The syntactic trellis that load_recipe reads from the recipe spec.yml
    of the durables application."""
    return load_recipe(DURABLES, "spec.yml")


@pytest.fixture(scope="module")
def shared_beta_registry(tmp_path_factory):
    """The folder of SHARED_BETA_REGISTRY."""
    return write_registry(tmp_path_factory.mktemp("shared"), SHARED_BETA_REGISTRY)


@pytest.fixture(scope="module")
def shared_beta_trellis(shared_beta_registry):
    """The syntactic trellis of the recipe of SHARED_BETA_REGISTRY and the
    trellis that specify_trellis answers for it."""
    syntactic = load_recipe(shared_beta_registry, "spec.yml")
    return syntactic, specify_trellis(syntactic)


@pytest.fixture(scope="module")
def filled_shared_beta(shared_beta_registry):
    """The recipe of SHARED_BETA_REGISTRY with the fill β = 0.9, and its
    elaborated trellis bound by calibrate_trellis."""
    filled = load_recipe(shared_beta_registry, "spec.yml", fill={"β": 0.9})
    return filled, calibrate_trellis(elaborate_trellis(filled), filled)


@pytest.fixture(scope="module")
def respecified_shared_beta(shared_beta_registry, shared_beta_trellis):
    """The recipe of SHARED_BETA_REGISTRY with the fill β = 0.9, which
    changes the two-node stage's record alone, and the trellis that
    respecify_trellis answers for it from the specified trellis."""
    before, specified = shared_beta_trellis
    after = load_recipe(shared_beta_registry, "spec.yml", fill={"β": 0.9})
    return after, respecify_trellis(specified, before, after)


@pytest.fixture(scope="module")
def retained_after_refusal(shared_beta_registry, shared_beta_trellis):
    """The recipe of SHARED_BETA_REGISTRY with β = 0.5 supplied by the
    discounting stage's slot, which disagrees with the two-node stage's
    0.96, and the trellis that specify_trellis answers for the methods and
    the settings alone with the specified trellis as the previous trellis."""
    _, specified = shared_beta_trellis
    requested = load_recipe(shared_beta_registry, "spec.yml", disc_fill={"β": 0.5})
    return requested, specify_trellis(requested, specified, ["methods", "settings"])


@pytest.fixture(scope="module")
def one_union_registry(tmp_path_factory):
    """SHARED_BETA_REGISTRY with both stages declaring β in the union of
    (0,1) and (1, inf), its members written in the two orders."""
    return registry_declaring_beta(
        tmp_path_factory.mktemp("same"), "β : (0,1) \\/ (1, inf)", "β : (1, inf) \\/ (0,1)"
    )


def test_load_recipe_reads_the_fifty_one_periods_of_the_durables_recipe_and_their_stages(
    durables_recipe,
):
    """load_recipe reads the durables recipe as 51 periods joined by 50
    inter-period mappings, the terminal period holding the bequest after the
    three stages that each of the fifty other periods holds."""
    assert len(durables_recipe["periods"]) == 51
    assert len(durables_recipe["inter_connectors"]) == 50
    assert list(durables_recipe["periods"][0]["stages"]) == [
        "tenure",
        "keeper_cons",
        "adjuster_cons",
        "bequest",
    ]
    assert [list(period["stages"]) for period in durables_recipe["periods"][1:]] == [
        ["tenure", "keeper_cons", "adjuster_cons"]
    ] * 50


def test_a_record_of_a_recipe_holds_the_stage_file_values_and_methods_its_sources_name(
    durables_recipe,
):
    """The adjuster's record that load_recipe reads holds the origin of its
    stage file, the values of the calibration file, the setting n_a and its
    one methods file with its text and its origin."""
    record = durables_recipe["periods"][0]["stages"]["adjuster_cons"]
    assert record["stage"]["origin"] == str(DURABLES / "stages/adjuster_cons/adjuster_cons.bl")
    assert {name: record["calibration"][name] for name in ("β", "α", "γ_c", "γ_h", "κ", "τ")} == {
        "β": 0.945,
        "α": 0.7,
        "γ_c": 3.5,
        "γ_h": 1.5,
        "κ": 0.06,
        "τ": 0.12,
    }
    assert record["settings"]["n_a"] == 300
    (held,) = record["methods"]
    assert held["origin"] == str(DURABLES / "stages/adjuster_cons/methods.bl")
    assert held["text"].startswith("@methods: adjuster_cons\n")
    # the policy block of the methods file names the routine of the
    # replication code
    assert 'handler : "fues-durables:make_adjuster_ops"' in held["text"]


def test_the_provenance_of_a_record_holds_its_calibration_sources_and_the_digest_of_its_text(
    durables_recipe,
):
    """The provenance of the adjuster's record lists the calibration file
    with its digest and the unbound slot `fill`, and holds the digest of the
    stage text."""
    record = durables_recipe["periods"][0]["stages"]["adjuster_cons"]
    lists = record["provenance"]["source_lists"]
    assert [item.get("source", item.get("slot")) for item in lists["calibration"]] == [
        "calibration/durables",
        "fill",
    ]
    file = DURABLES / "calibration/durables.yml"
    assert lists["calibration"][0]["sha256"] == hashlib.sha256(file.read_bytes()).hexdigest()
    assert lists["calibration"][1] == {"slot": "fill", "bound": False, "names": []}
    text = record["stage"]["text"]
    assert record["provenance"]["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_load_recipe_reads_the_two_income_tables_into_the_calibration_of_each_tenure_record(
    durables_recipe,
):
    """load_recipe reads the income level Y and the retirement income y_R of
    the durables application into the calibration of each tenure record, as
    tables of 52 entries, one for each age, from the source that the recipe
    lists after the calibration file of the application."""
    records = [period["stages"]["tenure"] for period in durables_recipe["periods"]]
    assert {
        (len(record["calibration"]["Y"]), len(record["calibration"]["y_R"])) for record in records
    } == {(52, 52)}
    assert {
        tuple(
            item.get("source", item.get("slot"))
            for item in record["provenance"]["source_lists"]["calibration"]
        )
        for record in records
    } == {("calibration/durables", "calibration/wage_schedule", "fill")}


def test_load_trellis_of_the_two_stage_model_written_out_equals_load_recipe_of_its_recipe(
    tmp_path,
):
    """load_trellis of the two-stage durables model written out by hand,
    each record naming the folder's files and the fifty equal periods one
    template repeated, reads the records and connectors that load_recipe
    reads from the two-stage recipe."""
    stages = {
        key: {
            "stage": str(DURABLES / f"stages/{key}/{key}.bl"),
            "calibration": str(DURABLES / "calibration/durables.yml"),
            "settings": str(DURABLES / "settings/durables.yml"),
            "methods": str(DURABLES / f"stages/{key}/methods.bl"),
        }
        for key in ("keeper_cons", "adjuster_cons")
    }
    # the methods file of the bequest writes the derivative lines of its two
    # value builders
    bequest = {
        "stage": str(DURABLES / "stages/bequest/bequest.bl"),
        "calibration": str(DURABLES / "calibration/durables.yml"),
        "methods": str(DURABLES / "stages/bequest/methods.bl"),
    }
    period = {"stages": stages, "connectors": []}
    (tmp_path / "period-two-stages-written.yml").write_text(
        yaml.safe_dump(period, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    written = {
        "periods": [
            {"stages": {**stages, "bequest": bequest}, "connectors": [BEQUEST_CONNECTOR]},
            {"template": "period-two-stages-written.yml", "repeat": 50},
        ],
        "inter_connectors": [],
    }
    file = tmp_path / "trellis-two-stages-written.yml"
    file.write_text(yaml.safe_dump(written, allow_unicode=True, sort_keys=False), encoding="utf-8")
    expected = without_provenance(load_recipe(DURABLES, DURABLES_RECIPE_WITHOUT_TENURE))
    assert without_provenance(load_trellis(file)) == expected


def test_the_records_of_a_recipe_written_out_with_their_values_are_read_back_equal(
    durables_recipe, tmp_path
):
    """load_trellis reads back the records that load_recipe read, written
    out with their calibration and settings inline and their methods files
    by path, as the same records and connectors."""
    inline = {
        "periods": [
            {
                "stages": {
                    key: {
                        "stage": record["stage"]["origin"],
                        "calibration": record["calibration"],
                        "settings": record["settings"],
                        "methods": [held["origin"] for held in record["methods"]],
                    }
                    for key, record in period["stages"].items()
                },
                "connectors": period["connectors"],
            }
            for period in durables_recipe["periods"]
        ],
        "inter_connectors": durables_recipe["inter_connectors"],
    }
    file = tmp_path / "trellis-written.yml"
    file.write_text(yaml.safe_dump(inline, allow_unicode=True, sort_keys=False), encoding="utf-8")
    assert without_provenance(load_trellis(file)) == without_provenance(durables_recipe)


# This test elaborates the durables trellis without the tenure stage whole,
# 103 positions over 51 periods, two stages in each of fifty periods and three
# in the terminal period, so it runs only with --complete.
@pytest.mark.complete_set
@pytest.mark.xfail(
    strict=True,
    reason="The test expects, in a period of `cons` and a copy of the portfolio stage `port` "
    "that continues to `m`, the inferred candidate port.m → cons.m, which closes a cycle with "
    "the authored pair cons.a → port.k, to be recorded among the rejected candidates under "
    "`inference-cycle`. Today the trellis is admitted with the authored pair, and the list of "
    "rejected candidates is empty.",
)
def test_elaborate_trellis_places_symbolic_copies_orders_by_fields_and_refuses_a_cycle(
    cons, corpus_path, monkeypatch
):
    """`elaborate_trellis` builds the 51 periods and 103 positions of the
    durables trellis without the tenure stage from one construction of each
    of its three stage texts, each position outside the terminal period a
    separate stage object with the graphs, the definitions and the bindings
    of its key in the terminal period; the joins and the forward order of a
    period do not depend on the order of its list of stages; an inferred
    candidate that closes a cycle with the authored pairs is rejected as a
    cycle; and a cycle that authored pairs alone close is refused under
    `period-join-cycle`."""
    constructions, construct = [], trellis_module.construct_stage
    monkeypatch.setattr(
        trellis_module,
        "construct_stage",
        lambda text, origin, additions=(): constructions.append(origin)
        or construct(text, origin, additions),
    )
    elaborated = elaborate_trellis(load_recipe(DURABLES, DURABLES_RECIPE_WITHOUT_TENURE))
    assert len(elaborated["periods"]) == 51 and len(positions(elaborated)) == 103
    # three constructions, one per distinct stage text, for the 103 positions
    assert sorted(Path(origin).name for origin in constructions) == [
        "adjuster_cons.bl",
        "bequest.bl",
        "keeper_cons.bl",
    ]
    terminal = elaborated["periods"][0]["stages"]
    for h, key, _, stage in positions(elaborated):
        status = "symbolic" if key == "bequest" else "methods"
        assert repr(stage) == f"ElaboratedStage({key!r}, {status})"
        assert dict(stage.provenance["position"]) == {"h": h, "key": key}
        assert h == 0 or stage is not terminal[key]
        assert differing_graph_triples(stage, terminal[key]) == []
        assert without_addresses(stage.definitions) == without_addresses(terminal[key].definitions)
        assert stage.bindings == terminal[key].bindings
    # the portfolio period of docs/Bellman-Sym/06-period.md, in which port.bl
    # continues to m_next: the joins and the order are the same under the
    # list [cons, disc, port] and its reverse
    port_next = elaborate_stage(load_stage(corpus_path("port")))
    disc = elaborate_stage(
        {
            "stage": {"text": DISC_WITH_K_NEXT_TEXT, "origin": "disc.bl"},
            "calibration": {},
            "settings": {},
            "methods": {},
        }
    )
    listed = {
        "stages": {"cons": cons, "disc": disc, "port": port_next},
        "connectors": [{"k_next": "k"}],
    }
    reversed_listing = {
        "stages": {"port": port_next, "disc": disc, "cons": cons},
        "connectors": [{"k_next": "k"}],
    }
    assert period_joins(listed) == period_joins(reversed_listing)
    assert period_joins(listed)["joins"] == [
        {"from": ("cons", "a"), "to": ("disc", "a")},
        {"from": ("disc", "k_next"), "to": ("port", "k")},
    ]
    assert forward_order(listed) == forward_order(reversed_listing) == ["cons", "disc", "port"]
    # the planted cycles, each under both orders of the list: a copy of port.bl
    # that continues to m, at which cons arrives; with the connector {a: k}
    # the two stages close a cycle through the inferred candidate
    # port.m → cons.m, and with disc between them a cycle of three stages
    # closes through two inferred candidates. The test expects each inferred
    # candidate on such a cycle to be rejected as a cycle and recorded among
    # the rejected candidates, so that the authored pairs stand and the
    # trellis is admitted: a cycle refuses the trellis only where authored
    # pairs alone close it
    from bellman.trellis import connection_report

    cons_record = load_stage(corpus_path("cons"))
    port_record = {
        "stage": {"text": corpus_text("port").replace("m_next", "m"), "origin": "port.bl"},
        "calibration": {},
        "settings": {},
        "methods": {},
    }
    for stages in (
        {"cons": cons_record, "port": port_record},
        {"port": port_record, "cons": cons_record},
    ):
        two = elaborate_trellis(
            {"periods": [{"stages": stages, "connectors": [{"a": "k"}]}], "inter_connectors": []}
        )
        report = connection_report(two)
        assert [(str(p.writing), str(p.reading)) for p in report.pairs] == [
            ("periods[0].cons.a", "periods[0].port.k")
        ]
        assert [(str(r.writing), str(r.reading), r.rule) for r in report.selection.rejected] == [
            ("periods[0].port.m", "periods[0].cons.m", "inference-cycle")
        ]
        assert forward_order(two["periods"][0], "periods[0]") == ["cons", "port"]
    port = elaborate_stage(port_record)
    for stages in (
        {"cons": cons, "disc": disc, "port": port},
        {"port": port, "disc": disc, "cons": cons},
    ):
        three = {"stages": stages, "connectors": [{"k_next": "k"}]}
        assert period_joins(three, "periods[0]")["joins"] == [
            {"from": ("disc", "k_next"), "to": ("port", "k")}
        ]
        assert forward_order(three, "periods[0]") == ["cons", "disc", "port"]
        rejected = connection_report(
            elaborate_trellis({"periods": [three], "inter_connectors": []})
        ).selection.rejected
        assert sorted((str(r.writing), str(r.reading), r.rule) for r in rejected) == [
            ("periods[0].cons.a", "periods[0].disc.a", "inference-cycle"),
            ("periods[0].port.m", "periods[0].cons.m", "inference-cycle"),
        ]
    # two authored pairs in opposite directions close a cycle that the
    # rejection of an inferred candidate cannot break: the forward order is
    # refused, and the message names the two fields of each pair
    with pytest.raises(FactoryError) as refused:
        forward_order(
            {"stages": {"cons": cons, "port": port}, "connectors": [{"a": "k"}, {"m": "m"}]},
            "periods[0]",
        )
    assert (refused.value.rule, refused.value.address) == ("period-join-cycle", "periods[0]")
    assert all(
        word in refused.value.message
        for word in (
            "cons continues to 'a'",
            "port arrives at 'k'",
            "port continues to 'm'",
            "cons arrives at 'm'",
        )
    )
    assert "_next" in refused.value.write


def test_elaborate_trellis_records_the_origin_and_the_digest_of_the_text_of_an_occurrence(
    one_record_trellis,
):
    """elaborate_trellis records in the provenance of a new stage occurrence
    the origin of its record's text and the digest of that text."""
    text, elaborated = one_record_trellis
    stage = elaborated["periods"][0]["stages"]["cons"]
    assert stage.provenance["origin"] == "cons.bl"
    assert stage.provenance["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_elaborate_trellis_writes_empty_connectors_and_mappings_for_a_trellis_that_writes_none(
    one_record_trellis,
):
    """elaborate_trellis answers empty connectors of the period and an empty
    list of inter-period mappings for a trellis of one record that writes
    both empty."""
    _, elaborated = one_record_trellis
    assert (elaborated["periods"][0]["connectors"], elaborated["inter_connectors"]) == ([], [])


def test_elaborate_trellis_refuses_a_record_that_holds_no_calibration_methods_or_settings():
    """elaborate_trellis refuses a record that holds its stage alone, with a
    message that names the three missing fields."""
    record = {"stage": {"text": "", "origin": "cons.bl"}}
    with pytest.raises(
        FactoryError, match=r"the record holds no calibration, methods or settings fields"
    ):
        elaborate_trellis(
            {"periods": [{"stages": {"cons": record}, "connectors": []}], "inter_connectors": []}
        )


def test_elaborate_trellis_makes_two_records_of_a_period_two_occurrences_at_their_positions(
    records_and_a_placed_stage,
):
    """elaborate_trellis makes two records of one stage file in one period
    two distinct stage occurrences of the same grammar versions, each
    recording its own position, the first symbolic with no calibration
    bound."""
    _, elaborated = records_and_a_placed_stage
    first, second = (elaborated["periods"][0]["stages"][key] for key in ("first", "second"))
    assert repr(first) == "ElaboratedStage('cons', symbolic)"
    assert dict(first.provenance["position"]) == {"h": 0, "key": "first"}
    assert first is not second and dict(second.provenance["position"]) == {"h": 0, "key": "second"}
    assert first.provenance["versions"] == second.provenance["versions"]
    assert first.bindings.calibration is None


def test_elaborate_trellis_places_a_copy_of_a_stage_object_that_records_its_position(
    records_and_a_placed_stage, cons
):
    """elaborate_trellis places a copy of a stage object that a period holds,
    with the graphs, the definitions and the bindings of the object and its
    provenance with the position added."""
    _, elaborated = records_and_a_placed_stage
    held = elaborated["periods"][1]["stages"]["held"]
    assert (
        held is not cons
        and differing_graph_triples(held, cons) == []
        and held.definitions == cons.definitions
    )
    assert held.bindings == cons.bindings and dict(held.provenance["position"]) == {
        "h": 1,
        "key": "held",
    }
    provenance = {name: value for name, value in held.provenance.items() if name != "position"}
    assert provenance == dict(cons.provenance)


def test_a_record_elaborates_to_the_graphs_of_the_stage_of_its_file(
    records_and_a_placed_stage, cons
):
    """The stage occurrence that elaborate_trellis makes of a record of the
    stage file of cons has the graphs of the stage cons."""
    _, elaborated = records_and_a_placed_stage
    assert differing_graph_triples(elaborated["periods"][0]["stages"]["first"], cons) == []


def test_elaborate_trellis_keeps_the_other_entries_of_a_trellis_and_a_copy_of_its_registry(
    records_and_a_placed_stage,
):
    """elaborate_trellis keeps the inter-period mappings, the solutions and
    the registry of a trellis, the registry an equal copy."""
    trellis, elaborated = records_and_a_placed_stage
    assert (elaborated["inter_connectors"], elaborated["solutions"]) == ([{"a": "m"}], [])
    assert elaborated["registry"] == trellis["registry"]
    assert elaborated["registry"] is not trellis["registry"]


def test_elaborate_trellis_refuses_a_record_whose_digest_is_not_that_of_its_text(cons_record):
    """elaborate_trellis refuses a record whose provenance holds a digest
    other than that of its text, its notes naming the stage occurrence."""
    # a SHA-256 digest is 64 hexadecimal digits; 64 zeros are not the digest of
    # the text of cons
    record = {**cons_record, "provenance": {"sha256": "0" * 64}}
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis(
            {"periods": [{"stages": {"cons": record}, "connectors": []}], "inter_connectors": []}
        )
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['cons']"]


def test_elaborate_trellis_refuses_a_trellis_that_is_no_mapping():
    """elaborate_trellis refuses a list in place of a trellis under
    `trellis-file-shape`, naming the periods."""
    with pytest.raises(FactoryError, match="periods") as refused:
        elaborate_trellis([])
    assert refused.value.rule == "trellis-file-shape"


def test_elaborate_trellis_refuses_three_periods_with_one_inter_period_mapping(cons_record):
    """elaborate_trellis refuses three periods with one inter-period mapping,
    since each pair of adjacent periods takes its own mapping."""
    periods = [{"stages": {"cons": cons_record}, "connectors": []}] * 3
    with pytest.raises(FactoryError, match="1 inter-period mappings for 3 periods") as refused:
        elaborate_trellis({"periods": periods, "inter_connectors": [{"a": "m"}]})
    assert (refused.value.rule, refused.value.address) == (
        "trellis-file-shape",
        "inter_connectors",
    )


def test_a_stage_text_refused_at_two_positions_is_refused_once_naming_both_occurrences(
    cons_record,
):
    """A stage text whose construction is refused, recorded at two
    positions, is refused once, its notes naming both stage occurrences."""
    text = cons_record["stage"]["text"].replace("m_d = m", "m_d = ")
    broken = {**cons_record, "stage": {"text": text, "origin": "cons.bl"}, "provenance": {}}
    stages = {"x": broken, "y": dict(broken)}
    with pytest.raises(ConstructionError) as refused:
        elaborate_trellis(
            {"periods": [{"stages": stages, "connectors": []}], "inter_connectors": []}
        )
    assert refused.value.__notes__ == [
        "Affected stage occurrences: periods[0].stages['x'], periods[0].stages['y']"
    ]


def test_elaborate_trellis_copies_from_a_previous_trellis_only_the_occurrence_of_an_unchanged_file(
    cons_record, corpus_path
):
    """elaborate_trellis given a previous trellis places a copy of the
    occurrence held there for an unchanged stage file, its binding included,
    and a new symbolic occurrence for a changed one."""
    syntactic = {
        "periods": [
            {"stages": {"cons": cons_record}, "connectors": []},
            {"stages": {"cons": dict(cons_record)}, "connectors": []},
        ],
        "inter_connectors": [{"a": "m"}],
    }
    elaborated = elaborate_trellis(syntactic)
    # the previous trellis holds a version bound by hand at the terminal
    # period
    held = elaborated["periods"][0]["stages"]["cons"].calibrate({"ρ": 2.0})
    previous = {
        **elaborated,
        "periods": [{"stages": {"cons": held}, "connectors": []}, elaborated["periods"][1]],
    }
    # the changed file halves the law of motion and writes the grid line as
    # the halved law solved for m_d
    text = (
        corpus_text("cons")
        .replace("    a = m_d - c\n", "    a = (m_d - c)/2\n")
        .replace(
            "    m_d[>] = a + c[>]                :: [id=endoggrid]",
            "    m_d[>] = 2*a + c[>]              :: [id=endoggrid]",
        )
    )
    changed = {
        **cons_record,
        "stage": {"text": text, "origin": str(corpus_path("cons"))},
        "provenance": {},
    }
    periods = [syntactic["periods"][0], {"stages": {"cons": changed}, "connectors": []}]
    again = elaborate_trellis({**syntactic, "periods": periods}, previous)
    kept, made = (again["periods"][h]["stages"]["cons"] for h in (0, 1))
    assert kept == held and kept is not held
    assert repr(made) == "ElaboratedStage('cons', symbolic)"
    assert made.provenance["sha256"] != cons_record["provenance"]["sha256"]


def test_accrete_appends_the_earlier_period_with_its_mapping_as_a_copy_recording_its_position(
    cons, port
):
    """accrete appends the earlier period after the later one, with the
    mapping that joins them, as a copy of its stage that records its
    position."""
    _, later = cons_then_port(cons, port)
    assert [list(period["stages"]) for period in later["periods"]] == [["cons"], ["port"]]
    assert later["inter_connectors"] == [{"m_next": "m"}]
    appended = later["periods"][1]["stages"]["port"]
    assert appended is not port and differing_graph_triples(appended, port) == []
    assert appended.definitions == port.definitions
    assert dict(appended.provenance["position"]) == {"h": 1, "key": "port"}


def test_accrete_keeps_the_stage_occurrences_of_the_trellis_it_is_given_in_a_copy_of_its_periods(
    cons, port
):
    """accrete holds the very stage occurrences of the periods that the trellis
    held, in a copy of each period's stages, so that a write into the result
    changes no argument."""
    trellis, later = cons_then_port(cons, port)
    assert trellis["periods"][0]["stages"]["cons"] is later["periods"][0]["stages"]["cons"]
    later["periods"][0]["stages"]["extra"] = port
    assert list(trellis["periods"][0]["stages"]) == ["cons"]


def test_accrete_leaves_the_trellis_that_it_is_given_unchanged(cons, port):
    """The trellis to which accrete appends a period keeps its one period
    and its empty list of inter-period mappings."""
    trellis, _ = cons_then_port(cons, port)
    assert (len(trellis["periods"]), trellis["inter_connectors"]) == (1, [])


def test_accrete_admits_a_mapping_of_unknown_fields_and_the_report_names_each_endpoint(cons, port):
    """accrete admits a mapping whose fields name no field of the two
    periods, and the connection report of the trellis names each unresolved
    endpoint at the mapping and selects no pair."""
    trellis, _ = cons_then_port(cons, port)
    unfinished = accrete(trellis, {"stages": {"port": port}, "connectors": []}, {"a": "k"})
    report = connection_report(unfinished)
    assert [(d.rule, d.address) for d in report.diagnostics] == [
        ("endpoint-unresolved", "inter_connectors[0]")
    ] * 2
    assert "'a'" in report.diagnostics[0].message
    assert "continuation" in report.diagnostics[0].message
    assert unfinished["inter_connectors"] == [{"a": "k"}] and report.pairs == ()


def test_accrete_appends_a_record_as_a_copy(cons, port):
    """accrete appends a record of a stage text as an equal copy of the
    record."""
    _, later = cons_then_port(cons, port)
    period = {"stages": {"t": RECORD_OF_A_STAGE_TEXT}, "connectors": []}
    appended = accrete(later, period)["periods"][2]["stages"]["t"]
    assert appended == RECORD_OF_A_STAGE_TEXT and appended is not RECORD_OF_A_STAGE_TEXT


def test_accrete_without_a_mapping_joins_the_appended_period_by_the_empty_mapping(cons, port):
    """accrete given no inter-period mapping writes the empty mapping
    between the appended period and the one after it."""
    _, later = cons_then_port(cons, port)
    with_record = accrete(later, {"stages": {"t": RECORD_OF_A_STAGE_TEXT}, "connectors": []})
    assert with_record["inter_connectors"] == [{"m_next": "m"}, {}]


def test_accrete_refuses_a_mapping_given_with_the_terminal_period():
    """accrete refuses under `trellis-file-shape` an inter-period mapping
    given with the first period that it appends, the terminal one."""
    with pytest.raises(FactoryError, match="terminal period") as refused:
        accrete(
            {"periods": [], "inter_connectors": []}, {"stages": {}, "connectors": []}, {"a": "k"}
        )
    assert (refused.value.rule, refused.value.address) == (
        "trellis-file-shape",
        "inter_connectors",
    )


def test_accrete_refuses_an_inter_period_mapping_that_is_no_mapping(cons, port):
    """accrete refuses a list in place of an inter-period mapping, saying that
    it writes a mapping from continuation fields to arrival fields."""
    trellis, _ = cons_then_port(cons, port)
    with pytest.raises(FactoryError, match="a mapping from continuation fields") as refused:
        accrete(trellis, {"stages": {}, "connectors": []}, ["a", "k"])
    assert refused.value.write == "{<continuation field>: <arrival field>}"


def test_load_trellis_expands_a_template_and_repeats_its_one_inter_period_mapping(written_out):
    """load_trellis reads one written period and a template repeated twice
    as three periods, the one inter-period mapping standing for each pair."""
    assert len(written_out["periods"]) == 3
    assert written_out["inter_connectors"] == [{"a": "m"}, {"a": "m"}]


def test_load_trellis_reads_a_written_out_record_with_its_stage_values_and_methods_file(
    written_out, corpus_path
):
    """The written-out record that load_trellis reads holds the origin of
    its stage file, the values of its calibration file, its inline settings
    and the origin of its methods file."""
    record = written_out["periods"][0]["stages"]["cons"]
    assert record["stage"]["origin"] == str(corpus_path("cons"))
    assert record["calibration"] == {"ρ": 4.0} and record["settings"] == {"n_m": 10}
    assert [addition["origin"] for addition in record["methods"]] == [str(CONS_METHODS)]


def test_the_provenance_of_a_written_out_record_names_the_files_that_it_reads(
    written_out, written_out_folder
):
    """The provenance of the written-out record names its calibration file
    and no settings file, since its settings are written inline."""
    lists = written_out["periods"][0]["stages"]["cons"]["provenance"]["source_lists"]
    assert lists["calibration"][0]["path"] == str(written_out_folder / "ρ.yml")
    assert lists["settings"] == []


def test_a_record_that_names_no_methods_is_read_with_no_methods_file(written_out):
    """The records that the template repeats, which name no methods, are
    read with an empty list of methods files at both periods."""
    assert written_out["periods"][1]["stages"]["cons"]["methods"] == []
    assert written_out["periods"][2]["stages"]["cons"]["methods"] == []


def test_load_trellis_records_the_path_of_the_trellis_file(written_out, written_out_folder):
    """The provenance of the syntactic trellis that load_trellis reads holds
    the path of the trellis file."""
    assert written_out["provenance"]["trellis"]["path"] == str(written_out_folder / "trellis.yml")


def test_one_inter_period_mapping_with_one_period_stands_for_no_pair(written_out_folder):
    """load_trellis reads a template repeated once with one inter-period
    mapping as one period with no mapping, since one period has no pair."""
    one = load_trellis(written_out_folder / "one.yml")
    assert (len(one["periods"]), one["inter_connectors"]) == (1, [])


def test_load_trellis_refuses_a_file_that_writes_no_periods(written_out_folder):
    """load_trellis refuses under `trellis-file-shape` a file that writes no
    list of periods, naming the periods."""
    with pytest.raises(FactoryError) as refused:
        load_trellis(written_out_folder / "no-periods.yml")
    assert refused.value.rule == "trellis-file-shape" and "periods" in refused.value.message


def test_load_trellis_reads_each_methods_file_of_a_list_with_its_text_origin_and_path(
    methods_list_record,
):
    """load_trellis reads each methods file that a record lists as its text
    and its origin, with its path in the record's provenance."""
    assert methods_list_record["methods"] == [
        {"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": str(CONS_METHODS)}
    ]
    lists = methods_list_record["provenance"]["source_lists"]
    assert [entry["path"] for entry in lists["methods"]] == [str(CONS_METHODS)]


def test_load_trellis_reads_one_methods_file_as_a_list_of_one(methods_folder, methods_list_record):
    """load_trellis reads a record's methods written as one path as the list
    of that one methods file."""
    record = load_trellis(methods_folder / "one.yml")["periods"][0]["stages"]["cons"]
    assert record["methods"] == methods_list_record["methods"]


def test_load_trellis_refuses_a_mapping_in_place_of_the_methods_files(methods_folder):
    """load_trellis refuses under `trellis-file-shape` a record whose methods
    are a mapping, saying that it names `.bl` methods files."""
    with pytest.raises(FactoryError) as refused:
        load_trellis(methods_folder / "inline.yml")
    assert refused.value.rule == "trellis-file-shape" and "`.bl` addition" in refused.value.message


def test_both_stages_that_declare_beta_hold_the_value_that_one_source_supplies(
    shared_beta_trellis,
):
    """Both stages of each period that declare β hold the value 0.96 of the
    two-node stage's calibration file, the discounting stage's list holding
    an unfilled slot alone."""
    _, specified = shared_beta_trellis
    for period in specified["periods"]:
        assert [dict(stage.bindings.calibration) for stage in period["stages"].values()] == [
            {"β": 0.96, "R": 1.02},
            {"β": 0.96},
        ]
        assert period["stages"]["disc"].par["β"].value == 0.96


def test_two_sources_of_a_shared_parameter_agree_on_one_value_and_are_refused_on_two(
    shared_beta_registry, shared_beta_trellis
):
    """The discounting stage's slot filled with the value 0.96 that the
    two-node stage's file supplies binds both stages as the file alone does,
    and filled with 0.5 is refused under `period-parameter-agreement`, naming
    both values with their sources and, in its notes, the discounting
    stage's position and the kind."""
    _, specified = shared_beta_trellis
    agreed = assemble_trellis(shared_beta_registry, "spec.yml", disc_fill={"β": 0.96})
    assert [
        [dict(stage.bindings.calibration) for stage in period["stages"].values()]
        for period in agreed["periods"]
    ] == [
        [dict(stage.bindings.calibration) for stage in period["stages"].values()]
        for period in specified["periods"]
    ]
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(shared_beta_registry, "spec.yml", disc_fill={"β": 0.5})
    assert (refused.value.rule, refused.value.address) == (
        "period-parameter-agreement",
        "periods[0]",
    )
    assert refused.value.written == "β: 0.96 (calibration/main, $fill); 0.5 ($disc_fill)"
    assert "supply the parameter 'β' with the values 0.96 and 0.5" in refused.value.message
    assert refused.value.__notes__ == [
        "Stage occurrence: periods[0].stages['disc']",
        "Binding kind: calibration",
    ]


def test_a_value_that_both_sources_supply_in_place_of_the_files_binds_both_stages(
    shared_beta_registry,
):
    """The value 0.5, which lies in both ℝ₊₊ and (0,1), supplied by both
    stages' sources in place of the file's 0.96 binds both stages."""
    both = assemble_trellis(
        shared_beta_registry, "spec.yml", fill={"β": 0.5}, disc_fill={"β": 0.5}
    )
    assert [stage.par["β"].value for stage in both["periods"][0]["stages"].values()] == [0.5, 0.5]


def test_calibrate_trellis_binds_a_filled_shared_parameter_at_both_stages(filled_shared_beta):
    """calibrate_trellis binds the fill β = 0.9 of the two-node stage's list
    at both stages of a period."""
    _, direct = filled_shared_beta
    assert [
        dict(stage.bindings.calibration) for stage in direct["periods"][1]["stages"].values()
    ] == [
        {"β": 0.9, "R": 1.02},
        {"β": 0.9},
    ]


def test_calibrate_trellis_and_specify_trellis_bind_the_same_values_of_a_shared_parameter(
    filled_shared_beta,
):
    """At every position, the calibration that calibrate_trellis binds from
    the fill is already bound as specify_trellis of the calibration binds
    it."""
    filled, direct = filled_shared_beta
    by_specify_trellis = specify_trellis(filled, kinds=["calibration"])
    assert all(
        already_bound(
            direct["periods"][h]["stages"][key],
            "calibration",
            by_specify_trellis["periods"][h]["stages"][key].bindings.calibration,
        )
        for h in range(2)
        for key in ("two_nodes", "disc")
    )


def test_the_same_parameter_name_in_another_period_is_another_parameter(tmp_path):
    """Where the discounting stage stands in the terminal period alone, the
    terminal period's β takes its own value 0.5 at both stages, and the
    two-node stage of the period before keeps the file's 0.96."""
    spec = (
        SHARED_BETA_REGISTRY["spec.yml"]
        .replace(
            "calibration: {all: [calibration/main, $fill]}",
            "calibration: {all: [calibration/main, $fill], '0-0': [calibration/terminal]}",
        )
        .replace(
            "stage: stages/disc/disc.bl\n", "stage: stages/disc/disc.bl\n    periods: [0, 0]\n"
        )
    )
    trellis = (
        "periods:\n  - {stages: [two_nodes, disc], connectors: []}\n"
        "  - {template: period.yml, repeat: 1}\ninter_connectors:\n  - {a: k}\n"
    )
    files = {
        **SHARED_BETA_REGISTRY,
        "calibration/terminal.yml": "calibration:\n  β: 0.5\n",
        "period.yml": "name: one\nstages: [two_nodes]\nconnectors: []\n",
        "trellis.yml": trellis,
        "spec.yml": spec,
    }
    periods = assemble_trellis(write_registry(tmp_path / "apart", files), "spec.yml")["periods"]
    assert [stage.par["β"].value for stage in periods[0]["stages"].values()] == [0.5, 0.5]
    assert [stage.par["β"].value for stage in periods[1]["stages"].values()] == [0.96]


def test_a_changed_value_of_a_shared_parameter_binds_again_both_stages_of_each_period(
    shared_beta_trellis, respecified_shared_beta
):
    """A fill that changes β through the two-node stage's list binds again
    the discounting stage of each period too, whose record is unchanged,
    with the new value."""
    _, specified = shared_beta_trellis
    _, again = respecified_shared_beta
    assert changed_positions(specified, again) == [
        (0, "two_nodes"),
        (0, "disc"),
        (1, "two_nodes"),
        (1, "disc"),
    ]
    assert [stage.par["β"].value for stage in again["periods"][1]["stages"].values()] == [0.9, 0.9]


def test_respecify_trellis_after_a_change_of_a_shared_parameter_answers_what_specify_answers(
    respecified_shared_beta,
):
    """After a change of β, respecify_trellis answers each stage occurrence
    that specify_trellis answers for the new recipe, as the standard pickle
    writes them."""
    after, again = respecified_shared_beta
    whole = specify_trellis(after)
    for place in positions(whole):
        answered = again["periods"][place.h]["stages"][place.key]
        assert pickle.dumps(answered) == pickle.dumps(place.stage), (place.h, place.key)


def test_a_fill_of_the_value_that_a_shared_parameter_holds_binds_again_only_the_changed_record(
    shared_beta_registry, shared_beta_trellis
):
    """A fill of the value 0.96 that both stages hold changes the two-node
    stage's record alone, so respecify_trellis binds that stage again and
    keeps the discounting stage's very occurrences."""
    before, specified = shared_beta_trellis
    filled = load_recipe(shared_beta_registry, "spec.yml", fill={"β": 0.96})
    same = respecify_trellis(specified, before, filled)
    assert changed_positions(specified, same) == [(0, "two_nodes"), (1, "two_nodes")]
    assert all(
        same["periods"][h]["stages"]["disc"] is specified["periods"][h]["stages"]["disc"]
        for h in range(2)
    )


def test_specify_trellis_with_a_previous_trellis_refuses_two_values_of_a_shared_parameter(
    shared_beta_trellis, retained_after_refusal
):
    """specify_trellis with a previous trellis refuses under
    `period-parameter-agreement` two values of β, its notes naming the
    discounting stage's position and the kind."""
    _, specified = shared_beta_trellis
    requested, _ = retained_after_refusal
    with pytest.raises(FactoryError) as refused:
        specify_trellis(requested, specified)
    assert refused.value.rule == "period-parameter-agreement"
    assert refused.value.__notes__ == [
        "Stage occurrence: periods[0].stages['disc']",
        "Binding kind: calibration",
    ]


def test_the_methods_and_settings_bound_after_a_refused_calibration_keep_every_occurrence(
    shared_beta_trellis, retained_after_refusal
):
    """specify_trellis of the methods and the settings alone, after the
    calibration of the recipe is refused, keeps every stage occurrence of
    the previous trellis."""
    _, specified = shared_beta_trellis
    _, retained = retained_after_refusal
    assert changed_positions(specified, retained) == []


def test_already_bound_tells_the_values_kept_after_a_refused_calibration_from_those_requested(
    retained_after_refusal,
):
    """The occurrences kept after a refused calibration hold the earlier
    value 0.96, which already_bound says is not the value that the recipe
    requests at the discounting stage."""
    requested, retained = retained_after_refusal
    for h, period in enumerate(retained["periods"]):
        for key, stage in period["stages"].items():
            assert stage.par["β"].value == 0.96
            calibration = requested["periods"][h]["stages"][key]["calibration"]
            assert not already_bound(stage, "calibration", calibration) or key == "two_nodes"
    disc = retained["periods"][0]["stages"]["disc"]
    calibration = requested["periods"][0]["stages"]["disc"]["calibration"]
    assert not already_bound(disc, "calibration", calibration)


def test_two_declared_sets_whose_intersection_the_package_does_not_read_are_refused(tmp_path):
    """The elaboration refuses under `period-parameter-agreement` the sets ℝ₊₊
    and ℤ that two stages of a period declare for β, naming the parameter,
    the stages and their sets, with no notes."""
    integers = registry_declaring_beta(tmp_path, "β : ℝ₊₊", "β : ℤ")
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis(load_recipe(integers, "spec.yml"))
    assert (refused.value.rule, refused.value.address) == (
        "period-parameter-agreement",
        "periods[0]",
    )
    assert refused.value.written == "β : ℝ₊₊ in two_nodes; β : ℤ in disc"
    phrases = ("two_nodes", "disc", "'β'", "reads no intersection")
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert not hasattr(refused.value, "__notes__")


def test_a_value_outside_the_set_that_another_declaring_stage_writes_is_refused(tmp_path):
    """The value 0 of β, which lies in the discounting stage's ℝ₊ but outside
    the two-node stage's ℝ₊₊, is refused, the notes naming the two-node
    stage's position and the kind."""
    widened = registry_declaring_beta(tmp_path, "β : ℝ₊₊", "β : ℝ₊")
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(widened, "spec.yml", fill={"β": 0.0}, disc_fill={"β": 0.0})
    assert refused.value.written == "β: 0.0 (calibration/main, $fill); β : ℝ₊₊ in two_nodes"
    assert (
        "the value 0.0 of the parameter 'β', supplied by two_nodes, lies outside the set ℝ₊₊"
        in refused.value.message
    )
    assert refused.value.__notes__ == [
        "Stage occurrence: periods[0].stages['two_nodes']",
        "Binding kind: calibration",
    ]


def test_two_stages_agree_on_one_union_in_either_order_and_are_refused_on_two_unions(
    one_union_registry, tmp_path
):
    """Two stages that declare β in one union, its members written in either
    order, elaborate and bind 0.5 at both, and two different unions are
    refused under `period-parameter-agreement`, since the package reads no
    intersection of them."""
    elaborate_trellis(load_recipe(one_union_registry, "spec.yml"))
    bound = assemble_trellis(one_union_registry, "spec.yml", fill={"β": 0.5}, disc_fill={"β": 0.5})
    stages = bound["periods"][0]["stages"].values()
    assert [stage.par["β"].value for stage in stages] == [0.5, 0.5]
    different = registry_declaring_beta(
        tmp_path, "β : (0,1) \\/ (1, inf)", "β : (0,1) \\/ (2, inf)"
    )
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis(load_recipe(different, "spec.yml"))
    error = refused.value
    assert (error.rule, error.address) == ("period-parameter-agreement", "periods[0]")
    assert error.written == "β : (0, 1) \\/ (1, inf) in two_nodes; β : (0, 1) \\/ (2, inf) in disc"
    assert "reads no intersection" in error.message


def test_a_value_outside_the_union_that_two_stages_declare_is_refused_for_the_period(
    one_union_registry,
):
    """The value 1.0, outside the union of (0,1) and (1, inf) that both stages
    declare, is refused for the period before any stage binds it."""
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(one_union_registry, "spec.yml", fill={"β": 1.0}, disc_fill={"β": 1.0})
    assert (refused.value.rule, refused.value.address) == (
        "period-parameter-agreement",
        "periods[0]",
    )
    assert (
        "the value 1.0 of the parameter 'β', supplied by two_nodes, lies outside the set "
        "(0, 1) \\/ (1, inf)"
    ) in refused.value.message


def test_a_name_inside_a_union_is_read_as_the_set_that_its_own_stage_defines(tmp_path):
    """A union that one stage writes through a name and the other in full is
    one set of the period: the trellis elaborates, and a value outside the
    set is refused with the set as the two-node stage reads it."""
    named = "Xb := [0,1)\nβ : Xb \\/ (1, inf)"
    through = registry_declaring_beta(tmp_path, named, "β : [0,1) \\/ (1, inf)")
    elaborate_trellis(load_recipe(through, "spec.yml"))
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(through, "spec.yml", fill={"β": 1.0}, disc_fill={"β": 1.0})
    assert (refused.value.rule, refused.value.address) == (
        "period-parameter-agreement",
        "periods[0]",
    )
    assert "lies outside the set (1, inf) \\/ [0, 1) that two_nodes" in refused.value.message


@pytest.mark.parametrize(
    ("declared", "first", "second"),
    [
        pytest.param(
            "(1, inf) \\/ Xb",
            "(1, inf) \\/ [0, 1)",
            "(1, inf) \\/ [0, 2)",
            id="union-through-a-name",
        ),
        pytest.param(
            "Xb @ (0, 5)", "[0, 1) @ (0, 5)", "[0, 2) @ (0, 5)", id="name-bounded-by-a-second-set"
        ),
    ],
)
def test_one_text_that_two_stages_read_as_two_sets_is_refused(tmp_path, declared, first, second):
    """One declaration of β whose name Xb each stage defines as another set
    is refused, each set quoted as written and as its stage reads it."""
    renamed = registry_declaring_beta(
        tmp_path, f"Xb := [0,1)\nβ : {declared}", f"Xb := [0,2)\nβ : {declared}"
    )
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis(load_recipe(renamed, "spec.yml"))
    error = refused.value
    assert (error.rule, error.address) == ("period-parameter-agreement", "periods[0]")
    assert error.written == f"β : {declared} in two_nodes; β : {declared} in disc"
    assert (
        f"with the sets {declared}, read in two_nodes as {first}, and {declared}, read in "
        f"disc as {second}, and the package reads no intersection of them"
    ) in error.message
