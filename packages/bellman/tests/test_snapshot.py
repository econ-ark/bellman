"""The snapshot guard, the first layer of the tests
(`packages/bellman/README.md` §8), and the recordings of the corpus test.

Every view of the eight corpus stages at every grain, with the stage's own
printed face, card, stage graph and conditions, equals the recording in
`tests/snapshot/`. The recording is of the package as it is; a package
amendment re-records it once, naming the differences it expects. The guard is
one of the sweeps (marker `sweep`), run before a lane's acceptance and at its
merge; a failure names the first difference and every differing leaf of the
stage and selection, by box and field, as `record.py --leaves` lists them.

The recordings the corpus test `tests/sym/test_corpus.py` compares stand in
`tests/snapshot/corpus/`, one folder per application. Every stage file that
test collects has the recording of its parsed term and that of its encoding,
save a recording the test's tables leave out; every recording there is one of
a stage file that test collects; and `record.py --corpus` writes again, byte
for byte, every recording there: the recordings the corpus test compares and
the encoding of the specified version of `portfolio-choice/cons.bl`, which
`test_behaviour.py` compares.
"""
import pytest

from snapshot.record import (CORPUS_RECORDINGS, SELECTIONS, compared_suffixes, differing_leaves,
                             first_difference, record, recording_path, stored,
                             write_corpus_recordings)
from sym.test_corpus import APPLICATIONS, CORPUS as CORPUS_FILES

STAGES = ("cons", "cons_obs", "port", "ez_savings", "cons_savings_iid", "sa_savings", "tenure", "retiree_death")


@pytest.mark.sweep
@pytest.mark.parametrize("selection", SELECTIONS)
@pytest.mark.parametrize("name", STAGES)
def test_the_stage_and_every_view_at_every_grain_equal_their_recording(request, name, selection):
    import json
    live = json.loads(json.dumps(record(request.getfixturevalue(name), selection), ensure_ascii=False))
    recorded = stored(name)[selection]
    if live != recorded:
        leaves = "; ".join(f"{box or 'the selection'}: {field or 'the whole box'}"
                           for box, field in differing_leaves(recorded, live))
        pytest.fail(f"stage {name}, {selection}: {first_difference(recorded, live)}\n"
                    f"every differing leaf, by box and field: {leaves}", pytrace=False)


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


@pytest.mark.sweep
@pytest.mark.parametrize("src", CORPUS_FILES,
                         ids=lambda path: path.relative_to(APPLICATIONS).as_posix())
def test_the_corpus_option_reproduces_every_recording(src, tmp_path):
    """The recordings `record.py --corpus` writes of a stage file equal the
    stored ones byte for byte. Each case writes one stage file's recordings
    into a temporary folder with the function the option calls for every
    stage file."""
    written = write_corpus_recordings(src, tmp_path)
    assert [suffix for suffix, path in written.items()
            if path.read_bytes() != recording_path(src, suffix).read_bytes()] == []
