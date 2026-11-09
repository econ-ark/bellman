"""The public JSON decoder's values and malformed-input diagnostics.

The complete corpus snapshot guard checks decoded terms against their parsed
sources and preserves every recorded JSON value. These checks cover inputs
that those valid recordings cannot supply, including every admitted constructor.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
from dataclasses import fields

import pytest
from bellman.syntax import terms as T
from bellman.syntax.decode import TermDecodeError, from_json
from bellman.syntax.lower import to_json
from conftest import ROOT
from snapshot.record import recording_path

CANONICAL = (recording_path(
    ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl", ".ast.json"),)

# The constructor and sort names of the generated module, read from its text:
# a constructor is a frozen dataclass with a base; a sort is a bare class with
# no base, carrying the empty slots that let its constructors be slotted.
TERMS_SOURCE = pathlib.Path(T.__file__).read_text(encoding="utf-8")
CONSTRUCTORS_IN_SOURCE = tuple(re.findall(
    r"^@dataclass\(frozen=True, slots=True\)\nclass (\w+)\(\w+\):",
    TERMS_SOURCE, flags=re.MULTILINE))
SORTS_IN_SOURCE = tuple(re.findall(
    r"^class (\w+):\n    __slots__ = \(\)$", TERMS_SOURCE, flags=re.MULTILINE))

# A valid encoded item and the FILE encoding around a list of items.
METADATA = {"__class__": "Metadata", "key": "stage", "value": "cons"}


def file_of(*items):
    return {"__class__": "FILE", "items": list(items)}


def assert_round_trip(data) -> T.FILE:
    """Decode `data`, require `to_json` to give `data` back, and require the
    input to be unchanged; the decoded FILE is returned."""
    before = copy.deepcopy(data)
    term = from_json(data)
    assert isinstance(term, T.FILE)
    assert to_json(term) == before
    assert data == before
    return term


def defect(data) -> str:
    """The message of the TermDecodeError that `from_json` raises for `data`;
    the test fails when nothing is raised."""
    with pytest.raises(TermDecodeError) as caught:
        from_json(data)
    return str(caught.value)


def test_round_trip_of_empty_file():
    assert assert_round_trip(file_of()) == T.FILE(())


# The optional slots of the ASDL (`?`), each hand-encoded with null and
# compared with the dataclass built the way ToAst builds it.
OPTIONAL_SLOT_CASES = {
    "Statement.annot": (
        {"__class__": "Statement",
         "core": {"__class__": "Residual",
                  "form": {"__class__": "Number", "value": 0}},
         "annot": None},
        T.Statement(T.Residual(T.Number(0)), None)),
    "PathAssignment.bound": (
        {"__class__": "PathAssignment",
         "target": {"__class__": "Variable", "name": "k",
                    "when": {"__class__": "T"}, "shift": 1},
         "bound": None,
         "value": {"__class__": "Number", "value": 2}},
        T.PathAssignment(T.Variable("k", T.T(), 1), None, T.Number(2))),
    "Range.left and Range.right": (
        {"__class__": "Range", "left": None,
         "lower": {"__class__": "Number", "value": 0},
         "upper": {"__class__": "Number", "value": 1},
         "right": None},
        T.Range(None, T.Number(0), T.Number(1), None)),
    "Declaration.value": (
        {"__class__": "Declaration",
         "subject": {"__class__": "Subject", "coordinates": []},
         "classifiers": [], "value": None},
        T.Declaration(T.Subject(()), (), None)),
    "Coordinate.at": (
        {"__class__": "Coordinate", "stem": "c", "at": None,
         "classifiers": []},
        T.Coordinate("c", None, ())),
    "Comprehension.base": (
        {"__class__": "Comprehension",
         "bound": {"__class__": "Subject", "coordinates": []},
         "base": None, "conds": []},
        T.Comprehension(T.Subject(()), None, ())),
}


def test_round_trip_of_every_hand_encoded_optional_slot():
    for slot, (encoded, expected) in sorted(OPTIONAL_SLOT_CASES.items()):
        (item,) = assert_round_trip(file_of(encoded)).items
        assert item == expected, slot


def test_every_generated_constructor_decodes():
    """An instance with empty sequence slots and a string in every other
    slot: the decoder checks slot categories, not sorts, so this encoding
    must decode for each of the constructors the source text lists."""
    for name in CONSTRUCTORS_IN_SOURCE:
        cls = getattr(T, name)
        instance = cls(**{f.name: () if f.type is tuple else f"<{f.name}>"
                          for f in fields(cls)})
        (item,) = assert_round_trip(file_of(to_json(instance))).items
        assert item == instance and type(item) is cls, name


def test_primitive_slot_values_pass_through_unchanged():
    for value in ["x", "𝑢", "", 3, -7, 0.5, True, False]:
        (item,) = assert_round_trip(file_of({"__class__": "Number", "value": value})).items
        assert (item.value is value or item.value == value) and type(item.value) is type(value), repr(value)


def test_key_order_is_not_significant():
    """JSON objects are unordered (RFC 8259 §4); the field set, not the key
    order, is checked. Assumption recorded for AAS in the S06 report."""
    assert from_json({"items": [], "__class__": "FILE"}) == T.FILE(())
    permuted = {"value": "cons", "__class__": "Metadata", "key": "stage"}
    assert from_json(file_of(permuted)) == T.FILE((T.Metadata("stage", "cons"),))


def test_constructor_names_admit_generated_constructors_only():
    outside = ["Bogus", "PosixPath", "Tree", "Lark", "Token", "Transformer", "MappingProxyType",
               "dataclass", "field", "dict", "list", "object", "str", "FILE.items",
               "bellman.syntax.terms.FILE", ""]
    for name in [*outside, *SORTS_IN_SOURCE]:
        encoded = {"__class__": name, **({"x": 1} if name == "Bogus" else {})}
        message = defect(file_of(encoded))
        assert "items[0]" in message and repr(name) in message, name


def test_each_constructor_requires_its_exact_field_set():
    cases = {
        "unknown field": (file_of({**METADATA, "extra": 1}), "items[0]", "'extra'"),
        "missing required field": (file_of({"__class__": "Metadata", "key": "stage"}),
                                   "items[0]", "'value'"),
        "missing optional field": (file_of({"__class__": "Statement", "core": {
            "__class__": "Residual", "form": {"__class__": "Number", "value": 0}}}),
            "items[0]", "'annot'"),
        "nested class missing": (file_of({"__class__": "Statement", "core": {
            "lhs": {"__class__": "Number", "value": 1},
            "rhs": {"__class__": "Number", "value": 1}}, "annot": None}),
            "items[0].core", "__class__"),
    }
    for name, (data, path, detail) in cases.items():
        message = defect(data)
        assert path in message and detail in message, name


def test_slot_categories_refuse_malformed_values_at_their_path():
    cases = {
        "array in single slot": (file_of({**METADATA, "key": ["stage"]}), "items[0].key"),
        "mapping in root sequence": ({"__class__": "FILE", "items": METADATA}, "items"),
        "mapping in nested sequence": (file_of({"__class__": "Block", "tag": {
            "__class__": "Annotation", "entries": []}, "body": METADATA}), "items[0].body"),
        "null in sequence": ({"__class__": "FILE", "items": None}, "items"),
        "array sequence element": (file_of([METADATA]), "items[0]"),
        "non-JSON single value": (file_of({**METADATA, "key": ("stage",)}), "items[0].key"),
    }
    for name, (data, path) in cases.items():
        assert path in defect(data), name


def test_root_must_encode_a_file_mapping():
    assert issubclass(TermDecodeError, ValueError)
    with pytest.raises(ValueError):
        from_json([])
    for root in [[file_of()], [], "FILE", 3, 0.5, True, None]:
        assert "root" in defect(root), repr(root)
    message = defect(METADATA)
    assert "root" in message and "Metadata" in message and "FILE" in message
    message = defect({"items": []})
    assert "root" in message and "__class__" in message


def test_class_names_must_be_strings_at_root_and_nested_positions():
    for value in [3, None, True, 0.5, ["FILE"], file_of()]:
        assert "items[0]" in defect(file_of({"__class__": value})), repr(value)
        assert "root" in defect({"__class__": value, "items": []}), repr(value)


def test_path_of_a_defect_deep_in_a_saved_fixture():
    data = json.loads(CANONICAL[0].read_text(encoding="utf-8"))
    k = next(i for i, item in enumerate(data["items"])
             if item["__class__"] == "Declare")
    data["items"][k]["declaration"]["subject"] = []
    assert f"items[{k}].declaration.subject" in defect(data)

    data = json.loads(CANONICAL[0].read_text(encoding="utf-8"))
    b = next(i for i, item in enumerate(data["items"])
             if item["__class__"] == "Block")
    j = next(i for i, item in enumerate(data["items"][b]["body"])
             if item["__class__"] == "Statement")
    data["items"][b]["body"][j]["core"]["__class__"] = "Equatoin"
    message = defect(data)
    assert f"items[{b}].body[{j}].core" in message and "'Equatoin'" in message
