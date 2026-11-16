"""The file and the entry that write each period, each inter-period pair and
each connector line of a trellis, and where a connector entry writes its line
in the application models; the unsaved texts that the readers take in place
of their files; and the refusal of a key written twice. The spelling that a
connector entry writes, the reason that it answers and the pairs that it may
replace or extend are tested in test_connections_read_and_written.py, apart
from one test of the spelling of a shared name, which carries a strict mark
of expected failure and stays here."""

import functools
import hashlib
from pathlib import Path

import pytest
from application_files import CONS_PORT, PENSION
from trellises import (
    SIX_PERIODS,
    TWO_PERIOD_TRELLIS_TEXT,
    declarations_copy,
    port_cons_vfi_trellis_file_without_connectors,
    rewrite_once,
)

from bellman.factory import file_entries
from bellman.factory.loading import period_and_repeat
from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import write_registry
from bellman.refusals import FactoryError
from bellman.trellis import (
    connector_entry,
    entry_span,
    entry_value,
    load_recipe,
    load_trellis,
    period_entries,
    read_trellis_file,
    specify_trellis,
    written_at,
    written_spans,
)

# the pension model's trellis file
PENSION_TRELLIS_FILE = PENSION / "trellis.yml"

# the portfolio model's copied folder, and cons-port's copied trellis file of
# records, which writes each stage occurrence as a record of its stage file and
# its sources; each path is written from the folder into which
# `declarations_copy` copies
PORTFOLIO_COPY = "applications/portfolio-choice/declaration"
PORT_CONS_COPY = "applications/cons-port/declaration/trellis.port-cons-vfi.yml"


# a period file that writes `repeat: 3`, and the last period of a trellis
# file, written out after the entry that names the period file
PERIOD_FILE = "!period\nstages: [worker, retiree]\nconnectors:\n  - {}\nrepeat: 3\n"
TERMINAL_PERIOD = "  - stages: [worker, retiree, terminal]\n    connectors: []\n"

# a trellis file whose entry names the period file and writes no repeat of its
# own, followed by the terminal period
TEMPLATE_AND_TERMINAL = "!trellis\nperiods:\n  - {template: period.yml}\n" + TERMINAL_PERIOD

# texts that no reader takes from a mapping of texts, each with its path from
# the folder of `declarations_copy`: a file that no file names, a stage file
# and two calibration files
UNTAKEN = (
    (f"{PORTFOLIO_COPY}/notes.yml", "periods: []\n"),
    (f"{PORTFOLIO_COPY}/stages/cons/cons.bl", "@stage: cons\n"),
    (f"{PORTFOLIO_COPY}/calibration/portfolio.yml", "calibration: {}\n"),
    ("applications/cons-port/declaration/calibration/portfolio.yml", "{}\n"),
)

# the two mappings of texts of which no reader takes a text
MAPPINGS_THAT_NO_READER_TAKES = [
    pytest.param((), id="the-empty-mapping"),
    pytest.param(UNTAKEN, id="texts-that-no-reader-takes"),
]

# the addresses of the trellis file of `spans_trellis` that `written_spans` is
# asked for: at positions 0 to 39 the key `S.a` of the connector of each period
# that the period file writes; at 40 and 41 the keyed connector of the second
# entry and the last pair of the inter-period mapping, both written in the
# trellis file; at 42 a stage of the period file; and at 43 to 45 three
# addresses that no file writes: a period past the expansion, a key that the
# connector does not hold, and no address
ADDRESSES = tuple(f"periods[{h}].connectors[0]['S.a']" for h in range(40)) + (
    "periods[40].connectors[0].fields.a",
    "inter_connectors[39]['S.a']",
    "periods[39].stages[0]",
    "periods[99].stages",
    "periods[0].connectors[0].missing",
    None,
)


@pytest.fixture
def five_period_texts(tmp_path):
    """Copies of the portfolio model's folder and of cons-port's folder under
    `tmp_path`, and texts of their two trellis files that write `repeat: 5`
    where the files write `repeat: 6`, each at the file's resolved path."""
    registry, port_cons = declarations_copy(tmp_path)
    texts = {
        str(path.resolve()): path.read_text(encoding="utf-8").replace("repeat: 6", "repeat: 5")
        for path in (registry / "trellis.yml", port_cons)
    }
    return registry, port_cons, texts


@pytest.fixture
def period_and_recipe_texts(tmp_path):
    """A copy of the portfolio model's folder, that folder reached through
    `stages/..`, and texts of its period file, with a second connector, and of
    its recipe, with a `registry` block, each at the file's resolved path."""
    registry, _ = declarations_copy(tmp_path)
    period, recipe = registry / "period.yml", registry / "spec.yml"
    texts = {
        str(period.resolve()): period.read_text(encoding="utf-8") + "  - {}\n",
        str(recipe.resolve()): recipe.read_text(encoding="utf-8")
        + "registry:\n  calibration: [calibration/portfolio]\n",
    }
    return registry, registry / "stages" / "..", texts


@pytest.fixture
def spans_trellis(tmp_path):
    """A trellis file in `tmp_path` whose first entry repeats the period file
    beside it forty times, whose second names that file with a keyed
    connector of its own, and whose one inter-period mapping stands for every
    pair."""
    period = tmp_path / "period.yml"
    period.write_text("stages: [S, T]\nconnectors:\n  - {S.a: T.b, S.b: T.a}\n")
    file = tmp_path / "trellis.yml"
    file.write_text(
        "periods:\n  - {template: period.yml, repeat: 40}\n"
        "  - template: period.yml\n    connectors: [{from: S, to: T, fields: {a: b}}]\n"
        "inter_connectors: [{S.a: T.b}]\n"
    )
    return file


@pytest.fixture
def counted_reads(monkeypatch):
    """The lists of the trellis files that the module
    `bellman.factory.file_entries` reads and of the texts that it parses,
    each recorded from the moment the fixture is made."""
    reads, parsed = [], []
    original_read, original_parse = file_entries._trellis_read, file_entries._composed

    def counted_read(file, texts):
        reads.append(file)
        return original_read(file, texts)

    def counted_parse(text):
        parsed.append(text)
        return original_parse(text)

    monkeypatch.setattr(file_entries, "_trellis_read", counted_read)
    monkeypatch.setattr(file_entries, "_composed", counted_parse)
    return reads, parsed


@pytest.fixture
def twice_written_files(tmp_path, cons_sources, corpus_path):
    """`tmp_path` holding a calibration file that writes `ρ` twice, a copy of
    the settings file of `cons` that writes `n_m` twice, and a trellis file
    whose one period holds `cons` with that calibration file."""
    (tmp_path / "calibration.yml").write_text(
        "calibration:\n  ρ: 2.0\n  ρ: 3.0\n", encoding="utf-8"
    )
    settings = cons_sources["settings"].read_text(encoding="utf-8")
    (tmp_path / "settings.yml").write_text(
        settings.replace("  n_m: 8000", "  n_m: 8000\n  n_m: 10"), encoding="utf-8"
    )
    (tmp_path / "trellis.yml").write_text(
        f"periods:\n  - stages:\n      cons: {{stage: {corpus_path('cons')}, "
        "calibration: calibration.yml}\n    connectors: []\ninter_connectors: []\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def calibration_of_a_copy(cons, twice_written_files):
    """`calibrate` of a copy of `cons` with the calibration file of
    `twice_written_files`, as a call of no argument."""
    return functools.partial(copy_native(cons).calibrate, twice_written_files / "calibration.yml")


@pytest.fixture
def settings_of_a_methodized_copy(cons, cons_sources, twice_written_files):
    """`configure` of a copy of `cons` with its methods bound, with the
    settings file of `twice_written_files`, as a call of no argument."""
    methodized = copy_native(cons).methodize(cons_sources["methods"])
    return functools.partial(methodized.configure, twice_written_files / "settings.yml")


@pytest.fixture
def loading_of_the_trellis(twice_written_files):
    """`load_trellis` of the trellis file of `twice_written_files`, as a call
    of no argument."""
    return functools.partial(load_trellis, twice_written_files / "trellis.yml")


def emptied_portfolio(folder):
    """The copy of the portfolio model's folder under `folder` with the
    connector of `period.yml` and the inter-period mapping of `trellis.yml`
    each emptied to `{}`; answers the copied folder."""
    registry, _ = declarations_copy(folder)
    rewrite_once(registry / "period.yml", "- {m_next: m}", "- {}")
    rewrite_once(registry / "trellis.yml", "- {disc.a: k}", "- {}")
    return registry


def emptied_portfolio_entry(folder):
    """The copy `emptied_portfolio` whose entry of `trellis.yml` writes its
    own `connectors: [{}]`, which stands over the connectors of the period
    file that the entry names; answers the copied folder."""
    registry = emptied_portfolio(folder)
    rewrite_once(
        registry / "trellis.yml",
        "- {template: period.yml, repeat: 6}",
        "- {template: period.yml, repeat: 6, connectors: [{}]}",
    )
    return registry


def five_mappings_port_cons(folder):
    """The copy of cons-port's trellis file of records under `folder` whose
    `inter_connectors` writes one empty mapping for each of its five adjacent
    pairs, its connector `{w: m}` kept; answers the copied trellis file."""
    _, trellis = declarations_copy(folder)
    rewrite_once(trellis, "  - {disc.a: k}\n", "  - {}\n" * 5)
    return trellis


def two_cons_period(folder):
    """The copy `port_cons_vfi_trellis_file_without_connectors` whose period
    holds `cons_one` and `cons_two` in place of `cons`, two occurrences of
    `cons.bl`, each with the record of `cons`, so that both arrive at `m` and
    both continue to `a`; answers the copied trellis file."""
    trellis = port_cons_vfi_trellis_file_without_connectors(folder)
    lines = trellis.read_text(encoding="utf-8").splitlines(keepends=True)
    (first,) = [n for n, line in enumerate(lines) if line.startswith("      cons: {")]
    # the record of `cons` is written on two lines
    record = lines[first] + lines[first + 1]
    rewrite_once(
        trellis,
        record,
        record.replace("cons: {", "cons_one: {", 1) + record.replace("cons: {", "cons_two: {", 1),
    )
    return trellis


def specified_from_file(file, texts=None):
    """The specified trellis of the trellis file `file`, each text of `texts`
    read in place of the file at its resolved path."""
    return specify_trellis(load_trellis(file, texts))


def specified_from_recipe(registry, texts=None):
    """The specified trellis of the recipe `spec.yml` of the folder
    `registry`, each text of `texts` read in place of the file at its
    resolved path."""
    return specify_trellis(load_recipe(registry, "spec.yml", texts))


def written_file(folder, name, text):
    """The path of the file `name` in `folder`, written with `text`."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def value_written_at(trellis, address):
    """The value at the file and the address that `written_at` answers for
    the address `address` of the trellis file `trellis`."""
    file, place = written_at(trellis, address)
    return entry_value(Path(file).read_text(encoding="utf-8"), place)


def sha256_of(text):
    """The SHA-256 of the UTF-8 bytes of `text`."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def texts_under(folder, written):
    """The mapping of texts of `written`, pairs of a path from `folder` and a
    text, each text at its file's resolved path."""
    return {str((folder / name).resolve()): text for name, text in written}


def spans_on_disk(file):
    """For each of `ADDRESSES`, the file and the span that `written_at` and
    `entry_span` give for the files on disk, and None for the three addresses
    that no file writes."""
    spans = []
    for address in ADDRESSES[:43]:
        path, place = written_at(file, address)
        spans.append((path, entry_span(Path(path).read_text(), place)))
    return (*spans, None, None, None)


def unsaved_period_text(file):
    """A mapping of texts that holds the text of the period file beside the
    trellis file `file` with a comment line added above it."""
    period = file.parent / "period.yml"
    return {str(period.resolve()): "# unsaved source\n" + period.read_text()}


@pytest.mark.parametrize(
    ("trellis", "address", "file", "place"),
    [
        pytest.param(
            PENSION_TRELLIS_FILE,
            "periods[0].connectors[0]",
            PENSION_TRELLIS_FILE,
            "periods[0].connectors[0]",
            id="a-period-written-out",
        ),
        pytest.param(
            PENSION_TRELLIS_FILE,
            "periods[5].connectors[0]",
            PENSION / "period.yml",
            "connectors[0]",
            id="a-period-of-the-period-file",
        ),
        pytest.param(
            PENSION_TRELLIS_FILE,
            "inter_connectors[7]",
            PENSION_TRELLIS_FILE,
            "inter_connectors[0]",
            id="a-pair-of-the-one-mapping",
        ),
        pytest.param(
            PENSION_TRELLIS_FILE,
            "stages.worker_saving",
            PENSION_TRELLIS_FILE,
            "stages.worker_saving",
            id="an-address-outside-the-periods",
        ),
        pytest.param(
            CONS_PORT / "trellis.port-cons.yml",
            "periods[4].stages.cons.methods",
            CONS_PORT / "trellis.port-cons.yml",
            "periods[0].stages.cons.methods",
            id="a-period-of-an-entry-repeated-six-times",
        ),
    ],
)
def test_written_at_answers_the_file_and_the_address_that_write_a_part_of_the_trellis(
    trellis, address, file, place
):
    """`written_at` answers for an address of the expanded trellis the file
    and the address that write it, the trellis file's entry or the period file
    that the entry names, and an address outside the periods as given."""
    assert written_at(trellis, address) == (str(file), place)


def test_written_at_refuses_a_period_that_the_trellis_does_not_hold():
    """`written_at` refuses with a KeyError a period past the fifteen periods
    of the pension model's trellis."""
    with pytest.raises(KeyError):
        written_at(PENSION_TRELLIS_FILE, "periods[15].connectors[0]")


@pytest.mark.parametrize(
    ("entry", "repeated"),
    [
        pytest.param("  - {template: period.yml}\n", 3, id="the-period-file-writes-the-repeat"),
        pytest.param(
            "  - {template: period.yml, repeat: 2}\n",
            2,
            id="the-entry-repeat-stands-over-the-period-file",
        ),
    ],
)
def test_written_at_counts_the_periods_of_a_repeat_as_the_loader_does(tmp_path, entry, repeated):
    """`written_at` answers for each period that `read_trellis_file` expands
    the place that holds the stages the loader reads there, and refuses the
    period past the expansion."""
    period = written_file(tmp_path, "period.yml", PERIOD_FILE)
    trellis = written_file(
        tmp_path, "trellis.yml", "!trellis\nperiods:\n" + entry + TERMINAL_PERIOD
    )
    expanded = read_trellis_file(trellis)["periods"]
    period_stages = [f"periods[{h}].stages" for h in range(len(expanded))]
    assert [value_written_at(trellis, address) for address in period_stages] == [
        each["stages"] for each in expanded
    ]
    assert [written_at(trellis, address) for address in period_stages] == [
        (str(period), "stages")
    ] * repeated + [(str(trellis), "periods[1].stages")]
    with pytest.raises(KeyError):
        written_at(trellis, f"periods[{repeated + 1}].stages")


@pytest.mark.parametrize(
    ("text", "places"),
    [
        pytest.param(
            "!trellis\nperiods:\n  - {template: period.yml}\ninter_connectors:\n  - {a: k}\n",
            ["inter_connectors[0]"] * 2,
            id="one-mapping-for-every-pair",
        ),
        pytest.param(
            TEMPLATE_AND_TERMINAL + "inter_connectors:\n  - {a: k}\n  - {b: k}\n  - {c: k}\n",
            ["inter_connectors[0]", "inter_connectors[1]", "inter_connectors[2]"],
            id="one-mapping-for-each-pair",
        ),
    ],
)
def test_written_at_answers_each_inter_period_pair_at_the_mapping_that_writes_it(
    tmp_path, text, places
):
    """`written_at` answers for each adjacent pair that `read_trellis_file`
    expands the mapping that the file writes for it, and refuses the pair past
    the expansion."""
    written_file(tmp_path, "period.yml", PERIOD_FILE)
    trellis = written_file(tmp_path, "trellis.yml", text)
    mappings = read_trellis_file(trellis)["inter_connectors"]
    assert len(mappings) == len(places)
    pair_addresses = [f"inter_connectors[{h}]" for h in range(len(mappings))]
    assert [written_at(trellis, pair) for pair in pair_addresses] == [
        (str(trellis), place) for place in places
    ]
    assert [value_written_at(trellis, pair) for pair in pair_addresses] == mappings
    with pytest.raises(KeyError):
        written_at(trellis, f"inter_connectors[{len(places)}]")


@pytest.mark.parametrize(
    ("text", "mappings"),
    [
        pytest.param(TWO_PERIOD_TRELLIS_TEXT, [{}], id="no-key-inter-connectors"),
        pytest.param(
            TWO_PERIOD_TRELLIS_TEXT + "inter_connectors: []\n",
            [{}],
            id="an-empty-list-of-mappings",
        ),
        pytest.param(
            "!trellis\nperiods:\n  - stages: [worker]\ninter_connectors:\n  - {a: k}\n",
            [],
            id="one-period-and-one-mapping",
        ),
    ],
)
def test_written_at_refuses_an_inter_period_pair_that_the_file_does_not_write(
    tmp_path, text, mappings
):
    """`written_at` refuses the first inter-period pair where the loader reads
    an empty mapping that no file writes, or no pair at all."""
    trellis = written_file(tmp_path, "trellis.yml", text)
    assert read_trellis_file(trellis)["inter_connectors"] == mappings
    with pytest.raises(KeyError):
        written_at(trellis, "inter_connectors[0]")


def test_read_trellis_file_reads_an_unsaved_text_in_place_of_its_file(five_period_texts):
    """`read_trellis_file` reads five periods from an unsaved text of the
    portfolio model's trellis file and records the text's digest and its one
    path."""
    registry, _, texts = five_period_texts
    trellis = registry / "trellis.yml"
    assert trellis.read_text(encoding="utf-8").count("repeat: 6") == 1
    key = str(trellis.resolve())
    read = read_trellis_file(trellis, texts=texts)
    assert (len(read["periods"]), read["sha256"], read["texts"]) == (
        5,
        sha256_of(texts[key]),
        [key],
    )


def test_load_recipe_reads_an_unsaved_text_of_its_trellis_file_in_place_of_the_file(
    five_period_texts,
):
    """`load_recipe` reads five periods from an unsaved text of the portfolio
    model's trellis file and records the text's digest and its one path."""
    registry, _, texts = five_period_texts
    trellis = registry / "trellis.yml"
    assert trellis.read_text(encoding="utf-8").count("repeat: 6") == 1
    key = str(trellis.resolve())
    syntactic = load_recipe(registry, "spec.yml", texts)
    assert len(syntactic["periods"]) == 5
    assert syntactic["provenance"]["trellis"]["sha256"] == sha256_of(texts[key])
    assert syntactic["provenance"]["texts"] == [key]


def test_load_trellis_reads_an_unsaved_text_in_place_of_its_file(five_period_texts):
    """`load_trellis` reads five periods from an unsaved text of cons-port's
    trellis file of records and records the text's digest and its one path."""
    _, port_cons, texts = five_period_texts
    assert port_cons.read_text(encoding="utf-8").count("repeat: 6") == 1
    key = str(port_cons.resolve())
    loaded = load_trellis(port_cons, texts=texts)
    assert len(loaded["periods"]) == 5
    assert loaded["provenance"]["trellis"]["sha256"] == sha256_of(texts[key])
    assert loaded["provenance"]["texts"] == [key]


def test_written_at_counts_the_periods_of_an_unsaved_text_of_the_trellis_file(five_period_texts):
    """`written_at` answers the sixth period of the portfolio model at its
    period file on disk and refuses it where an unsaved text writes five."""
    registry, _, texts = five_period_texts
    trellis = registry / "trellis.yml"
    assert trellis.read_text(encoding="utf-8").count("repeat: 6") == 1
    assert written_at(trellis, "periods[5].connectors[0]") == (
        str(registry / "period.yml"),
        "connectors[0]",
    )
    with pytest.raises(KeyError):
        written_at(trellis, "periods[5].connectors[0]", texts)


def test_reading_unsaved_texts_leaves_the_files_on_disk_unchanged(five_period_texts):
    """The readers of a trellis and `written_at`, given unsaved texts of two
    trellis files, leave both files on disk as they were."""
    registry, port_cons, texts = five_period_texts
    trellis = registry / "trellis.yml"
    on_disk = {path: path.read_text(encoding="utf-8") for path in (trellis, port_cons)}
    assert [written.count("repeat: 6") for written in on_disk.values()] == [1, 1]
    read_trellis_file(trellis, texts=texts)
    load_recipe(registry, "spec.yml", texts)
    load_trellis(port_cons, texts=texts)
    # the fifth period, the last that the unsaved text of the trellis file
    # writes
    written_at(trellis, "periods[4].connectors[0]", texts)
    assert {path: path.read_text(encoding="utf-8") for path in on_disk} == on_disk


def test_period_and_repeat_reads_an_unsaved_text_of_a_period_file(period_and_recipe_texts):
    """`period_and_repeat`, given the folder through `stages/..`, reads the
    connectors of an unsaved text of the period file that an entry names at
    the path that it resolves."""
    _, directory, texts = period_and_recipe_texts
    # the entry, the folder of the files it names, and the trellis file and
    # the address of the entry, which a refusal would name
    expanded, repeat = period_and_repeat(
        {"template": "period.yml", "repeat": 6},
        directory,
        directory / "trellis.yml",
        "periods[0]",
        texts,
    )
    assert (expanded["connectors"], repeat) == ([{"m_next": "m"}, {}], 6)


def test_load_recipe_reads_unsaved_texts_of_the_period_file_and_the_recipe(
    period_and_recipe_texts,
):
    """`load_recipe`, given the folder through `stages/..`, reads unsaved texts
    of the period file and of the recipe at the paths that it resolves,
    recording the digest of the recipe's text and both paths."""
    registry, directory, texts = period_and_recipe_texts
    assert load_recipe(directory, "spec.yml")["registry"] == {}
    syntactic = load_recipe(directory, "spec.yml", texts)
    assert [each["connectors"] for each in syntactic["periods"]] == [[{"m_next": "m"}, {}]] * 6
    assert list(syntactic["registry"]) == ["calibration"] and syntactic["registry"]["calibration"]
    recipe = texts[str((registry / "spec.yml").resolve())]
    assert syntactic["provenance"]["recipe"]["sha256"] == sha256_of(recipe)
    assert syntactic["provenance"]["texts"] == sorted(texts)


def test_written_at_counts_the_periods_that_an_unsaved_text_of_a_period_file_repeats(tmp_path):
    """`written_at` answers the fourth period at the terminal entry of the
    trellis file where the period file on disk writes `repeat: 3`, and at the
    period file where an unsaved text of it writes `repeat: 4`."""
    period = written_file(tmp_path, "period.yml", PERIOD_FILE)
    trellis = written_file(tmp_path, "trellis.yml", TEMPLATE_AND_TERMINAL)
    assert PERIOD_FILE.count("repeat: 3") == 1
    texts = {str(period.resolve()): PERIOD_FILE.replace("repeat: 3", "repeat: 4")}
    assert written_at(trellis, "periods[3].stages") == (str(trellis), "periods[1].stages")
    assert written_at(trellis, "periods[3].stages", texts) == (str(period), "stages")


@pytest.mark.parametrize("untaken_texts", MAPPINGS_THAT_NO_READER_TAKES)
def test_load_recipe_answers_as_without_texts_where_it_takes_none_of_them(tmp_path, untaken_texts):
    """`load_recipe`, given a mapping of texts that it does not take, records
    no texts and answers what it answers with no mapping."""
    registry, _ = declarations_copy(tmp_path)
    answer = load_recipe(registry, "spec.yml", texts_under(tmp_path, untaken_texts))
    assert "texts" not in answer["provenance"]
    assert answer == load_recipe(registry, "spec.yml")


@pytest.mark.parametrize("untaken_texts", MAPPINGS_THAT_NO_READER_TAKES)
def test_load_trellis_answers_as_without_texts_where_it_takes_none_of_them(
    tmp_path, untaken_texts
):
    """`load_trellis`, given a mapping of texts that it does not take, records
    no texts and answers what it answers with no mapping."""
    _, port_cons = declarations_copy(tmp_path)
    answer = load_trellis(port_cons, texts=texts_under(tmp_path, untaken_texts))
    assert "texts" not in answer["provenance"]
    assert answer == load_trellis(port_cons)


@pytest.mark.parametrize("untaken_texts", MAPPINGS_THAT_NO_READER_TAKES)
def test_read_trellis_file_answers_as_without_texts_where_it_takes_none_of_them(
    tmp_path, untaken_texts
):
    """`read_trellis_file`, given a mapping of texts that it does not take,
    records no texts and answers what it answers with no mapping."""
    registry, _ = declarations_copy(tmp_path)
    answer = read_trellis_file(
        registry / "trellis.yml", texts=texts_under(tmp_path, untaken_texts)
    )
    assert "texts" not in answer
    assert answer == read_trellis_file(registry / "trellis.yml")


def test_load_recipe_refuses_a_mapping_of_texts_given_as_the_keyword_texts(tmp_path):
    """`load_recipe` reads the keyword `texts` as a slot that the recipe does
    not write and refuses it under `recipe-slot-unknown`, since the mapping of
    texts is its third positional argument, which no slot can name."""
    registry, _ = declarations_copy(tmp_path)
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml", texts={})
    assert refused.value.rule == "recipe-slot-unknown"


@pytest.mark.parametrize(
    ("copy", "trellis", "written", "address"),
    [
        pytest.param(
            port_cons_vfi_trellis_file_without_connectors,
            PORT_CONS_COPY,
            PORT_CONS_COPY,
            "periods[0]",
            id="an-entry-that-writes-its-periods-out",
        ),
        pytest.param(
            emptied_portfolio,
            f"{PORTFOLIO_COPY}/trellis.yml",
            f"{PORTFOLIO_COPY}/period.yml",
            "",
            id="an-entry-that-names-a-period-file",
        ),
        pytest.param(
            emptied_portfolio_entry,
            f"{PORTFOLIO_COPY}/trellis.yml",
            f"{PORTFOLIO_COPY}/period.yml",
            "",
            id="an-entry-that-writes-connectors-of-its-own",
        ),
    ],
)
def test_period_entries_answers_the_file_and_the_entry_that_write_each_period(
    tmp_path, copy, trellis, written, address
):
    """`period_entries` answers for each of the six periods of a copied
    trellis the file and the address of the entry that writes it and the six
    periods of that entry."""
    copy(tmp_path)
    assert (
        period_entries(tmp_path / trellis) == [(str(tmp_path / written), address, SIX_PERIODS)] * 6
    )


def test_period_entries_answers_the_terminal_period_and_the_period_file_of_the_pension_model():
    """`period_entries` answers the pension model's terminal period at its
    entry of the trellis file and the fourteen earlier periods at the period
    file."""
    assert (
        period_entries(PENSION_TRELLIS_FILE)
        == [(str(PENSION_TRELLIS_FILE), "periods[0]", (0,))]
        + [(str(PENSION / "period.yml"), "", tuple(range(1, 15)))] * 14
    )


def test_period_entries_reads_an_unsaved_text_of_the_trellis_file(tmp_path):
    """`period_entries` reads four periods from an unsaved text of a trellis
    file that writes `repeat: 4` where the file writes `repeat: 6`."""
    port_cons = port_cons_vfi_trellis_file_without_connectors(tmp_path)
    on_disk = port_cons.read_text(encoding="utf-8")
    assert on_disk.count("repeat: 6") == 1
    texts = {str(port_cons.resolve()): on_disk.replace("repeat: 6", "repeat: 4")}
    assert period_entries(port_cons, texts) == [(str(port_cons), "periods[0]", (0, 1, 2, 3))] * 4


# a port is written (period index, stage occurrence, field), periods[0] being
# the last period in time; an answer of `connector_entry` is the record (file,
# address, periods, line, reason, shared, held): the file and the address at
# which the line is written, the periods that it reaches, the line, the reason
# that no line may be written or None, the stage occurrence of the period that
# shares a dragged name, and the perch, the name and the occurrences that hold
# it
@pytest.mark.parametrize(
    ("copy", "read", "written", "address", "field"),
    [
        pytest.param(
            port_cons_vfi_trellis_file_without_connectors,
            specified_from_file,
            PORT_CONS_COPY,
            "periods[0].connectors[0]",
            "w",
            id="the-trellis-file-writes-the-period-out",
        ),
        pytest.param(
            emptied_portfolio,
            specified_from_recipe,
            f"{PORTFOLIO_COPY}/period.yml",
            "connectors[0]",
            "m_next",
            id="the-entry-names-a-period-file",
        ),
        pytest.param(
            emptied_portfolio_entry,
            specified_from_recipe,
            f"{PORTFOLIO_COPY}/trellis.yml",
            "periods[0].connectors[0]",
            "m_next",
            id="the-entry-writes-connectors-over-its-period-file",
        ),
    ],
)
def test_connector_entry_answers_a_flat_connector_in_the_list_that_writes_the_period(
    tmp_path, copy, read, written, address, field
):
    """A drag within a period from `port`'s continuation field to `cons`'s
    `m` is answered as a flat connector in the first empty mapping of the list
    that writes the period, reaching the six periods of that list."""
    trellis = read(copy(tmp_path))
    assert connector_entry(trellis, (2, "port", field), (2, "cons", "m")) == (
        str(tmp_path / written),
        address,
        SIX_PERIODS,
        f"{{{field}: m}}",
        None,
        None,
        None,
    )


def test_connector_entry_appends_to_a_connectors_list_that_holds_no_empty_mapping(tmp_path):
    """A drag within a period from `disc`'s `a` to `port`'s `k`, where the
    list holds only the filled connector `{w: m}`, is appended to the list as
    `{disc.a: k}`, the stage key written since `cons` continues to `a`."""
    five = five_mappings_port_cons(tmp_path)
    # the line closes a cycle of the period's pairs through the inferred pair
    # of `cons`'s `a` and `disc`'s `a`, joined by their equal name; the answer
    # admits the line, its `reason` being None, and names where the line is
    # written
    assert connector_entry(specified_from_file(five), (2, "disc", "a"), (2, "port", "k")) == (
        str(five),
        "periods[0].connectors",
        SIX_PERIODS,
        "{disc.a: k}",
        None,
        (2, "cons"),
        ("cntn", "a", ("cons", "disc")),
    )


def test_connector_entry_appends_to_a_connectors_list_written_empty(tmp_path):
    """A drag within a period from `port`'s `w` to `cons`'s `m` is appended as
    `{w: m}` to a `connectors` list that an unsaved text writes `[]`."""
    port_cons = port_cons_vfi_trellis_file_without_connectors(tmp_path)
    on_disk = port_cons.read_text(encoding="utf-8")
    assert on_disk.count("connectors:\n      - {}\n") == 1
    texts = {
        str(port_cons.resolve()): on_disk.replace("connectors:\n      - {}\n", "connectors: []\n")
    }
    trellis = specified_from_file(port_cons, texts)
    assert connector_entry(trellis, (2, "port", "w"), (2, "cons", "m"), texts) == (
        str(port_cons),
        "periods[0].connectors",
        SIX_PERIODS,
        "{w: m}",
        None,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("copy", "read", "written", "removed", "writing", "reading", "address", "periods", "line"),
    [
        pytest.param(
            port_cons_vfi_trellis_file_without_connectors,
            specified_from_file,
            PORT_CONS_COPY,
            "    connectors:\n      - {}\n",
            (2, "port", "w"),
            (2, "cons", "m"),
            "periods[0]",
            SIX_PERIODS,
            "{w: m}",
            id="an-entry-of-the-trellis-file-with-no-connectors",
        ),
        pytest.param(
            emptied_portfolio,
            specified_from_recipe,
            f"{PORTFOLIO_COPY}/period.yml",
            "connectors:\n  - {}\n",
            (2, "port", "m_next"),
            (2, "cons", "m"),
            "",
            SIX_PERIODS,
            "{m_next: m}",
            id="a-period-file-with-no-connectors",
        ),
        pytest.param(
            port_cons_vfi_trellis_file_without_connectors,
            specified_from_file,
            PORT_CONS_COPY,
            "inter_connectors:\n  - {}\n",
            (3, "disc", "a"),
            (2, "port", "k"),
            "inter_connectors",
            (),
            "a: k",
            id="a-trellis-file-with-no-inter-period-mapping",
        ),
    ],
)
def test_connector_entry_answers_no_mapping_where_no_list_can_hold_the_line(
    tmp_path, copy, read, written, removed, writing, reading, address, periods, line
):
    """Where an unsaved text writes no `connectors` list for a period, or no
    inter-period mapping, a drag is answered as `no-mapping` at the address of
    the entry or of the key that would hold it, with the line that was not
    written."""
    copied = copy(tmp_path)
    file = tmp_path / written
    on_disk = file.read_text(encoding="utf-8")
    assert on_disk.count(removed) == 1
    texts = {str(file.resolve()): on_disk.replace(removed, "")}
    answer = connector_entry(read(copied, texts), writing, reading, texts)
    assert answer == (str(file), address, periods, line, "no-mapping", None, None)


@pytest.mark.parametrize(
    ("copy", "address", "periods"),
    [
        pytest.param(
            port_cons_vfi_trellis_file_without_connectors,
            "inter_connectors[0]",
            SIX_PERIODS,
            id="one-mapping-for-every-pair",
        ),
        pytest.param(
            five_mappings_port_cons, "inter_connectors[2]", (2, 3), id="one-mapping-for-each-pair"
        ),
    ],
)
def test_connector_entry_answers_the_inter_period_mapping_that_joins_two_periods(
    tmp_path, copy, address, periods
):
    """A drag from `disc`'s `a` in `periods[3]` to `port`'s `k` in the period
    after it in time is the entry `disc.a: k` of the mapping that joins the
    two periods, reaching the periods of the pairs that the mapping joins."""
    trellis = specified_from_file(copy(tmp_path))
    assert connector_entry(trellis, (3, "disc", "a"), (2, "port", "k")) == (
        str(tmp_path / PORT_CONS_COPY),
        address,
        periods,
        "disc.a: k",
        None,
        (3, "cons"),
        ("cntn", "a", ("cons", "disc")),
    )


@pytest.mark.xfail(
    strict=True,
    reason="The test expects the answer of `connector_entry` for a drag to `cons_one`'s `m`, "
    "where `cons_two` of the same period also arrives, to name `cons_two` in `shared` and the "
    "two occurrences in `held`. Today the answer writes the expected line "
    "`{w: cons_one.m}` and gives None for both `shared` and `held`.",
)
def test_connector_entry_qualifies_a_shared_name_within_a_period_and_between_periods(
    tmp_path,
):
    """`connector_entry` writes the stage key before each endpoint of a drag
    whose field a second stage occurrence holds at the same perch, in the
    period of the drag or in another period to which the written line
    applies, and answers that occurrence with its period in `shared` and the
    perch, the field and the occurrences that hold the field in `held`, for
    a line of the `connectors` list of a period and for a line of the
    inter-period mapping."""
    from bellman.factory.file_entries import connector_entry

    file = two_cons_period(tmp_path / "two-cons")
    trellis = specify_trellis(load_trellis(file))
    six = (0, 1, 2, 3, 4, 5)
    arriving = ("arvl", "m", ("cons_one", "cons_two"))
    assert connector_entry(trellis, (1, "port", "w"), (1, "cons_one", "m")) == (
        str(file),
        "periods[0].connectors[0]",
        six,
        "{w: cons_one.m}",
        None,
        (1, "cons_two"),
        arriving,
    )
    assert connector_entry(trellis, (2, "disc", "a"), (1, "cons_one", "m")) == (
        str(file),
        "inter_connectors[0]",
        six,
        "disc.a: cons_one.m",
        None,
        (1, "cons_two"),
        arriving,
    )
    registry = emptied_portfolio(tmp_path / "portfolio")
    entries, recipe = registry / "trellis.yml", registry / "spec.yml"
    entry = "- {template: period.yml, repeat: 6}"
    assert entries.read_text(encoding="utf-8").count(entry) == 1
    # the occurrence the second entry adds, the stages it lists, the stage
    # folder of the added occurrence, and each drag with its answer
    for key, stages, stage, drags in (
        (
            "cons_two",
            "port, cons, cons_two, disc",
            "cons",
            [
                (
                    (0, "port", "m_next"),
                    (0, "cons", "m"),
                    (
                        str(registry / "period.yml"),
                        "connectors[0]",
                        six,
                        "{m_next: cons.m}",
                        None,
                        (3, "cons_two"),
                        ("arvl", "m", ("cons", "cons_two")),
                    ),
                ),
                (
                    (3, "disc", "a"),
                    (2, "cons", "m"),
                    (
                        str(entries),
                        "inter_connectors[0]",
                        six,
                        "disc.a: cons.m",
                        None,
                        (3, "cons_two"),
                        ("arvl", "m", ("cons", "cons_two")),
                    ),
                ),
            ],
        ),
        (
            "port_two",
            "port, port_two, cons, disc",
            "port",
            [
                (
                    (2, "port", "m_next"),
                    (1, "cons", "m"),
                    (
                        str(entries),
                        "inter_connectors[0]",
                        six,
                        "port.m_next: m",
                        None,
                        (3, "port_two"),
                        ("cntn", "m_next", ("port", "port_two")),
                    ),
                ),
            ],
        ),
    ):
        texts = {
            str(entries.resolve()): entries.read_text(encoding="utf-8").replace(
                entry,
                "- {template: period.yml, repeat: 3}\n"
                f"  - {{template: period.yml, repeat: 3, stages: [{stages}]}}",
            ),
            str(recipe.resolve()): recipe.read_text(encoding="utf-8")
            + f"  {key}: {{stage: stages/{stage}/{stage}.bl, calibration: "
            f"{{all: [calibration/portfolio]}}, settings: {{all: [settings/{stage}]}}, "
            f"methods: {{all: [stages/{stage}/methods]}}}}\n",
        }
        trellis = specify_trellis(load_recipe(registry, "spec.yml", texts))
        for writing, reading, answer in drags:
            assert connector_entry(trellis, writing, reading, texts) == answer, (writing, reading)


def test_written_spans_answers_what_written_at_and_entry_span_answer_reading_each_file_once(
    spans_trellis, counted_reads
):
    """`written_spans` answers for each address the file and the span that
    `written_at` and `entry_span` give, or None, reading the trellis file once
    and parsing each of the two files once."""
    reads, parsed = counted_reads
    expected = spans_on_disk(spans_trellis)
    reads.clear()
    parsed.clear()
    assert written_spans(spans_trellis, ADDRESSES) == expected
    assert reads == [spans_trellis] and len(parsed) == 2


def test_written_spans_reads_an_unsaved_period_text_in_its_place_reading_each_file_once(
    spans_trellis, counted_reads
):
    """Given a text of the period file with a comment line added above it,
    `written_spans` answers each address of the period file one line lower,
    reading the trellis file once and parsing each of the two texts once."""
    reads, parsed = counted_reads
    expected = spans_on_disk(spans_trellis)
    reads.clear()
    parsed.clear()
    refreshed = written_spans(spans_trellis, ADDRESSES, unsaved_period_text(spans_trellis))
    assert reads == [spans_trellis] and len(parsed) == 2
    assert refreshed[0][1].line == expected[0][1].line + 1
    # the two addresses that the trellis file writes are answered as before
    assert refreshed[40:42] == expected[40:42]
    assert refreshed[42][1].line == expected[42][1].line + 1
    assert refreshed[43:] == (None, None, None)


def test_written_spans_keeps_no_unsaved_text_for_a_later_call(spans_trellis):
    """After a call with an unsaved text of the period file, `written_spans`
    given no text answers from the files on disk."""
    expected = spans_on_disk(spans_trellis)
    written_spans(spans_trellis, ADDRESSES, unsaved_period_text(spans_trellis))
    assert written_spans(spans_trellis, ADDRESSES) == expected


def test_written_spans_leaves_the_period_file_on_disk_unchanged(spans_trellis):
    """A call of `written_spans` with an unsaved text of the period file
    leaves the period file on disk as it was."""
    written_spans(spans_trellis, ADDRESSES, unsaved_period_text(spans_trellis))
    assert not (spans_trellis.parent / "period.yml").read_text().startswith("# unsaved")


def test_written_spans_answers_none_for_an_address_that_is_no_string_or_does_not_parse(
    spans_trellis,
):
    """`written_spans` answers None for an address that is a number or that
    does not parse, and answers the other addresses beside them."""
    expected = spans_on_disk(spans_trellis)
    mixed = (ADDRESSES[0], 17, "periods[bad]", ADDRESSES[40])
    assert written_spans(spans_trellis, mixed) == (expected[0], None, None, expected[40])


def test_written_spans_answers_none_for_an_address_of_an_unsaved_period_file_that_does_not_read(
    spans_trellis,
):
    """`written_spans` answers None for an address that an unsaved text of the
    period file writes where that text does not read, and answers an address
    of the trellis file."""
    broken = {str((spans_trellis.parent / "period.yml").resolve()): "stages: [\n"}
    mixed = written_spans(spans_trellis, (ADDRESSES[0], "inter_connectors", None), broken)
    assert mixed == (
        None,
        (str(spans_trellis), entry_span(spans_trellis.read_text(), "inter_connectors")),
        None,
    )


def test_written_spans_answers_none_for_every_address_where_an_unsaved_trellis_text_does_not_read(
    spans_trellis,
):
    """`written_spans` answers None for every address where an unsaved text of
    the trellis file does not read."""
    broken = {str(spans_trellis.resolve()): "periods: [\n"}
    assert written_spans(spans_trellis, (ADDRESSES[0], "inter_connectors"), broken) == (None, None)


# the calibration file writes `ρ` at lines 2 and 3, and the copied settings
# file writes `n_m` at line 6 and again at line 7
@pytest.mark.parametrize(
    ("reading", "source", "key", "line"),
    [
        pytest.param("calibration_of_a_copy", "calibration.yml", "ρ", 3, id="calibrate"),
        pytest.param("settings_of_a_methodized_copy", "settings.yml", "n_m", 7, id="configure"),
        pytest.param("loading_of_the_trellis", "calibration.yml", "ρ", 3, id="load_trellis"),
    ],
)
def test_a_key_written_twice_in_a_file_that_binds_a_stage_is_refused_under_readable_file(
    request, cons_sources, twice_written_files, reading, source, key, line
):
    """A calibration or a settings file that writes a key twice is refused
    under `readable-file` on each path that reads it, the refusal naming the
    file, the second line and both lines in its message."""
    assert cons_sources["settings"].read_text(encoding="utf-8").count("  n_m: 8000") == 1
    read = request.getfixturevalue(reading)
    with pytest.raises(FactoryError) as refused:
        read()
    path = twice_written_files / source
    assert (
        refused.value.rule,
        refused.value.file,
        refused.value.written,
        refused.value.write,
    ) == (
        "readable-file",
        str(path),
        f"{key!r} at line {line}",
        f"one `{key}:` entry",
    )
    written_twice = f"in {path.name}, at line {line - 1} and again at line {line}"
    assert f"the key {key!r} is written twice {written_twice}" in refused.value.message


def test_a_key_written_twice_in_a_source_of_a_recipe_is_refused_under_recipe_source(tmp_path):
    """A calibration file of a recipe that writes a key twice is refused under
    `recipe-source` when the recipe is loaded."""
    registry = write_registry(
        tmp_path / "registry", {"calibration/main.yml": "calibration:\n  β: 0.96\n  β: 0.5\n"}
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml")
    assert (refused.value.rule, refused.value.write) == ("recipe-source", "one `β:` entry")
