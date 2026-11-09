"""The snapshot guard, the first layer of the tests
(`packages/bellman/README.md` §8), and the recordings of the corpus test.

Every view of the eight corpus stages at every grain, with the stage's own
printed face, card, stage graph and conditions, equals the recording in
`tests/snapshot/`. The recording is of the package as it is; a package
amendment re-records it once, naming the differences it expects. The guard is
one of the sweeps (marker `sweep`), run before a lane's acceptance and at its
merge; a failure names the first difference and every differing leaf of the
stage and selection, by box and field, as `record.py --leaves` lists them.

The recordings the corpus test `tests/test_snapshot.py` compares stand in
`tests/snapshot/corpus/`, one folder per application. Every stage file that
test collects has the recording of its parsed term and that of its encoding,
save a recording the test's tables leave out; every recording there is one of
a stage file that test collects; and `record.py --corpus` writes again, byte
for byte, every recording there that the corpus test compares.
"""
import pytest

from conftest import CORPUS, ROOT, STAGE_FILES as CORPUS_FILES
from snapshot.record import (APPLICATIONS, CORPUS_RECORDINGS, SELECTIONS, compared_suffixes,
                             differing_leaves, first_difference, record, recording_path, stored,
                             write_corpus_recordings)

STAGES = ("cons", "cons_obs", "port", "ez_savings", "cons_savings_iid", "sa_savings", "tenure", "retiree_death")


@pytest.mark.sweep
@pytest.mark.parametrize("name", STAGES)
def test_the_stage_and_every_view_at_every_grain_equal_their_recording(request, name):
    """One snapshot comparison includes every stage, direction and grain."""
    import json
    differences = []
    stage = request.getfixturevalue(name)
    for selection in SELECTIONS:
        live = json.loads(json.dumps(record(stage, selection), ensure_ascii=False))
        recorded = stored(name)[selection]
        if live != recorded:
            leaves = "; ".join(
                f"{box or 'the selection'}: {field or 'the whole box'}"
                for box, field in differing_leaves(recorded, live))
            differences.append(
                f"stage {name}, {selection}: {first_difference(recorded, live)}; {leaves}")
    assert differences == [], "\n".join(differences)


@pytest.mark.sweep
@pytest.mark.parametrize("src", CORPUS_FILES, ids=lambda path: path.relative_to(APPLICATIONS).as_posix())
def test_application_sources_and_encodings_match_their_recordings(application_stage, parsed_source, src):
    """Every source term and live encoding equals its recorded full value.

    Refused applications retain their exact rule and reason. No case is
    skipped. The encoding hashes are checked against prior schema validation.
    """
    import json
    from bellman.refusals import ConstructionError
    from bellman.syntax.lower import to_json
    from bellman.syntax.decode import from_json
    from snapshot.corpus_cases import KNOWN_UNELABORATABLE

    differences = []
    relative = src.relative_to(APPLICATIONS).as_posix()
    term = parsed_source(src).term
    expected_term = json.loads(recording_path(src, ".ast.json").read_text(encoding="utf-8"))
    decoded = from_json(expected_term)
    assert decoded == term, relative
    assert to_json(decoded) == expected_term, relative
    assert (json.dumps(to_json(term), indent=2, ensure_ascii=False) + "\n"
            == recording_path(src, ".ast.json").read_text(encoding="utf-8")), relative
    if to_json(term) != expected_term:
        differences.append(f"{relative}: parsed source differs")
    try:
        stage = application_stage(src)
    except ConstructionError as error:
        if relative not in KNOWN_UNELABORATABLE:
            raise
        rule, reason = KNOWN_UNELABORATABLE[relative]
        assert error.rule == rule and reason in error.message, relative
        return
    assert relative not in KNOWN_UNELABORATABLE, f"{relative}: now elaborates; review its recording"
    live = json.loads(json.dumps(stage.encoding()))
    expected = json.loads(recording_path(src, ".stage.json").read_text(encoding="utf-8"))
    if live != expected:
        differences.append(f"{relative}: {first_difference(expected, live)}")
    assert differences == [], "\n".join(differences)


def test_every_stage_file_of_the_corpus_has_its_two_recordings():
    """Each stage file the corpus test collects has the recording of its
    parsed term and that of its encoding, each at a path of its own, save a
    recording the corpus test's tables leave out."""
    paths = [recording_path(src, suffix)
             for src in CORPUS_FILES for suffix in compared_suffixes(src)]
    assert len(set(paths)) == len(paths)
    missing = [path.relative_to(CORPUS_RECORDINGS).as_posix() for path in paths
               if not path.is_file()]
    assert missing == []


def test_every_recording_of_the_corpus_belongs_to_a_stage_file_the_corpus_test_collects():
    """No recording in `tests/snapshot/corpus/` stands without its stage file,
    so that a stage file the corpus test no longer collects is named by the
    recordings it leaves behind."""
    patterns = [recording_path(src, ".*json") for src in CORPUS_FILES]
    held = {path for pattern in patterns for path in pattern.parent.glob(pattern.name)}
    assert [path.relative_to(CORPUS_RECORDINGS).as_posix()
            for path in sorted(CORPUS_RECORDINGS.glob("*/*.json")) if path not in held] == []


def test_the_corpus_writer_preserves_the_recording_text_and_paths(tmp_path):
    """The writer preserves formatting and the application-relative paths.

    The corpus tests compare every parsed term and stage encoding. Repeating
    their construction here adds no semantic coverage.
    """
    src = ROOT / CORPUS["cons"]
    written = write_corpus_recordings(src, tmp_path)
    assert set(written) == {".ast.json", ".stage.json"}
    assert all(path.parent == tmp_path / "portfolio-choice" for path in written.values())
    assert [suffix for suffix, path in written.items()
            if path.read_bytes() != recording_path(src, suffix).read_bytes()] == []


def test_recorded_encodings_were_validated_against_the_current_schema():
    """Full live equality and these exact hashes imply schema validity."""
    import json
    from snapshot.validate_encodings import VALIDATIONS, digest, recording_hashes, schema_bytes

    validated = json.loads(VALIDATIONS.read_text(encoding="utf-8"))
    assert validated["schema_sha256"] == digest(schema_bytes()), (
        "Schema changed: run tests/snapshot/validate_encodings.py and review its result.")
    assert validated["recordings"] == recording_hashes(), (
        "Recordings changed: run tests/snapshot/validate_encodings.py and review its result.")


@pytest.mark.sweep
def test_complete_cards_equal_the_recording(application_stage):
    """The formatting corpus retains every complete card and source path."""
    import json
    from snapshot.record_cards import CARD_SOURCES, RECORDING, card_texts

    recorded = json.loads(RECORDING.read_text(encoding="utf-8"))
    assert set(recorded) == set(CARD_SOURCES)
    differences = []
    for name, source in CARD_SOURCES.items():
        live = {"source": source, "cards": card_texts(application_stage(ROOT / source))}
        if recorded[name] != live:
            differences.append(f"{name}: {first_difference(recorded[name], live)}")
    assert differences == [], "\n".join(differences)
