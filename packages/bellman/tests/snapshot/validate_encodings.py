"""Validate the encoding of every stage file that the tests of the recordings
elaborate against the JSON schema, and record the SHA-256 digests of each
encoding.

Run this file from `packages/bellman` with the project interpreter after a
change has altered an encoding or the schema, once the differences that the
failing test names have been read:

    python tests/snapshot/validate_encodings.py

Run as a script, the file reads the package `bellman` of the checkout that
holds it, whatever copy the environment has installed. It elaborates each
stage file that the tests of the recordings elaborate, validates the live
encoding against the schema, and only then writes `encoding_digests.json`:
the digest of the schema and, for each stage file, the digests that
`encoding_digests` returns. It writes no encoding; this command writes the
encodings in FOLDER, outside the repository:

    python tests/snapshot/record.py --encodings FOLDER
"""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
if __name__ == "__main__":
    from snapshot import put_this_checkout_first

    put_this_checkout_first()

from stage_builders import stage_from_file  # noqa: E402

from snapshot.record import (  # noqa: E402
    CORPUS_RECORDINGS,
    ELABORATED_FILES,
    WRITE_ENCODINGS_COMMAND,
    encoding_as_stored,
    recording_path,
)

if TYPE_CHECKING:
    from bellman.stage import ElaboratedStage

DIGESTS_FILE = HERE / "encoding_digests.json"
# the command, run from packages/bellman, that records the digests again
RECORD_DIGESTS_COMMAND = "python tests/snapshot/validate_encodings.py"
# the instruction that says how to read the differences of two encodings
ENCODING_DIFFERENCE_INSTRUCTION = (
    "Where no printed text shows the change, read the differences by running from "
    f"packages/bellman {WRITE_ENCODINGS_COMMAND} at the commit before the change and at the "
    "commit after it, with a new FOLDER outside the repository each time, and by "
    "comparing the two folders."
)


def schema_bytes() -> bytes:
    """The bytes of the JSON schema of the encoding of a stage."""
    return files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_bytes()


def digest(data: bytes) -> str:
    """The SHA-256 digest of `data`, in hexadecimal."""
    return hashlib.sha256(data).hexdigest()


def digest_key(stage_path: Path | str) -> str:
    """The key of the stage file `stage_path` in `encoding_digests.json`,
    `<application>/<file>.bl`: the folder and the name that `recording_path`
    gives the recordings of the file under `corpus/`."""
    return recording_path(stage_path, "").relative_to(CORPUS_RECORDINGS).as_posix()


def digests_of_text(text: str) -> dict[str, str]:
    """The SHA-256 digests of the stored text `text` of an encoding, by
    section.

    The key `encoding` holds the digest of `text` in UTF-8. Each other key
    names one section: a top-level key of the encoding other than `derived`,
    or `derived.<key>` for a key of `derived`. Its value is the digest of the
    section written as JSON with sorted keys, in UTF-8. An encoding with a
    top-level key named `encoding` raises a `ValueError`, since the digest of
    that section would take the place of the digest of the whole text."""
    encoding = json.loads(text)
    if "encoding" in encoding:
        raise ValueError(
            "The encoding has a top-level key named 'encoding'. Its digest would "
            "take the place of the digest of the whole text, which the table of "
            "digests keeps under that name."
        )
    sections = {key: value for key, value in encoding.items() if key != "derived"}
    for key, value in encoding.get("derived", {}).items():
        sections[f"derived.{key}"] = value
    digests = {"encoding": digest(text.encode("utf-8"))}
    for name, value in sections.items():
        section = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        digests[name] = digest(section.encode("utf-8"))
    return digests


def encoding_digests(stage: ElaboratedStage) -> dict[str, str]:
    """The SHA-256 digests of the encoding of `stage`, by section: those
    that `digests_of_text` gives of the text that `record.py` stores for the
    encoding, `encoding_as_stored(stage)`."""
    return digests_of_text(encoding_as_stored(stage))


def recorded_digests(relative: str) -> dict[str, str]:
    """The digests that `encoding_digests.json` records for the stage file
    whose key is `relative`, or an empty mapping when the table or its entry
    is missing."""
    if not DIGESTS_FILE.is_file():
        return {}
    return json.loads(DIGESTS_FILE.read_text(encoding="utf-8"))["encodings"].get(relative, {})


def digest_message(relative: str, recorded: dict[str, str], live: dict[str, str]) -> str:
    """The failure message for the stage file `relative`, whose live digests
    `live` differ from its recorded digests `recorded`.

    The message names the stage file and the sections whose digests differ,
    in sorted order. It leaves out `encoding`, whose digest differs whenever
    that of a section does. When the section `package_version` differs, it
    says that the package's version changed. It then says how to read the
    differences of the two encodings, and ends with the command that records
    the digests again once the differences have been read. A stage file with
    no recorded digests gives a message that ends with the same command."""
    if not recorded:
        return (
            f"{relative}: {DIGESTS_FILE.name} records no digests of this stage file.\n"
            "After reading its encoding, run from packages/bellman the command "
            f"that records the digests: {RECORD_DIGESTS_COMMAND}"
        )
    differing = sorted(
        key
        for key in set(recorded) | set(live)
        if key != "encoding" and recorded.get(key) != live.get(key)
    )
    lines = [
        f"{relative}: the digests of these sections of the encoding differ from "
        f"{DIGESTS_FILE.name}: {', '.join(differing or ['encoding'])}."
    ]
    if "package_version" in differing:
        lines.append(
            "The package's version changed; the encoding records the version in "
            "the sections package_version and provenance."
        )
    lines.append(ENCODING_DIFFERENCE_INSTRUCTION)
    lines.append(
        "After reading the differences, run from packages/bellman the command "
        f"that records the digests again: {RECORD_DIGESTS_COMMAND}"
    )
    return "\n".join(lines)


def validate_encodings_and_record_digests() -> dict[str, object]:
    """Validate the live encoding of every stage file that the tests of the
    recordings elaborate against the schema. Then write the table of digests
    of those encodings to `encoding_digests.json`, and return that table. A
    file whose encoding the schema refuses raises the validator's error
    before the table is written."""
    from jsonschema import Draft202012Validator

    schema = schema_bytes()
    document = json.loads(schema)
    Draft202012Validator.check_schema(document)
    validator = Draft202012Validator(document)
    encodings = {}
    for src in ELABORATED_FILES:
        text = encoding_as_stored(stage_from_file(src))
        validator.validate(json.loads(text))
        encodings[digest_key(src)] = digests_of_text(text)
    table = {"schema_sha256": digest(schema), "encodings": encodings}
    text = json.dumps(table, indent=2, sort_keys=True) + "\n"
    DIGESTS_FILE.write_text(text, encoding="utf-8", newline="\n")
    return table


if __name__ == "__main__":
    table = validate_encodings_and_record_digests()
    print(f"Validated {len(table['encodings'])} live stage encodings; wrote {DIGESTS_FILE.name}")
