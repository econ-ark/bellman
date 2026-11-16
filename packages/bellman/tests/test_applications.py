"""The recordings of the stage files of the applications, the parsed term,
the printed text, the text of the graphs and the digests of the encoding of
each, and the scripts that write them."""

import hashlib
import json
from pathlib import Path

import pytest
from application_files import (
    ADJUSTER_CONS_WITH_EGM_LINES_FILE,
    CORPUS,
    ROOT,
    STAGE_FILES,
    stage_file_id,
)
from snapshot.corpus_cases import REFUSED_STAGE_FILES
from snapshot.record import (
    ADJUSTER_CONS_PRINTED_TEXT_PATH,
    APPLICATIONS,
    CORPUS_RECORDINGS,
    CORPUS_STAGE_FILES,
    DELETE_BY_HAND_INSTRUCTION,
    ELABORATED_FILES,
    GRAPHS_SUFFIX,
    compared_suffixes,
    folder_outside_the_repository,
    graphs_text,
    left_over_files,
    missing_recordings_message,
    recording_path,
    stage_printed_text,
    text_difference,
    write_adjuster_cons_printed_text,
    write_corpus_recordings,
    write_encodings,
)
from snapshot.validate_encodings import (
    DIGESTS_FILE,
    RECORD_DIGESTS_COMMAND,
    digest,
    digest_key,
    digest_message,
    digests_of_text,
    encoding_digests,
    recorded_digests,
    schema_bytes,
)
from two_sets import one_row_by_default

from bellman.refusals import ConstructionError
from bellman.syntax.decode import from_json
from bellman.syntax.lower import to_json

# a small stage file that elaborates, for the tests of the writer of the
# encodings
SMALL_STAGE_FILE = APPLICATIONS / "durables/declaration/stages/disc/disc.bl"


# the stage file among the fixtures of the tests whose printed text is
# recorded beside those of the applications: the adjuster stage of the
# durables model, with the lines of the endogenous grid method written in its
# policy block
ADJUSTER_STAGE_FILE = ROOT / ADJUSTER_CONS_WITH_EGM_LINES_FILE


# the recording of the printed text of each stage file whose printed text is
# recorded: each stage file of the applications that elaborates, and the
# adjuster stage file of the fixtures
PRINTED_RECORDINGS = {src: recording_path(src, ".printed.txt") for src in ELABORATED_FILES}
PRINTED_RECORDINGS[ADJUSTER_STAGE_FILE] = CORPUS_RECORDINGS / ADJUSTER_CONS_PRINTED_TEXT_PATH


def printed_recording_id(src):
    """The test identifier of a stage file of PRINTED_RECORDINGS: its path
    under `applications/`, or the name of the adjuster stage file of the
    fixtures."""
    return ADJUSTER_STAGE_FILE.name if src == ADJUSTER_STAGE_FILE else stage_file_id(src)


def encoding_text_of_version(version):
    """The stored text of a small encoding that records `version` where the
    encoding of a stage records it, beside one other section and one section
    of `derived`."""
    encoding = {
        "package_version": version,
        "name": "cons",
        "provenance": {"versions": {"package": version}},
        "derived": {"stage": {"name": "cons"}},
    }
    return json.dumps(encoding, ensure_ascii=False, sort_keys=True) + "\n"


# a short text in the form of a printed text: the stage's own text, then two
# sections, each opened by its line `==== <title> ====`
SHORT_PRINTED_TEXT = (
    "stage cons\n"
    "origin: cons.bl\n"
    "\n"
    "==== stage ====\n"
    "V = u(c) + β*V[>]\n"
    "\n"
    "==== backward cntn_to_dcsn ====\n"
    "c = (β*dV[>])^(-1/ρ)\n"
    "m = a + c\n"
)


# a short text in the form of a text of the graphs, whose last section is
# written as the same as the section before it
SHORT_GRAPHS_TEXT = (
    "==== wires ====\n"
    "cons:function:cntn:V\n"
    "\n"
    "==== builders backward builder: wiring ====\n"
    "inputs: cons:function:cntn:V\n"
    "outputs: cons:function:arvl:V\n"
    "\n"
    "==== builders backward primitive: wiring ====\n"
    "the same as builders backward builder: wiring\n"
)


# the line that ends every message of `text_difference`
RECORD_AGAIN = (
    "After reading the difference, run from packages/bellman the command that writes the "
    "recordings again: python tests/snapshot/record.py --corpus"
)


@pytest.fixture(scope="module")
def table_of_digests():
    """The table that `encoding_digests.json` holds: the digest of the schema
    of encodings, and the digests of the encoding of each stage file."""
    return json.loads(DIGESTS_FILE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("src", one_row_by_default(STAGE_FILES), ids=stage_file_id)
def test_a_stage_file_parses_to_the_term_that_its_recording_holds(parsed_source, src):
    """The term that the parser gives of a stage file equals the term that
    `from_json` reads from the recording of its parsed term."""
    term = parsed_source(src).term
    path = recording_path(src, ".ast.json")
    assert path.is_file(), missing_recordings_message([(src, path)])
    recorded = path.read_bytes().decode("utf-8")
    assert from_json(json.loads(recorded)) == term


@pytest.mark.parametrize("src", one_row_by_default(STAGE_FILES), ids=stage_file_id)
def test_the_parsed_term_of_a_stage_file_is_written_as_the_text_of_its_recording(
    parsed_source, src
):
    """The term that the parser gives of a stage file, written by `to_json`
    as JSON indented by two spaces, equals the text of the recording of its
    parsed term."""
    term = parsed_source(src).term
    path = recording_path(src, ".ast.json")
    assert path.is_file(), missing_recordings_message([(src, path)])
    recorded = path.read_bytes().decode("utf-8")
    assert json.dumps(to_json(term), indent=2, ensure_ascii=False) + "\n" == recorded


# the two refused stage files in the default set: the first file of the
# table, and renter_housing.bl, the smallest of the three files refused at a
# grid constructor; the other four files are in the complete set
DEFAULT_REFUSED_FILES = (
    "cagetti-denardi-2006/declaration/stages/old_entrepreneur/old_entrepreneur.bl",
    "housing-renting/declaration/stages/renter_housing/renter_housing.bl",
)


@pytest.mark.parametrize(
    "relative",
    [
        pytest.param(
            relative, marks=() if relative in DEFAULT_REFUSED_FILES else pytest.mark.complete_set
        )
        for relative in REFUSED_STAGE_FILES
    ],
    ids=str,
)
def test_a_refused_stage_file_is_refused_by_its_recorded_rule(read_only_stage_from_file, relative):
    """The elaboration of a stage file that KNOWN_UNELABORATABLE holds raises
    a `ConstructionError` with the rule that the table records, whose message
    holds the phrase that the table records."""
    rule, reason = REFUSED_STAGE_FILES[relative]
    # when the package starts to elaborate the stage file, this test fails;
    # then remove the file from KNOWN_UNELABORATABLE and run record.py --corpus
    with pytest.raises(ConstructionError) as refused:
        read_only_stage_from_file(APPLICATIONS / relative)
    assert refused.value.rule == rule
    assert reason in refused.value.message


def test_every_stage_file_has_each_of_its_recordings():
    """Each stage file of the applications has a recording of each kind that
    `compared_suffixes` gives for it, each at a path of its own."""
    pairs = [
        (src, recording_path(src, suffix))
        for src in STAGE_FILES
        for suffix in compared_suffixes(src)
    ]
    assert len({path for _, path in pairs}) == len(pairs)
    missing = [(src, path) for src, path in pairs if not path.is_file()]
    assert missing == [], missing_recordings_message(missing)


def test_every_file_in_the_folder_of_the_recordings_is_a_recording_that_a_test_compares():
    """Every file under `tests/snapshot/corpus/`, of any suffix, is a
    recording that a test of this file compares."""
    # a stage file that no stage folder holds any longer, or a recording that
    # no test compares any longer, leaves behind a file that the message names
    left_over = left_over_files()
    assert left_over == [], (
        f"No test compares these files under tests/snapshot/corpus/: {', '.join(left_over)}.\n"
        f"{DELETE_BY_HAND_INSTRUCTION}"
    )


def test_left_over_files_names_each_visible_file_that_no_test_compares(tmp_path):
    """In a folder laid out as the folder of the recordings, `left_over_files`
    names exactly the files that no test compares, leaving out each file whose
    name or folder begins with a dot."""
    compared = [
        "portfolio-choice/cons.bl.ast.json",
        "portfolio-choice/cons.bl.printed.txt",
        ADJUSTER_CONS_PRINTED_TEXT_PATH.as_posix(),
    ]
    hidden = [
        "portfolio-choice/.DS_Store",
        "portfolio-choice/.ipynb_checkpoints/cons.bl.printed.txt",
    ]
    # the printed text of a stage file that the package refuses, which has a
    # parsed term and no printed text, and the printed text of a file that no
    # stage folder holds
    left_over = [
        "housing-owner/housing_choice.bl.printed.txt",
        "portfolio-choice/retired.bl.printed.txt",
    ]
    for name in compared + hidden + left_over:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("", encoding="utf-8")
    assert left_over_files(tmp_path) == left_over


def test_the_table_of_digests_holds_the_stage_files_that_elaborate_and_no_others(
    table_of_digests,
):
    """The keys of `encoding_digests.json` are the keys of the stage files of
    the applications that elaborate."""
    assert sorted(table_of_digests["encodings"]) == sorted(
        digest_key(src) for src in ELABORATED_FILES
    )


def test_the_table_of_digests_was_recorded_with_the_current_schema(table_of_digests):
    """The digest of the schema of encodings that `encoding_digests.json`
    records equals the digest of the schema that the package holds."""
    assert table_of_digests["schema_sha256"] == digest(schema_bytes()), (
        "The schema of encodings changed. After reading the change, run from "
        "packages/bellman the command that validates every encoding against the "
        f"schema and records the digests again: {RECORD_DIGESTS_COMMAND}"
    )


def test_the_recordings_writer_writes_the_stored_recordings_of_a_stage_file(tmp_path):
    """`write_corpus_recordings` writes the parsed term, the printed text and
    the text of the graphs of the consumption stage file in the folder of its
    application under the folder it is given, each with the bytes of its
    stored recording."""
    # one stage file suffices, since the tables of this file compare every
    # recording of every stage file
    src = ROOT / CORPUS["cons"]
    written = write_corpus_recordings(src, tmp_path)
    assert set(written) == {".ast.json", ".printed.txt", ".graphs.txt"}
    assert all(path.parent == tmp_path / "portfolio-choice" for path in written.values())
    assert [
        suffix
        for suffix, path in written.items()
        if path.read_bytes() != recording_path(src, suffix).read_bytes()
    ] == []


def test_write_fixture_text_writes_the_stored_printed_text_of_the_adjuster_stage(tmp_path):
    """`write_adjuster_cons_printed_text` writes the printed text of the
    adjuster stage file of the fixtures at FIXTURE_TEXT under the folder it is
    given, with the bytes of its stored recording."""
    written = write_adjuster_cons_printed_text(tmp_path)
    assert written == tmp_path / ADJUSTER_CONS_PRINTED_TEXT_PATH
    assert (
        written.read_bytes() == (CORPUS_RECORDINGS / ADJUSTER_CONS_PRINTED_TEXT_PATH).read_bytes()
    )


def test_the_encodings_writer_writes_the_text_whose_digest_the_table_records(tmp_path):
    """`write_encodings` writes the encoding of a stage file at
    `<application>/<file>.bl.stage.json` under the folder it is given, as a
    text whose SHA-256 digest is the digest that `encoding_digests.json`
    records for the whole encoding of the stage file."""
    # one small stage file suffices, since a table of this file compares the
    # digests of every stage file that elaborates
    [written] = write_encodings(tmp_path, [SMALL_STAGE_FILE])
    assert written == tmp_path / "durables" / "disc.bl.stage.json"
    recorded = recorded_digests(digest_key(SMALL_STAGE_FILE))["encoding"]
    assert hashlib.sha256(written.read_bytes()).hexdigest() == recorded


def test_the_encodings_writer_refuses_a_folder_inside_the_repository():
    """`write_encodings` refuses the folder of the recordings, a folder inside
    the repository, with a `ValueError` that says so, before it writes an
    encoding there."""
    with pytest.raises(ValueError, match="lies inside the repository"):
        write_encodings(CORPUS_RECORDINGS, [SMALL_STAGE_FILE])
    assert not (CORPUS_RECORDINGS / "durables" / "disc.bl.stage.json").exists()


def test_a_folder_inside_the_repository_written_in_other_case_is_refused():
    """The path of a folder inside the repository, written with the case of
    its letters changed, is refused as a folder for the encodings where the
    file system ignores case, so that the changed path names the same
    folder."""
    changed = Path(str(CORPUS_RECORDINGS).swapcase())
    if not changed.exists():
        pytest.skip(
            "The file system distinguishes the case of letters, so the path "
            "written in other case names no folder of the repository."
        )
    with pytest.raises(ValueError, match="lies inside the repository"):
        folder_outside_the_repository(changed / "encodings")


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_a_stage_file_has_its_recorded_encoding_digests(read_only_stage_from_file, src):
    """The digest of the encoding of the stage elaborated from a stage file,
    and that of each of its sections, equals the digest that
    `encoding_digests.json` records."""
    relative = digest_key(src)
    recorded, live = recorded_digests(relative), encoding_digests(read_only_stage_from_file(src))
    assert live == recorded, digest_message(relative, recorded, live)


@pytest.mark.parametrize(
    "src", one_row_by_default(list(PRINTED_RECORDINGS)), ids=printed_recording_id
)
def test_a_stage_file_prints_its_recorded_text(read_only_stage_from_file, src):
    """The printed text of the stage elaborated from a stage file equals the
    text of the recording of its printed text."""
    live = stage_printed_text(read_only_stage_from_file(src))
    path = PRINTED_RECORDINGS[src]
    assert path.is_file(), missing_recordings_message([(src, path)])
    recorded = path.read_bytes().decode("utf-8")
    assert live == recorded, text_difference(recorded, live)


@pytest.mark.parametrize("src", one_row_by_default(CORPUS_STAGE_FILES), ids=stage_file_id)
def test_a_stage_file_listed_by_name_gives_the_recorded_text_of_its_graphs(
    read_only_stage_from_file, src
):
    """The text of the graphs of the stage elaborated from one of the eight
    stage files that the tests list by name equals the text of the recording
    of its graphs."""
    live = graphs_text(read_only_stage_from_file(src))
    path = recording_path(src, GRAPHS_SUFFIX)
    assert path.is_file(), missing_recordings_message([(src, path)])
    recorded = path.read_bytes().decode("utf-8")
    assert live == recorded, text_difference(recorded, live)


def test_the_digests_of_an_encoding_are_keyed_by_its_sections():
    """`digests_of_text` keys the digest of the whole text by `encoding`,
    the digest of each top-level section by its key, and the digest of each
    section of `derived` by `derived.<key>`."""
    assert sorted(digests_of_text(encoding_text_of_version("0.1.7"))) == [
        "derived.stage",
        "encoding",
        "name",
        "package_version",
        "provenance",
    ]


def test_digests_of_text_refuses_an_encoding_with_a_top_level_key_named_encoding():
    """`digests_of_text` refuses with a `ValueError` an encoding with a
    top-level key named `encoding`, whose digest would take the place of the
    digest of the whole text."""
    with pytest.raises(ValueError, match="top-level key named 'encoding'"):
        digests_of_text(json.dumps({"encoding": {}, "name": "cons"}) + "\n")


def test_an_encoding_records_the_package_version_in_two_sections(cons):
    """The encoding of a stage records the package's version, a text that is
    not empty, in the section `package_version` and as the same text in the
    section `provenance`, under `versions.package`."""
    # the message for a new version of the package relies on this
    encoding = cons.encoding()
    assert encoding["package_version"]
    assert encoding["provenance"]["versions"]["package"] == encoding["package_version"]


def test_a_new_package_version_is_named_with_its_sections_and_the_command_that_records_again():
    """The message for a new version of the package names the two sections
    whose digests differ, `package_version` and `provenance`, says that the
    version changed, says how to read the differences of the two encodings,
    and ends with the command that records the digests again."""
    recorded = digests_of_text(encoding_text_of_version("0.1.7"))
    live = digests_of_text(encoding_text_of_version("0.1.8"))
    assert digest_message("portfolio-choice/cons.bl", recorded, live).splitlines() == [
        "portfolio-choice/cons.bl: the digests of these sections of the encoding differ "
        "from encoding_digests.json: package_version, provenance.",
        "The package's version changed; the encoding records the version in the sections "
        "package_version and provenance.",
        "Where no printed text shows the change, read the differences by running from "
        "packages/bellman python tests/snapshot/record.py --encodings FOLDER at the commit "
        "before the change and at the commit after it, with a new FOLDER outside the "
        "repository each time, and by comparing the two folders.",
        "After reading the differences, run from packages/bellman the command that records "
        "the digests again: python tests/snapshot/validate_encodings.py",
    ]


def test_a_missing_recording_is_named_with_the_command_that_writes_the_recordings():
    """The message for a missing recording names the stage file and the
    recording by their paths in the repository, and ends with the command
    that writes the recordings."""
    src = ROOT / CORPUS["cons"]
    path = recording_path(src, ".printed.txt")
    assert missing_recordings_message([(src, path)]).splitlines() == [
        "The stage file applications/portfolio-choice/declaration/stages/cons/cons.bl has no "
        "recording packages/bellman/tests/snapshot/corpus/portfolio-choice/cons.bl.printed.txt.",
        "Run from packages/bellman the command that writes the recordings: "
        "python tests/snapshot/record.py --corpus",
    ]


@pytest.mark.parametrize(
    "recorded, live, expected",
    [
        pytest.param(
            SHORT_PRINTED_TEXT,
            SHORT_PRINTED_TEXT.replace("m = a + c", "m = a + 2*c"),
            [
                'The texts differ at line 9, in the section "backward cntn_to_dcsn".',
                "recorded: 'm = a + c'",
                "live:     'm = a + 2*c'",
                RECORD_AGAIN,
            ],
            id="a-line-changed-inside-a-section",
        ),
        pytest.param(
            SHORT_PRINTED_TEXT,
            SHORT_PRINTED_TEXT.replace("origin: cons.bl", "origin: port.bl"),
            [
                "The texts differ at line 2, in the stage's own text.",
                "recorded: 'origin: cons.bl'",
                "live:     'origin: port.bl'",
                RECORD_AGAIN,
            ],
            id="a-line-changed-before-the-first-section",
        ),
        # the section that the recorded text writes as the same as the section
        # before it differs from that section, in the live text, in its second
        # line, which takes the number of the line `the same as`
        pytest.param(
            SHORT_GRAPHS_TEXT,
            SHORT_GRAPHS_TEXT.replace(
                "the same as builders backward builder: wiring",
                "inputs: cons:function:cntn:V\noutputs: cons:function:dcsn:V",
            ),
            [
                'The texts differ at line 9, in the section "builders backward primitive: '
                'wiring".',
                "recorded: 'outputs: cons:function:arvl:V'",
                "live:     'outputs: cons:function:dcsn:V'",
                RECORD_AGAIN,
            ],
            id="a-section-once-the-same-as-another-and-now-changed",
        ),
    ],
)
def test_the_text_difference_names_the_number_and_the_section_of_the_first_changed_line(
    recorded, live, expected
):
    """The message of `text_difference` for two texts of which a line differs
    names the number of the first such line in the recorded text and its
    section, or the stage's own text before the first section, shows that line
    as recorded and as it is now, and ends with the command that writes the
    recordings again."""
    assert text_difference(recorded, live).splitlines() == expected


def test_the_text_difference_says_which_text_has_more_lines():
    """A line added at the end of the live text is named as a line the live
    text has more than the recorded text, with its number and section."""
    live = SHORT_PRINTED_TEXT + "a = m - c\n"
    assert text_difference(SHORT_PRINTED_TEXT, live).splitlines() == [
        "The live text has 1 more line than the recorded text, from line 10, "
        'in the section "backward cntn_to_dcsn".',
        "live:     'a = m - c'",
        RECORD_AGAIN,
    ]


def test_the_text_difference_says_which_text_ends_with_a_newline():
    """Two texts whose lines are equal and of which only one ends with a
    newline are named as differing only at their end."""
    shorter = SHORT_PRINTED_TEXT.removesuffix("\n")
    assert text_difference(SHORT_PRINTED_TEXT, shorter).splitlines() == [
        "The texts differ only at their end: the recorded text ends "
        "with a newline and the other does not.",
        RECORD_AGAIN,
    ]
