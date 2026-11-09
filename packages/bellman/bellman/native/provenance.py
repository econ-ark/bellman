"""The provenance of a stage version: the description of each source it was
elaborated or bound from, with the SHA-256 digest of what was loaded; the
record a binding verb adds, which holds the provenance before it as its
parent; the versions of the package and of its grammar files; and the source
file a version names in a refusal.
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from hashlib import sha256
from importlib import metadata, resources
from os import PathLike, fspath
from pathlib import Path

from bellman.native.frozen import freeze


def binding_provenance(stage, operation, source, loaded):
    """The provenance of the version a binding verb makes. `operation` is the
    verb, `methodize`, `configure` or `calibrate`; the record holds it, the
    description of the verb's source, the sources of every binding so far
    and the provenance of `stage` as its parent. The values bound are held in
    the bindings alone, and the provenance holds their digest only."""

    names = {"methodize": "methods", "configure": "settings", "calibrate": "calibration"}
    if operation not in names:
        raise ValueError(f"unknown lifecycle operation {operation!r}")
    supplied = source if isinstance(source, (str, PathLike)) else None
    description = source_description(loaded, supplied)
    sources = dict(stage.provenance.get("sources", {}))
    name = names[operation]
    # A source recorded before elaboration, where the verb is given a mapping
    # and no path, keeps its path or origin in the new description. The
    # methods of a version are no binding: the additions its provenance
    # records say whether methodize has read a selection into it.
    unbound = (
        "additions" not in stage.provenance
        if name == "methods"
        else getattr(stage.bindings, name) is None
    )
    if supplied is None and unbound and name in sources:
        previous = sources[name]
        location = {key: previous[key] for key in ("path", "origin") if key in previous}
        description = source_description(loaded, location)
    sources[name] = description
    return freeze(
        {
            **stage.provenance,
            "operation": operation,
            "parent": stage.provenance,
            "source": description,
            "sources": sources,
        }
    )


def source_description(loaded, supplied=None):
    """The description of a source: its path or its origin, and the SHA-256
    digest of the loaded mapping. A supplied description names a path or an
    origin, not both, and a digest it gives must equal the loaded mapping's."""
    if not isinstance(loaded, Mapping):
        raise TypeError("a binding source must be a mapping")
    encoded = json.dumps(_source_value(loaded), ensure_ascii=False, separators=(",", ":"))
    digest = sha256(encoded.encode("utf-8")).hexdigest()
    if supplied is None:
        supplied = {"origin": "in-memory"}
    elif isinstance(supplied, (str, PathLike)):
        supplied = {"path": fspath(supplied)}
    elif not isinstance(supplied, Mapping):
        raise TypeError("a source description must be a path or a mapping")
    unknown = set(supplied) - {"path", "origin", "sha256"}
    if unknown:
        raise ValueError(f"unknown source description fields: {sorted(unknown)!r}")
    if "sha256" in supplied and supplied["sha256"] != digest:
        raise ValueError("the supplied source hash disagrees with the loaded mapping")
    places = [key for key in ("path", "origin") if key in supplied]
    if len(places) > 1:
        raise ValueError("a source description has either a path or an origin")
    key = places[0] if places else "origin"
    location = supplied.get(key, "in-memory")
    if not isinstance(location, str) or not location:
        raise ValueError(f"a source {key} must be a nonempty string")
    return {key: location, "sha256": digest}


def _source_value(value):
    """The tagged form of a source value that the digest is computed from:
    each value tagged with its kind, a float and a bytes value in hexadecimal
    form, a mapping with its string keys sorted, a set with its items sorted.
    A value of another type is refused, and no conversion a value defines for
    itself is called."""
    if value is None:
        return ["none"]
    if type(value) in (str, bool, int):
        return [type(value).__name__, value]
    if type(value) is float:
        return ["float", value.hex()]
    if type(value) is bytes:
        return ["bytes", value.hex()]
    if isinstance(value, Mapping):
        # the keys of a source mapping are strings, written as they are and
        # sorted, or the numbers that key the entries of a collection,
        # `{0: 10, 2.5: 20}`, each written tagged with its kind and sorted by
        # value after the strings
        if not all(type(key) in (str, int, float) for key in value):
            raise TypeError("source mappings require string or numerical keys")
        strings = sorted(key for key in value if type(key) is str)
        numbers = sorted(key for key in value if type(key) is not str)
        return [
            "mapping",
            [[key, _source_value(value[key])] for key in strings]
            + [[_source_value(key), _source_value(value[key])] for key in numbers],
        ]
    if isinstance(value, (tuple, list)):
        return ["sequence", [_source_value(item) for item in value]]
    if isinstance(value, (set, frozenset)):
        items = [_source_value(item) for item in value]
        return ["set", sorted(items, key=lambda item: json.dumps(item, ensure_ascii=False))]
    raise TypeError(f"a {type(value).__name__} is not an admitted source value")


def grammar_versions():
    """The version of the package and the SHA-256 digest of each of its
    grammar files `stage.lark`, `stage.asdl` and `dynspec_full.asdl`."""
    grammar = resources.files("bellman.syntax").joinpath("grammars")
    return {
        "package": package_version(),
        "grammar": {
            name: sha256(grammar.joinpath(name).read_bytes()).hexdigest()
            for name in ("stage.lark", "stage.asdl", "dynspec_full.asdl")
        },
    }


def package_version():
    """The version of the package that derived a document: the `pyproject.toml`
    above the imported package where the package is imported from a checkout,
    and the installed distribution's metadata otherwise, so that a document
    derived from a checkout names the checkout's version. The provenance and
    the encoding both read this one rule."""
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if project.is_file():
        return tomllib.loads(project.read_text(encoding="utf-8"))["project"]["version"]
    return metadata.version("bellman")


def source_file(stage):
    """The source a stage version was elaborated from, its path or its origin,
    as its provenance records it. A refusal made after construction, which
    has no source position, names this source."""
    return stage.provenance.get("path") or stage.provenance.get("origin")
