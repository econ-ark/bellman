"""The connections of a trellis read from the files of its model and written
into them: how often one reading selects the connections and constructs a
stage, the entry that each authored pair records and the file that writes
that entry, and the connector entry that writes a new pair, with the
spelling that it writes, the reason that it answers and the pairs that it
may replace or extend. Where a connector entry writes its line in the
application models is tested in test_trellis_entries.py, and so is one test
of the spelling of a shared name, which carries a strict mark of expected
failure.

A field use is a state field of a stage occurrence at its arrival perch or at
its continuation perch, and a selection holds every field use of the
trellis. A connector in the keyed form, `{from: S, to: T, fields: {a: b}}`,
names its two stages once; a flat connector, `{S.a: T.b}`, writes the stage
key before an endpoint where the endpoint needs it."""

import re
from pathlib import Path

import pytest
import yaml
from application_files import DURABLES
from model_explorer_views import needs_viewer
from stage_builders import stage_from_text
from stage_texts import DISC_WITH_K_NEXT_TEXT, TWO_FIELDS, UNCHANGED, renamed
from trellises import (
    SIX_PERIODS,
    period_record,
    port_cons_vfi_trellis_file_without_connectors,
    write_files,
)

from bellman.factory.connections import select_connections
from bellman.factory.trellis import construct_stage
from bellman.trellis import (
    append_to_mapping,
    append_to_sequence,
    connection_report,
    connector_entry,
    diagram_trellis,
    elaborate_trellis,
    entry_value,
    load_recipe,
    load_trellis,
    remove_from_mapping,
    specify_trellis,
    to_model_explorer,
    unjoined_fields,
    unpaired_joins,
    written_at,
)

# a registry of three periods of the two-field stage `s`, the stage `u` that
# carries `a` unchanged and the discounting stage `d`, whose period file holds
# one empty connector and whose trellis file holds one empty inter-period
# connector: `s` continues to `a` and `b`, `u` to `a` and `d` to `k_next`, and
# all three arrive at `a`
THREE_PERIOD_REGISTRY = {
    "stages/s/s.bl": renamed(TWO_FIELDS, "s"),
    "stages/u/u.bl": renamed(UNCHANGED, "u"),
    "stages/d/d.bl": DISC_WITH_K_NEXT_TEXT,
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

# the start of a trellis file whose one period template holds the two-field
# stage under the keys `S` and `T`
TWO_FIELD_PERIOD = "periods:\n  - stages: {S: {stage: two_fields.bl}, T: {stage: two_fields.bl}}\n"

# the stage that carries `b` unchanged: the stage that carries `a` unchanged,
# its field renamed
UNCHANGED_B = re.sub(r"\ba\b", "b", UNCHANGED)


def folder_with_two_fields(tmp_path_factory, name, trellis_text):
    """A new folder that holds the two-field stage file and a trellis file
    of the text `trellis_text`; answers the trellis file."""
    folder = tmp_path_factory.mktemp(name)
    (folder / "two_fields.bl").write_text(TWO_FIELDS)
    trellis_file = folder / "trellis.yml"
    trellis_file.write_text(trellis_text)
    return trellis_file


@pytest.fixture(scope="module")
def registry_folder(tmp_path_factory):
    """The folder that holds the files of the registry of three periods."""
    return write_files(tmp_path_factory.mktemp("registry"), THREE_PERIOD_REGISTRY)


@pytest.fixture(scope="module")
def specified_registry(registry_folder):
    """The trellis of the registry, read from its recipe and specified."""
    return specify_trellis(load_recipe(registry_folder, "spec.yml"))


@pytest.fixture(scope="module")
def registry_report(specified_registry):
    """The connection report of the specified trellis of the registry."""
    return connection_report(specified_registry)


@pytest.fixture
def readings(monkeypatch):
    """The selections of connections and the constructions of stages that
    the package makes while a test runs, recorded in two lists: each
    selection by its periods and each construction by the origin of its
    stage text."""
    selections, constructions = [], []

    def counted_selection(*arguments, **keywords):
        selections.append(arguments[0])
        return select_connections(*arguments, **keywords)

    def counted_construction(text, origin, additions=()):
        constructions.append(origin)
        return construct_stage(text, origin, additions)

    for module in ("bellman.factory.connections", "bellman.factory.joins"):
        monkeypatch.setattr(f"{module}.select_connections", counted_selection)
    monkeypatch.setattr("bellman.factory.trellis.construct_stage", counted_construction)
    return selections, constructions


@pytest.fixture(scope="module")
def written_entry_texts(registry_folder):
    """The text of the registry's period file with the entry `{b: u.a}`
    written into its empty connector, by the file's resolved path."""
    path = registry_folder / "period.yml"
    text = path.read_text(encoding="utf-8")
    return {str(path.resolve()): text.replace("- {}", "- {b: u.a}")}


@pytest.fixture(scope="module")
def registry_with_written_entry(registry_folder, written_entry_texts):
    """The trellis of the registry specified again with that text in place
    of the period file."""
    return specify_trellis(load_recipe(registry_folder, "spec.yml", written_entry_texts))


@pytest.fixture(scope="module")
def repeated_period_folder(tmp_path_factory):
    """A folder of the two-field stage file, a period file whose connector
    in the keyed form from `S` to `T` maps `a` to `b` and `b` to `q`, which
    names no field, and a trellis file that repeats that period twice."""
    folder = tmp_path_factory.mktemp("repeated")
    (folder / "two_fields.bl").write_text(TWO_FIELDS, encoding="utf-8")
    period = {
        "stages": {key: {"stage": "two_fields.bl"} for key in ("S", "T")},
        "connectors": [{"from": "S", "to": "T", "fields": {"a": "b", "b": "q"}}],
    }
    (folder / "period.yml").write_text(yaml.safe_dump(period, sort_keys=False), encoding="utf-8")
    (folder / "trellis.yml").write_text(
        "periods:\n  - {template: period.yml, repeat: 2}\ninter_connectors: []\n",
        encoding="utf-8",
    )
    return folder


@pytest.fixture(scope="module")
def repeated_period_report(repeated_period_folder):
    """The connection report of that trellis, restricted to its second
    period, `periods[1]`."""
    trellis = elaborate_trellis(load_trellis(repeated_period_folder / "trellis.yml"))
    return connection_report(trellis, periods=[1])


# each spelling of the two crossed pairs of the two stages under the row's
# `keys`, the source first, in a trellis of three periods made from one
# template, as a connector of the period or as the inter-period connector;
# what the pair of the source's field `a` in the earliest period records, its
# address and the address, the key and the value of its entry in the expanded
# trellis; and the file and the address that write that entry
CROSSED_PAIR_SPELLINGS = [
    pytest.param(
        {
            "keys": ("S", "T"),
            "connector": {"S.a": "T.b", "S.b": "T.a"},
            "between": False,
            "recorded": (
                "periods[2].connectors[0]",
                "periods[2].connectors[0]",
                "S.a",
                "T.b",
            ),
            "written": ("period.yml", "connectors[0]"),
        },
        id="endpoints-after-their-stage-keys",
    ),
    pytest.param(
        {
            "keys": ("S", "T"),
            "connector": {"from": "S", "to": "T", "fields": {"a": "b", "b": "a"}},
            "between": False,
            "recorded": (
                "periods[2].connectors[0]",
                "periods[2].connectors[0].fields",
                "a",
                "b",
            ),
            "written": ("period.yml", "connectors[0].fields"),
        },
        id="keyed-form",
    ),
    pytest.param(
        {
            "keys": ("S.inner", "T.inner"),
            "connector": {"S.inner.a": "T.inner.b", "S.inner.b": "T.inner.a"},
            "between": False,
            "recorded": (
                "periods[2].connectors[0]",
                "periods[2].connectors[0]",
                "S.inner.a",
                "T.inner.b",
            ),
            "written": ("period.yml", "connectors[0]"),
        },
        id="stage-keys-that-hold-a-dot",
    ),
    pytest.param(
        {
            "keys": ("S.inner", "T.inner"),
            "connector": {"S.inner.a": "T.inner.b", "S.inner.b": "T.inner.a"},
            "between": True,
            "recorded": ("inter_connectors[1]", "inter_connectors[1]", "S.inner.a", "T.inner.b"),
            "written": ("trellis.yml", "inter_connectors[0]"),
        },
        id="stage-keys-that-hold-a-dot-in-the-inter-period-connector",
    ),
]


@pytest.fixture(scope="module", params=CROSSED_PAIR_SPELLINGS)
def spelled_pair(request, tmp_path_factory):
    """One spelling of the crossed pairs, written into a folder of its own:
    the trellis file and the file that holds the connector, with its text,
    the selection of the trellis and the pair of the source's `a` in the
    earliest period."""
    row = request.param
    folder = tmp_path_factory.mktemp("spelling")
    (folder / "two_fields.bl").write_text(TWO_FIELDS, encoding="utf-8")
    period_text = yaml.safe_dump(
        {
            "stages": {key: {"stage": "two_fields.bl"} for key in row["keys"]},
            "connectors": [] if row["between"] else [row["connector"]],
        },
        sort_keys=False,
    )
    (folder / "period.yml").write_text(period_text, encoding="utf-8")
    trellis_text = yaml.safe_dump(
        {
            "periods": [{"template": "period.yml", "repeat": 3}],
            "inter_connectors": [row["connector"]] if row["between"] else [],
        },
        sort_keys=False,
    )
    trellis_file = folder / "trellis.yml"
    trellis_file.write_text(trellis_text, encoding="utf-8")
    selected = connection_report(elaborate_trellis(load_trellis(trellis_file))).selection
    return {
        "row": row,
        "folder": folder,
        "trellis_file": trellis_file,
        "source_file": folder / row["written"][0],
        "source_text": trellis_text if row["between"] else period_text,
        "selected": selected,
        "pair": next(p for p in selected.pairs if p.writing.h == 2 and p.writing.field == "a"),
    }


@pytest.fixture(scope="module")
def inferred_folder(tmp_path_factory):
    """A folder of the stage files `S.bl`, `T.bl` and `U.bl` and a trellis
    file of one period of the three with no connector: `S` continues to `a`
    in ℝ₊₊, `T` arrives at `a` in ℝ₊ and `U` arrives at `b`."""
    folder = tmp_path_factory.mktemp("inferred")
    for key, text in (
        ("S", UNCHANGED.replace("ℝ₊", "ℝ₊₊")),
        ("T", UNCHANGED),
        ("U", UNCHANGED_B),
    ):
        (folder / f"{key}.bl").write_text(text)
    (folder / "trellis.yml").write_text(
        "periods:\n  - stages: {S: {stage: S.bl}, T: {stage: T.bl}, U: {stage: U.bl}}\n"
        "    connectors: []\ninter_connectors: []\n"
    )
    return folder


@pytest.fixture(scope="module")
def inferred_trellis(inferred_folder, strictly_positive_identity_stage, identity_stage):
    """The elaborated trellis of the same three stages, whose provenance
    names the trellis file of that folder."""
    third = stage_from_text(UNCHANGED_B, "third.bl")
    return elaborate_trellis(
        {
            "periods": [
                period_record(
                    {"S": strictly_positive_identity_stage, "T": identity_stage, "U": third}
                )
            ],
            "inter_connectors": [],
            "provenance": {"trellis": {"path": str(inferred_folder / "trellis.yml")}},
        }
    )


@pytest.fixture(scope="module")
def inferred_selection(inferred_trellis):
    """The selection of that trellis, whose one pair is inferred from `S` to
    `T`."""
    return connection_report(inferred_trellis).selection


@pytest.fixture(scope="module")
def replacing_entry(inferred_trellis, inferred_selection):
    """The connector entry from `S`'s `a` to `U`'s `b` that replaces the
    inferred pair."""
    (inferred,) = inferred_selection.pairs
    return connector_entry(
        inferred_trellis,
        (0, "S", "a"),
        (0, "U", "b"),
        selection=inferred_selection,
        replacing=(inferred,),
    )


@pytest.fixture(scope="module")
def proposed_report(inferred_trellis, replacing_entry):
    """The connection report of the trellis whose period holds the text of
    the replacing entry as its connector."""
    period = dict(
        inferred_trellis["periods"][0], connectors=[yaml.safe_load(replacing_entry.text)]
    )
    return connection_report({**inferred_trellis, "periods": [period]})


@pytest.fixture(scope="module")
def appended_file(inferred_folder, replacing_entry):
    """A copy of the trellis file, beside it, with the replacing entry
    appended at the entry's address."""
    text = (inferred_folder / "trellis.yml").read_text()
    path = inferred_folder / "appended.yml"
    path.write_text(append_to_sequence(text, replacing_entry.address, replacing_entry.text))
    return path


# the connector of the period between `S` and `T` that maps `a` to `b`, flat
# or in the keyed form; the address at which the entry of a second
# coordinate, `S`'s `b` to `T`'s `a`, extends it, that entry's text, and the
# connector once the entry is appended
CONNECTORS_TO_EXTEND = [
    pytest.param(
        (
            "{S.a: T.b}",
            "periods[0].connectors[0]",
            "{S.b: T.a}",
            {"S.a": "T.b", "S.b": "T.a"},
        ),
        id="flat-connector",
    ),
    pytest.param(
        (
            "{from: S, to: T, fields: {a: b}}",
            "periods[0].connectors[0].fields",
            "{b: a}",
            {"from": "S", "to": "T", "fields": {"a": "b", "b": "a"}},
        ),
        id="keyed-form",
    ),
]


@pytest.fixture(scope="module", params=CONNECTORS_TO_EXTEND)
def extendable_trellis(request, tmp_path_factory):
    """A trellis file of two periods whose connector maps `S`'s `a` to `T`'s
    `b`, with the row, the file and its elaborated trellis."""
    connector = request.param[0]
    trellis_file = folder_with_two_fields(
        tmp_path_factory,
        "extended",
        TWO_FIELD_PERIOD + f"    connectors: [{connector}]\n    repeat: 2\ninter_connectors: []\n",
    )
    return {
        "row": request.param,
        "trellis_file": trellis_file,
        "trellis": elaborate_trellis(load_trellis(trellis_file)),
    }


@pytest.fixture(scope="module")
def extended_trellis(extendable_trellis):
    """That trellis read again once the connector entry of `S`'s `b` and
    `T`'s `a` is appended to its connector, the text written beside the
    trellis file as `extended.yml`."""
    entry = connector_entry(extendable_trellis["trellis"], (0, "S", "b"), (0, "T", "a"))
    text = extendable_trellis["trellis_file"].read_text()
    for field, arrival in yaml.safe_load(entry.text).items():
        text = append_to_mapping(text, entry.address, field, arrival)
    path = extendable_trellis["trellis_file"].with_name("extended.yml")
    path.write_text(text)
    return elaborate_trellis(load_trellis(path))


# an entry from `S` that maps `a` to `T.b` and `b` to `q`, which names no
# field, written as a flat connector of the period, in the keyed form, or as
# the inter-period connector; the continuation field asked for, the address
# of the entry, the connectors that the entry stands among, `periods` for the
# connectors of each period or `inter_connectors`, and what the trellis holds
# there, and the number of unresolved endpoints
ENTRIES_WITH_A_FAILED_TARGET = [
    pytest.param(
        {
            "written": "    connectors: [{S.a: T.b, S.b: q}]\n"
            "    repeat: 2\ninter_connectors: []\n",
            "writing": (0, "S", "b"),
            "address": "periods[0].connectors[0]",
            "side": "periods",
            "held": [[{"S.a": "T.b", "S.b": "q"}]] * 2,
            "unresolved": 2,
        },
        id="flat-connector",
    ),
    pytest.param(
        {
            "written": "    connectors: [{from: S, to: T, fields: {a: b, b: q}}]\n"
            "    repeat: 2\ninter_connectors: []\n",
            "writing": (0, "S", "b"),
            "address": "periods[0].connectors[0].fields",
            "side": "periods",
            "held": [[{"from": "S", "to": "T", "fields": {"a": "b", "b": "q"}}]] * 2,
            "unresolved": 2,
        },
        id="keyed-form",
    ),
    pytest.param(
        {
            "written": "    connectors: []\n"
            "    repeat: 2\ninter_connectors: [{S.a: T.b, S.b: q}]\n",
            "writing": (1, "S", "b"),
            "address": "inter_connectors[0]",
            "side": "inter_connectors",
            "held": [{"S.a": "T.b", "S.b": "q"}],
            "unresolved": 1,
        },
        id="inter-period-connector",
    ),
]


@pytest.fixture(scope="module", params=ENTRIES_WITH_A_FAILED_TARGET)
def failed_target_trellis(request, tmp_path_factory):
    """The row, the trellis file of the row, its text, its trellis and the
    connection report of that trellis."""
    row = request.param
    text = TWO_FIELD_PERIOD + row["written"]
    trellis_file = folder_with_two_fields(tmp_path_factory, "failed", text)
    trellis = elaborate_trellis(load_trellis(trellis_file))
    return {
        "row": row,
        "trellis_file": trellis_file,
        "text": text,
        "trellis": trellis,
        "before": connection_report(trellis),
    }


@pytest.fixture(
    scope="module",
    params=[(False, "periods[0].connectors[0]"), (True, "inter_connectors[0]")],
    ids=["in-the-period", "in-the-inter-period-connector"],
)
def ambiguous_key_trellis(request, tmp_path_factory):
    """The entry `{S.a: T.b, b: q}`, whose key `b` both stages continue to,
    written in the connector of the period or in the inter-period connector:
    the period of the writing field asked for, the address of the entry, the
    text, the trellis and its connection report."""
    between, address = request.param
    connector = "{S.a: T.b, b: q}"
    text = TWO_FIELD_PERIOD + (
        f"    connectors: {'[]' if between else '[' + connector + ']'}\n    repeat: 2\n"
        f"inter_connectors: {'[' + connector + ']' if between else '[]'}\n"
    )
    trellis_file = folder_with_two_fields(tmp_path_factory, "ambiguous", text)
    trellis = elaborate_trellis(load_trellis(trellis_file))
    return {
        "h": int(between),
        "address": address,
        "trellis_file": trellis_file,
        "text": text,
        "trellis": trellis,
        "before": connection_report(trellis),
    }


@pytest.fixture(scope="module")
def appended_beside_ambiguous_key(ambiguous_key_trellis):
    """The text of that file with `S.b: T.a` appended to the entry, written
    beside it as `appended.yml`, and the connection report of the trellis
    read from it."""
    text = ambiguous_key_trellis["text"]
    after_text = append_to_mapping(text, ambiguous_key_trellis["address"], "S.b", "T.a")
    path = ambiguous_key_trellis["trellis_file"].with_name("appended.yml")
    path.write_text(after_text)
    return {
        "after_text": after_text,
        "after": connection_report(elaborate_trellis(load_trellis(path))),
    }


@pytest.fixture(scope="module")
def durables_text():
    """The text of the durables model's trellis file with its template
    repeated twice in place of fifty times."""
    return (
        (DURABLES / "trellis.yml")
        .read_text(encoding="utf-8")
        .replace("{template: period.yml, repeat: 50}", "{template: period.yml, repeat: 2}")
    )


@pytest.fixture(scope="module")
def port_cons_vfi_trellis_without_connectors(tmp_path_factory):
    """The copied trellis file of
    `port_cons_vfi_trellis_file_without_connectors`, made once for the module,
    and its specified trellis."""
    file = port_cons_vfi_trellis_file_without_connectors(tmp_path_factory.mktemp("emptied"))
    return file, specify_trellis(load_trellis(file))


# The connector entry of a new pair


# each pair of fields of the registry's trellis, written `(period, stage key,
# field)`, and its connector entry: the file that holds the entry, its
# address, the periods it reaches, its text, and the reason where no text is
# written
CONNECTOR_ENTRIES = [
    pytest.param(
        (1, "s", "b"),
        (1, "u", "a"),
        "period.yml",
        "connectors[0]",
        (0, 1, 2),
        "{b: u.a}",
        None,
        id="the-arrival-after-its-stage-key",
    ),
    pytest.param(
        (1, "u", "a"),
        (1, "d", "a"),
        "period.yml",
        "connectors[0]",
        (0, 1, 2),
        "{u.a: d.a}",
        None,
        id="both-endpoints-after-their-stage-keys",
    ),
    pytest.param(
        (1, "d", "k_next"),
        (0, "u", "a"),
        "trellis.yml",
        "inter_connectors[0]",
        (0, 1, 2),
        "k_next: u.a",
        None,
        id="between-two-periods",
    ),
]


@pytest.mark.parametrize(
    "writing, reading, file, address, periods, text, reason", CONNECTOR_ENTRIES
)
def test_a_connector_entry_writes_the_shortest_spelling_of_its_pair(
    registry_folder, specified_registry, writing, reading, file, address, periods, text, reason
):
    """A connector entry writes, into the first empty connector of the
    period or into the inter-period connector, the shortest spelling that
    resolves to its pair at every period the entry reaches, a name bare
    where it is unique and after its stage key where it is not."""
    path = str(registry_folder / file) if file else None
    entry = connector_entry(specified_registry, writing, reading)
    assert entry[:5] == (path, address, periods, text, reason)


def test_the_registry_read_with_a_written_entry_selects_its_pair_at_its_address_in_each_period(
    registry_with_written_entry,
):
    """Read with the entry `{b: u.a}` written, the registry selects the pair
    from `s`'s `b` to `u`'s `a` in each of its three periods, at the address
    of the entry."""
    pairs = connection_report(registry_with_written_entry).pairs
    assert [(str(p.writing), str(p.reading), p.address) for p in pairs] == [
        (f"periods[{h}].s.b", f"periods[{h}].u.a", f"periods[{h}].connectors[0]")
        for h in (0, 1, 2)
    ]


def test_a_connector_entry_for_a_pair_that_a_join_already_reads_answers_port_joined(
    registry_with_written_entry, written_entry_texts
):
    """A connector entry asked again for the pair that the written entry
    joins answers `port-joined`."""
    reopened = registry_with_written_entry
    entry = connector_entry(reopened, (1, "s", "b"), (1, "u", "a"), written_entry_texts)
    assert entry.reason == "port-joined"


def test_a_connector_in_the_keyed_form_between_the_same_two_stages_takes_a_further_key_bare(
    registry_folder,
):
    """Where the period's connector is in the keyed form from `s` to `d`, the
    connector entry of `s`'s `b` and `d`'s `a` adds the bare key `{b: a}` to
    the connector's fields."""
    path = registry_folder / "period.yml"
    keyed = path.read_text(encoding="utf-8").replace("- {}", "- {from: s, to: d, fields: {a: a}}")
    texts = {str(path.resolve()): keyed}
    grouped = specify_trellis(load_recipe(registry_folder, "spec.yml", texts))
    entry = connector_entry(grouped, (1, "s", "b"), (1, "d", "a"), texts)
    assert entry[:5] == (str(path), "connectors[0].fields", (0, 1, 2), "{b: a}", None)


def test_an_inter_period_connector_that_cannot_reach_a_pair_at_every_period_answers_name_shared(
    tmp_path,
):
    """Where the earliest period lacks the stage `d`, so that the one
    inter-period connector, which stands for both pairs of adjacent periods,
    resolves a pair from `d` at no spelling at both pairs, the connector
    entry answers `name-shared` with the spelling that it does not write."""
    uneven = write_files(
        tmp_path / "uneven",
        {
            **THREE_PERIOD_REGISTRY,
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
        (0, 1, 2),
        "d.k_next: u.a",
        "name-shared",
    )


def test_a_connector_entry_may_replace_an_inferred_pair_and_no_authored_one(
    inferred_trellis, inferred_selection
):
    """The connector entry of `S`'s `a` and `U`'s `b` answers `port-joined`
    while the inferred pair from `S` to `T` reads `a`, writes `{S.a: b}`
    when told to replace that pair, and refuses to replace it as an
    authored pair."""
    (inferred,) = inferred_selection.pairs
    assert (inferred.writing.key, inferred.reading.key, inferred.origin) == ("S", "T", "inferred")
    assert connector_entry(inferred_trellis, (0, "S", "a"), (0, "U", "b")).reason == "port-joined"
    entry = connector_entry(
        inferred_trellis,
        (0, "S", "a"),
        (0, "U", "b"),
        selection=inferred_selection,
        replacing=(inferred,),
    )
    assert entry.reason is None and entry.text == "{S.a: b}"
    with pytest.raises(ValueError, match="inferred pair"):
        connector_entry(
            inferred_trellis,
            (0, "S", "a"),
            (0, "U", "b"),
            selection=inferred_selection,
            replacing=(inferred._replace(origin="authored"),),
        )


def test_a_connector_entry_given_a_selection_reuses_its_field_uses(
    inferred_trellis, inferred_selection, monkeypatch
):
    """A connector entry given the selection of the trellis neither finds the
    field uses nor types the fields again, the test failing where it does
    either."""

    def unexpected(*args, **kwargs):
        pytest.fail("the connector entry reads the field uses from the selection given")

    monkeypatch.setattr("bellman.factory.connections._uses", unexpected)
    monkeypatch.setattr("bellman.factory.connections._Types", unexpected)
    (inferred,) = inferred_selection.pairs
    connector_entry(
        inferred_trellis,
        (0, "S", "a"),
        (0, "U", "b"),
        selection=inferred_selection,
        replacing=(inferred,),
    )


def test_the_connector_that_replaces_an_inferred_pair_selects_the_pair_that_it_names(
    proposed_report,
):
    """With the replacing entry as the period's connector, the trellis
    selects the one pair from `S` to `U`'s field `b`."""
    (pair,) = proposed_report.pairs
    assert (pair.writing.key, pair.reading.key, pair.reading.field) == ("S", "U", "b")


def test_the_trellis_file_with_the_replacing_connector_appended_selects_the_same_pair(
    appended_file, proposed_report
):
    """The trellis file with the replacing entry appended, read again,
    selects the same pair as the trellis that holds the entry as its
    connector."""
    (pair,) = proposed_report.pairs
    (reread,) = connection_report(elaborate_trellis(load_trellis(appended_file))).pairs
    assert (reread.writing, reread.reading, reread.origin) == (
        pair.writing,
        pair.reading,
        pair.origin,
    )


def test_a_connector_appended_to_a_period_leaves_the_inter_period_connectors_last(
    inferred_folder, replacing_entry
):
    """The replacing entry, appended to the trellis file, stands within the
    period's connectors, so that the text still ends with its empty list of
    inter-period connectors."""
    text = (inferred_folder / "trellis.yml").read_text()
    appended = append_to_sequence(text, replacing_entry.address, replacing_entry.text)
    assert replacing_entry.text in appended
    assert appended.endswith("inter_connectors: []\n")


def test_a_second_coordinate_between_two_stages_is_written_into_their_existing_connector(
    extendable_trellis,
):
    """The connector entry of a second coordinate between `S` and `T` is a
    further key of the connector that already joins them, reaching both
    periods."""
    _, address, text, _ = extendable_trellis["row"]
    entry = connector_entry(extendable_trellis["trellis"], (0, "S", "b"), (0, "T", "a"))
    assert (entry.address, entry.periods, entry.text, entry.reason) == (
        address,
        (0, 1),
        text,
        None,
    )


def test_a_connector_extended_by_a_second_coordinate_remains_one_connector_in_each_period(
    extendable_trellis, extended_trellis
):
    """Once the entry is appended, each period still holds one connector,
    which holds the appended key."""
    extended = extendable_trellis["row"][3]
    assert all(period["connectors"][0] == extended for period in extended_trellis["periods"])
    assert all(len(period["connectors"]) == 1 for period in extended_trellis["periods"])


def test_a_connector_extended_by_a_second_coordinate_certifies_the_route_of_each_period(
    extended_trellis,
):
    """Once the entry is appended, the route from `S` to `T` of each of the
    two periods is certified."""
    assert connection_report(extended_trellis).counts["certified"] == 2


def test_a_connector_entry_for_a_field_of_an_entry_whose_target_fails_answers_source_authored(
    failed_target_trellis,
):
    """The connector entry of a field that an entry with an unresolved target
    already maps answers `source-authored` at that entry's address, so that
    no new entry replaces the authored one."""
    row = failed_target_trellis["row"]
    rules = [item.rule for item in failed_target_trellis["before"].diagnostics]
    assert rules.count("endpoint-unresolved") == row["unresolved"]
    entry = connector_entry(failed_target_trellis["trellis"], row["writing"], (0, "T", "a"))
    assert (entry.address, entry.reason) == (row["address"], "source-authored")


def test_a_connector_whose_target_fails_stays_in_the_trellis_as_written(failed_target_trellis):
    """The trellis of two periods holds the entry whose target `q` names no
    field among the connectors where the file writes it."""
    row, trellis = failed_target_trellis["row"], failed_target_trellis["trellis"]
    rules = [item.rule for item in failed_target_trellis["before"].diagnostics]
    assert rules.count("endpoint-unresolved") == row["unresolved"]
    sides = {
        "periods": [period["connectors"] for period in trellis["periods"]],
        "inter_connectors": trellis["inter_connectors"],
    }
    assert (len(trellis["periods"]), sides[row["side"]]) == (2, row["held"])


def test_a_connector_entry_changes_neither_the_trellis_file_nor_the_diagnostics(
    failed_target_trellis,
):
    """Answering the connector entry leaves the trellis file and the
    diagnostics of the trellis as they were."""
    row, trellis = failed_target_trellis["row"], failed_target_trellis["trellis"]
    connector_entry(trellis, row["writing"], (0, "T", "a"))
    assert failed_target_trellis["trellis_file"].read_text() == failed_target_trellis["text"]
    after = connection_report(trellis).diagnostics
    assert after == failed_target_trellis["before"].diagnostics


def test_a_connector_entry_beside_an_ambiguous_key_writes_the_qualified_key(
    ambiguous_key_trellis,
):
    """Beside the ambiguous key `b`, the connector entry of `S`'s `b` and
    `T`'s `a` writes the key after its stage key, `{S.b: T.a}`, into the
    entry that holds the ambiguous key."""
    writing = (ambiguous_key_trellis["h"], "S", "b")
    entry = connector_entry(ambiguous_key_trellis["trellis"], writing, (0, "T", "a"))
    assert (entry.address, entry.reason, yaml.safe_load(entry.text)) == (
        ambiguous_key_trellis["address"],
        None,
        {"S.b": "T.a"},
    )


def test_a_qualified_key_is_appended_beside_the_ambiguous_key_of_the_entry(ambiguous_key_trellis):
    """Appended, the qualified key stands in the entry after the authored
    keys, the ambiguous key among them."""
    address = ambiguous_key_trellis["address"]
    after_text = append_to_mapping(ambiguous_key_trellis["text"], address, "S.b", "T.a")
    assert entry_value(after_text, address) == {"S.a": "T.b", "b": "q", "S.b": "T.a"}


def test_a_qualified_key_appended_beside_an_ambiguous_key_leaves_it_ambiguous(
    ambiguous_key_trellis, appended_beside_ambiguous_key
):
    """Once `S.b: T.a` is appended, the bare key `b` is still diagnosed as
    ambiguous, and the target `q` as unresolved, as before the append."""
    assert "S.b: T.a" in appended_beside_ambiguous_key["after_text"]
    before = ambiguous_key_trellis["before"]
    after = appended_beside_ambiguous_key["after"]
    assert [d for d in after.diagnostics if d.rule.startswith("endpoint-")] == [
        d for d in before.diagnostics if d.rule.startswith("endpoint-")
    ]


def test_a_qualified_key_appended_beside_an_ambiguous_key_is_selected(
    appended_beside_ambiguous_key,
):
    """Once the qualified key is appended, the trellis selects the pair from
    `S`'s `b` to `T`'s `a`."""
    assert any(
        (p.writing.key, p.writing.field, p.reading.key, p.reading.field) == ("S", "b", "T", "a")
        for p in appended_beside_ambiguous_key["after"].pairs
    )


def test_a_join_by_equal_names_bars_a_second_line_from_its_continuation_field_alone(
    port_cons_vfi_trellis_without_connectors,
):
    """Where a join by equal names reads `cons`'s `a` and reaches `disc`'s
    `a`, a drag from `cons`'s `a` is answered `port-joined` while a drag to
    `disc`'s `a` takes a new connector."""
    file, trellis = port_cons_vfi_trellis_without_connectors
    assert connector_entry(trellis, (2, "cons", "a"), (2, "port", "k")) == (
        None,
        None,
        (),
        None,
        "port-joined",
        None,
        None,
    )
    assert connector_entry(trellis, (2, "port", "w"), (2, "disc", "a")) == (
        str(file),
        "periods[0].connectors[0]",
        SIX_PERIODS,
        "{w: a}",
        None,
        None,
        None,
    )


# the period after periods[h] in time is periods[h - 1]
@pytest.mark.parametrize(
    ("writing", "reading", "reason"),
    [
        pytest.param(
            (2, "port", "z"), (2, "cons", "m"), "port-joined", id="a-field-that-no-stage-declares"
        ),
        pytest.param(
            (9, "disc", "a"),
            (8, "port", "k"),
            "port-joined",
            id="a-period-that-the-trellis-does-not-hold",
        ),
        pytest.param(
            (3, "disc", "a"), (1, "port", "k"), "not-adjacent", id="two-periods-later-in-time"
        ),
        pytest.param(
            (2, "disc", "a"), (3, "port", "k"), "not-adjacent", id="one-period-earlier-in-time"
        ),
        pytest.param(
            (2, "port", "w"), (2, "port", "k"), "not-adjacent", id="the-writing-ports-own-stage"
        ),
    ],
)
def test_connector_entry_answers_the_reason_that_no_connector_may_join_two_ports(
    port_cons_vfi_trellis_without_connectors, writing, reading, reason
):
    """`connector_entry` answers the reason that no connector may join two
    ports, raising nothing and naming no file, address, period or line."""
    _, trellis = port_cons_vfi_trellis_without_connectors
    assert connector_entry(trellis, writing, reading) == (None, None, (), None, reason, None, None)


@pytest.mark.parametrize(
    ("join", "taken_out", "writing", "reading", "address", "periods", "line"),
    [
        pytest.param(
            # the joins that leave the last period of the durables model
            "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, "
            "a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}",
            " a_nxt_adj: a_bq,",
            (0, "adjuster_cons", "a_nxt_adj"),
            (0, "bequest", "a_bq"),
            "periods[0].connectors[0]",
            (0,),
            "{a_nxt_adj: a_bq}",
            id="the-connector-of-the-last-period",
        ),
        pytest.param(
            # the one inter-period mapping of the durables model
            "{a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}",
            " a_nxt_adj: a,",
            (2, "adjuster_cons", "a_nxt_adj"),
            (1, "tenure", "a"),
            "inter_connectors[0]",
            (0, 1, 2),
            "a_nxt_adj: a",
            id="the-one-inter-period-mapping",
        ),
    ],
)
def test_an_arrival_field_that_a_join_reaches_takes_a_further_key_of_that_join(
    durables_text, join, taken_out, writing, reading, address, periods, line
):
    """In the durables model with one key taken out of a join, a drag to the
    arrival field that `keeper_cons` still reaches is a further key of that
    join, while a drag from `keeper_cons`'s field is answered `port-joined`."""
    assert durables_text.count(join) == 1
    file = DURABLES / "trellis.yml"
    texts = {str(file.resolve()): durables_text.replace(join, join.replace(taken_out, ""))}
    trellis = elaborate_trellis(load_recipe(DURABLES, "spec.yml", texts))
    assert connector_entry(trellis, writing, reading, texts) == (
        str(file),
        address,
        periods,
        line,
        None,
        None,
        None,
    )
    kept = (writing[0], "keeper_cons", "a_nxt_kp")
    assert connector_entry(trellis, kept, reading, texts) == (
        None,
        None,
        (),
        None,
        "port-joined",
        None,
        None,
    )


# The entry that writes an authored pair


def test_an_authored_pair_records_its_address_and_its_entry_as_written(spelled_pair):
    """The pair of the source's `a` in the earliest period records the
    address of its connector and the address, the key and the value of its
    entry in the expanded trellis."""
    pair = spelled_pair["pair"]
    recorded = (pair.address, pair.source_address, pair.source_key, pair.source_value)
    assert recorded == spelled_pair["row"]["recorded"]


def test_the_expanded_entry_of_an_authored_pair_is_found_in_the_file_that_writes_it(
    spelled_pair,
):
    """The address of the pair's entry in the expanded trellis is written at
    an entry of the period file or of the trellis file."""
    name, address = spelled_pair["row"]["written"]
    found = written_at(spelled_pair["trellis_file"], spelled_pair["pair"].source_address)
    assert found == (str(spelled_pair["folder"] / name), address)


def test_the_entry_that_writes_an_authored_pair_maps_its_key_to_its_value(spelled_pair):
    """The entry of the file's text that writes the pair, as `written_at`
    finds it, maps the pair's key to its value."""
    pair = spelled_pair["pair"]
    # the address of the entry that writes the pair, as `written_at` finds it
    _, address = written_at(spelled_pair["trellis_file"], pair.source_address)
    assert entry_value(spelled_pair["source_text"], address)[pair.source_key] == (
        pair.source_value
    )


def test_removing_the_key_of_an_authored_pair_takes_it_out_of_its_entry(spelled_pair):
    """The entry with the pair's key removed no longer holds that key."""
    pair = spelled_pair["pair"]
    # the address of the entry that writes the pair, as `written_at` finds it
    _, address = written_at(spelled_pair["trellis_file"], pair.source_address)
    removed = remove_from_mapping(spelled_pair["source_text"], address, pair.source_key)
    assert pair.source_key not in entry_value(removed, address)


def test_a_pair_removed_from_its_entry_and_appended_again_leaves_the_same_pairs_selected(
    spelled_pair,
):
    """Read from the text in which the pair's key was removed from its entry
    and appended again, the trellis selects the same pairs as before the
    removal."""
    pair = spelled_pair["pair"]
    # the address of the entry that writes the pair, as `written_at` finds it
    _, address = written_at(spelled_pair["trellis_file"], pair.source_address)
    removed = remove_from_mapping(spelled_pair["source_text"], address, pair.source_key)
    assert pair.source_key not in entry_value(removed, address)
    restored = append_to_mapping(removed, address, pair.source_key, pair.source_value)
    texts = {str(spelled_pair["source_file"].resolve()): restored}
    reopened = connection_report(
        elaborate_trellis(load_trellis(spelled_pair["trellis_file"], texts))
    )
    assert sorted((p.writing, p.reading) for p in reopened.selection.pairs) == sorted(
        (p.writing, p.reading) for p in spelled_pair["selected"].pairs
    )


def test_a_trellis_read_from_a_text_in_place_of_its_file_leaves_the_file_unchanged(
    spelled_pair,
):
    """Reading the trellis from the restored text in place of the file that
    holds the connector leaves that file with the text it was written
    with."""
    pair = spelled_pair["pair"]
    # the address of the entry that writes the pair, as `written_at` finds it
    _, address = written_at(spelled_pair["trellis_file"], pair.source_address)
    removed = remove_from_mapping(spelled_pair["source_text"], address, pair.source_key)
    restored = append_to_mapping(removed, address, pair.source_key, pair.source_value)
    source_file = spelled_pair["source_file"]
    load_trellis(spelled_pair["trellis_file"], {str(source_file.resolve()): restored})
    assert source_file.read_text(encoding="utf-8") == spelled_pair["source_text"]


def test_an_unresolved_endpoint_of_a_repeated_period_names_its_entry_in_that_period(
    repeated_period_report,
):
    """The endpoint `q` of the connector in the keyed form is diagnosed in
    `periods[1]` with that period's entry, its key and its value as
    written."""
    unresolved = next(
        d for d in repeated_period_report.diagnostics if d.rule == "endpoint-unresolved"
    )
    assert unresolved.source_entries == (("periods[1].connectors[0].fields", "b", "q"),)


def test_the_entry_of_a_repeated_period_is_written_at_the_entry_of_its_period_file(
    repeated_period_folder, repeated_period_report
):
    """The entry of the unresolved endpoint, `periods[1].connectors[0].fields`
    of the trellis, is written at `connectors[0].fields` of the period
    file."""
    unresolved = next(
        d for d in repeated_period_report.diagnostics if d.rule == "endpoint-unresolved"
    )
    assert written_at(repeated_period_report.file, unresolved.source_entries[0][0]) == (
        str(repeated_period_folder / "period.yml"),
        "connectors[0].fields",
    )


def test_a_route_that_two_entries_write_keeps_both_source_entries(two_state_identity_stage):
    """The incompatible route from `S` into the fields in ℝ₊₊ of `T`, whose
    two pairs two connectors write, is diagnosed at the first connector with
    both entries as written."""
    positive = stage_from_text(TWO_FIELDS.replace("ℝ₊", "ℝ₊₊"), "positive.bl")
    period = period_record(
        {"S": two_state_identity_stage, "T": positive}, [{"S.a": "T.a"}, {"S.b": "T.b"}]
    )
    report = connection_report(elaborate_trellis({"periods": [period], "inter_connectors": []}))
    route_diagnostic = next(d for d in report.diagnostics if d.rule == "route-incompatible")
    assert route_diagnostic.source_entries == (
        ("periods[0].connectors[0]", "S.a", "T.a"),
        ("periods[0].connectors[1]", "S.b", "T.b"),
    )
    assert route_diagnostic.address == "periods[0].connectors[0]"


# The selections and constructions of one reading


@pytest.mark.parametrize(
    "read, selections",
    [
        pytest.param(elaborate_trellis, 1, id="elaborated"),
        pytest.param(specify_trellis, 2, id="specified"),
    ],
)
def test_elaborating_the_registry_selects_its_connections_once_and_specifying_it_twice(
    registry_folder, readings, read, selections
):
    """Elaborating the registry selects its connections once, on the
    symbolic occurrences, and specifying it selects them twice, again under
    the bound values."""
    read(load_recipe(registry_folder, "spec.yml"))
    assert len(readings[0]) == selections


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(elaborate_trellis, id="elaborated"),
        pytest.param(specify_trellis, id="specified"),
    ],
)
def test_a_reading_of_the_registry_constructs_each_distinct_stage_text_once(
    registry_folder, readings, read
):
    """A reading of the registry constructs each of its three stage texts
    once, though each of its three periods holds all three."""
    trellis = read(load_recipe(registry_folder, "spec.yml"))
    assert len(trellis["periods"]) == 3
    assert sorted(Path(origin).name for origin in readings[1]) == ["d.bl", "s.bl", "u.bl"]


# each query of a specified trellis that reads its connections: the view,
# whole and restricted, the report, the drawing, the unpaired joins, the
# unjoined fields, and a connector entry, each field written `(period, stage
# key, field)`, whose one selection supplies the field uses for every
# spelling that it tries
QUERIES = [
    pytest.param(to_model_explorer, id="view"),
    pytest.param(
        lambda trellis: to_model_explorer(trellis, periods=[0], unjoined=True),
        id="restricted-view-with-unjoined-fields",
    ),
    pytest.param(connection_report, id="report"),
    pytest.param(diagram_trellis, id="drawing"),
    pytest.param(unpaired_joins, id="unpaired-joins"),
    pytest.param(unjoined_fields, id="unjoined-fields"),
    pytest.param(
        lambda trellis: connector_entry(trellis, (1, "u", "a"), (1, "d", "a")),
        id="connector-entry",
    ),
]


@needs_viewer
@pytest.mark.parametrize("query", QUERIES)
def test_each_query_of_a_specified_trellis_selects_its_connections_once(
    specified_registry, readings, query
):
    """Each query of the specified trellis of the registry selects its
    connections once."""
    query(specified_registry)
    assert len(readings[0]) == 1


@needs_viewer
@pytest.mark.parametrize("query", QUERIES)
def test_no_query_of_a_specified_trellis_constructs_a_stage_again(
    specified_registry, readings, query
):
    """No query of the specified trellis of the registry constructs a
    stage."""
    query(specified_registry)
    assert readings[1] == []


@needs_viewer
def test_a_query_given_the_selection_of_the_trellis_reuses_it_without_selecting_again(
    specified_registry, registry_report, readings
):
    """A restricted report, a restricted view and the unpaired joins, each
    given the selection of the whole trellis, select no connections, the
    report holding that very selection."""
    selection = registry_report.selection
    restricted = connection_report(specified_registry, periods=[0], selection=selection)
    assert restricted.selection is selection
    to_model_explorer(specified_registry, periods=[0], unjoined=True, selection=selection)
    unpaired_joins(specified_registry, periods=[0], selection=selection)
    assert readings[0] == []


def test_a_report_given_a_selection_takes_the_state_fields_from_it(
    specified_registry, registry_report, monkeypatch
):
    """A report restricted to the terminal period and given the selection of
    the whole trellis answers the exterior continuation fields that the
    whole report places in that period without reading the state fields of
    any stage, the test failing where it reads them."""
    monkeypatch.setattr(
        "bellman.factory.joins.fields",
        lambda stage: pytest.fail("a supplied selection already holds the state fields"),
    )
    restricted = connection_report(
        specified_registry, periods=[0], selection=registry_report.selection
    )
    assert restricted.unjoined["exterior"]["writing"] == tuple(
        field for field in registry_report.unjoined["exterior"]["writing"] if field[0] == 0
    )
