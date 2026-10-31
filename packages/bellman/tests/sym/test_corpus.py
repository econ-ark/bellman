"""The corpus test: every spec example parses, and its JSON term
encoding reproduces its recording `.ast.json` exactly (the hub ruling: the
recorded encodings are the conformance targets). The recordings stand in
`tests/snapshot/corpus/`, where `tests/snapshot/record.py --corpus` writes
them."""

import json
import pathlib

import pytest

from bellman.syntax.lower import parse_with_spans, to_json
from bellman.refusals import ConstructionError
from conftest import CORPUS as STAGES
from snapshot.record import recording_path

APPLICATIONS = pathlib.Path(__file__).resolve().parents[4] / "applications"
# the stage files of the applications, each in its stage folder,
# `declaration/stages/<key>/<key>.bl`
CORPUS = sorted(APPLICATIONS.glob("*/declaration/stages/*/*.bl"))

# Files that do not currently parse, each with its recorded reason —
# design or authoring running ahead of the grammar, never a defect of
# the parser. Empty since the sketch line of housing-owner's
# consumption_choice.bl was removed; the file parses and is recorded.
KNOWN_UNPARSEABLE = {}

# Files committed without the recording of the parsed term the corpus test
# compares against, each with the commit that added it; the case fails
# strictly once the recording is written.
KNOWN_WITHOUT_ENCODING = {
    "buffer_stock": ("applications/buffer-stock/ was committed at d2b5b051c without the "
                     "recording buffer_stock.bl.ast.json"),
}


# These files parse but their construction is not admitted at the fixed base.
KNOWN_UNELABORATABLE = {
    # the two entrepreneur stages list a control beside the label (E14); the
    # three housing files define a set by a grid constructor or select a
    # family by a discrete state
    "cagetti-denardi-2006/declaration/stages/old_entrepreneur/old_entrepreneur.bl":
        ("not-constructed", "beside its branches"),
    "cagetti-denardi-2006/declaration/stages/young_entrepreneur/young_entrepreneur.bl":
        ("not-constructed", "beside its branches"),
    "housing-owner/declaration/stages/consumption_choice/consumption_choice.bl":
        ("not-constructed", "grid constructor"),
    "housing-owner/declaration/stages/housing_choice/housing_choice.bl":
        ("family-selection", "z_vals[y]"),
    "housing-renting/declaration/stages/owner_housing/owner_housing.bl":
        ("not-constructed", "grid constructor"),
    "housing-renting/declaration/stages/renter_housing/renter_housing.bl":
        ("not-constructed", "grid constructor"),
}

@pytest.mark.parametrize("src", CORPUS, ids=lambda path: path.relative_to(APPLICATIONS).as_posix())
def test_example_stage_encoding(src, request, elaborate_text):
    """The stage's encoding validates against the one schema, and equals its
    recording `.stage.json`, which is that encoding as written under the same
    schema (decision S3 of the structure review's cleanup)."""
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    relative = src.relative_to(APPLICATIONS).as_posix()
    origin = "applications/" + relative
    names = {path: name for name, path in STAGES.items()}
    try:
        stage = (request.getfixturevalue(names[origin]) if origin in names
                 else elaborate_text(src.read_text(encoding="utf-8"), origin))
    except ConstructionError as error:
        if relative not in KNOWN_UNELABORATABLE:
            raise
        rule, reason = KNOWN_UNELABORATABLE[relative]
        assert error.rule == rule and reason in error.message
        pytest.xfail(f"{rule}: {reason}")
    assert relative not in KNOWN_UNELABORATABLE, "This file now elaborates; record its fixture."
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    answer = json.loads(json.dumps(stage.encoding()))
    Draft202012Validator(schema).validate(answer)
    assert answer == json.loads(recording_path(src, ".stage.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("src", [
    pytest.param(path, marks=pytest.mark.xfail(reason=KNOWN_WITHOUT_ENCODING[path.stem], strict=True))
    if path.stem in KNOWN_WITHOUT_ENCODING else path for path in CORPUS], ids=lambda p: p.stem)
def test_example_parses_and_encodes(src):
    if src.stem in KNOWN_UNPARSEABLE:
        pytest.xfail(KNOWN_UNPARSEABLE[src.stem])
    term, _ = parse_with_spans(src.read_text(encoding="utf-8"), str(src))
    recorded = recording_path(src, ".ast.json")
    assert recorded.exists(), f"no recording of the parsed term of {src.name}"
    assert to_json(term) == json.loads(recorded.read_text(encoding="utf-8"))
