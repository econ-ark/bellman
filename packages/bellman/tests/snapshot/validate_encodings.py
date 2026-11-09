"""Record which exact stage encodings have passed the exact JSON schema.

Run this file with the project interpreter after changing the schema or a
recording. Tests compare both hashes and the entire live encoding. Together,
those comparisons preserve schema validity without validating unchanged JSON
objects again. This command never changes an encoding recording.
"""
from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATIONS = HERE / "schema_validations.json"


def schema_bytes():
    return files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def recording_hashes():
    return {path.relative_to(HERE).as_posix(): digest(path.read_bytes())
            for path in sorted((HERE / "corpus").glob("*/*.stage.json"))}


def validate_recordings():
    """Validate every recorded encoding before writing the hash record."""
    from jsonschema import Draft202012Validator

    schema = schema_bytes()
    document = json.loads(schema)
    Draft202012Validator.check_schema(document)
    validator = Draft202012Validator(document)
    hashes = recording_hashes()
    for name, expected in hashes.items():
        data = (HERE / name).read_bytes()
        assert digest(data) == expected, f"recording changed during validation: {name}"
        validator.validate(json.loads(data))
    result = {"schema_sha256": digest(schema), "recordings": hashes}
    VALIDATIONS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = validate_recordings()
    print(f"Validated {len(result['recordings'])} stage encodings; wrote {VALIDATIONS}")
