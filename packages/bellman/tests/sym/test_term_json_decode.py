"""The strict JSON decoder of generated Bellman-SYM terms (spec 0.3c, task S06;
decision D14).

`bellman.syntax.decode.from_json` inverts `bellman.syntax.lower.to_json`: a mapping
tagged "__class__" encodes a constructor of `bellman.syntax.terms` with one key
per ASDL field, a JSON array encodes a sequence slot element-wise, a primitive
encodes itself and null an absent slot; the root encodes a `terms.FILE`.

Three independent reference values are used, none of them the decoder's
own registry. The identity
`to_json(from_json(x)) == x`, which D14 states for the saved fixtures and whose
other half, `to_json`, the corpus test checks against the same fixtures; the
term `ToAst().transform(build_parser().parse(text))` of the matching `.bl`
source, compared by dataclass equality; and the text of `terms.py`, from which
the constructor and sort names are read by a regular expression. The failure
cases are hand-written encodings with one defect each; each asserts the
exception type and that the message names the JSON path of the defect.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
from dataclasses import fields, is_dataclass

import pytest
from snapshot.record import CORPUS_RECORDINGS, recording_path

from bellman.syntax import terms as T
from bellman.syntax.decode import TermDecodeError, from_json
from bellman.syntax.lower import ToAst, to_json
from bellman.syntax.parse import build_parser

from .test_corpus import CORPUS, KNOWN_UNPARSEABLE

REPO = pathlib.Path(__file__).resolve().parents[4]
APPLICATIONS = REPO / "applications"
# the stage folders of the portfolio model
PORTFOLIO = APPLICATIONS / "portfolio-choice" / "declaration" / "stages"
CANONICAL = tuple(recording_path(PORTFOLIO / name / f"{name}.bl", ".ast.json")
                  for name in ("cons", "disc", "port", "noport"))
# the recordings of the parsed terms of the other stage files of the corpus
OTHER = tuple(p for p in sorted(CORPUS_RECORDINGS.glob("*/*.ast.json")) if p not in CANONICAL)
FIXTURES = CANONICAL + OTHER
# the stage file of each recording of a parsed term
SOURCES = {recording_path(source, ".ast.json"): source for source in CORPUS}

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


# --- local helpers ----------------------------------------------------------


def source_of(fixture: pathlib.Path) -> pathlib.Path:
    """The `.bl` file whose parsed term the fixture records."""
    return SOURCES[fixture]


def encoded_nodes(value):
    """Every mapping inside a JSON value, depth first, the value itself first."""
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from encoded_nodes(v)
    elif isinstance(value, list):
        for v in value:
            yield from encoded_nodes(v)


def canonical_occurrences() -> dict:
    """Constructor name -> the distinct encoded nodes of that constructor in
    the four canonical fixtures (distinct by their JSON text)."""
    out = {}
    for path in CANONICAL:
        for node in encoded_nodes(json.loads(path.read_text(encoding="utf-8"))):
            key = json.dumps(node, sort_keys=True, ensure_ascii=False)
            out.setdefault(node["__class__"], {})[key] = node
    return {name: list(nodes.values()) for name, nodes in out.items()}


OCCURRENCES = canonical_occurrences()


def values_of(term):
    """Every value inside a decoded term, depth first: the term, each slot
    value, each child of a sequence slot."""
    yield term
    if is_dataclass(term):
        for f in fields(term):
            yield from values_of(getattr(term, f.name))
    elif isinstance(term, tuple):
        for x in term:
            yield from values_of(x)


def is_generated_term(value) -> bool:
    return (is_dataclass(value) and not isinstance(value, type)
            and type(value).__module__ == T.__name__
            and type(value).__name__ in CONSTRUCTORS_IN_SOURCE)


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


# --- the refusal type ---------------------------------------------------------

def test_error_type_is_a_value_error():
    assert issubclass(TermDecodeError, ValueError)
    with pytest.raises(ValueError):
        from_json([])


# --- (a) round trips over every constructor of the canonical fixtures --------

def test_round_trip_of_every_constructor_in_canonical_fixtures():
    for name in sorted(OCCURRENCES):
        for node in OCCURRENCES[name]:
            term = assert_round_trip(file_of(node))
            (item,) = term.items
            assert type(item) is getattr(T, name), name


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


def test_two_decodes_are_equal_and_distinct_objects():
    data = json.loads(CANONICAL[0].read_text(encoding="utf-8"))
    first, second = from_json(data), from_json(data)
    assert first == second
    assert first is not second
    assert first.items is not second.items
    assert first.items[0] is not second.items[0]


def test_key_order_is_not_significant():
    """JSON objects are unordered (RFC 8259 §4); the field set, not the key
    order, is checked. Assumption recorded for AAS in the S06 report."""
    assert from_json({"items": [], "__class__": "FILE"}) == T.FILE(())
    permuted = {"value": "cons", "__class__": "Metadata", "key": "stage"}
    assert from_json(file_of(permuted)) == T.FILE((T.Metadata("stage", "cons"),))


# --- (b) the saved fixtures ---------------------------------------------------

def test_every_fixture_round_trips_through_from_json():
    for fixture in FIXTURES:
        text = fixture.read_text(encoding="utf-8")
        assert to_json(from_json(json.loads(text))) == json.loads(text), fixture.name
        # the saved text itself is reproduced, in the format Stage.dumps writes
        assert json.dumps(to_json(from_json(json.loads(text))), indent=2,
                          ensure_ascii=False) + "\n" == text, fixture.name


def test_every_fixture_decodes_to_generated_terms_and_primitives_only():
    for fixture in FIXTURES:
        term = from_json(json.loads(fixture.read_text(encoding="utf-8")))
        assert type(term) is T.FILE, fixture.name
        nodes = 0
        for value in values_of(term):
            assert not isinstance(value, dict), (fixture.name, value)
            if is_generated_term(value):
                nodes += 1
            else:
                assert value is None or isinstance(value, (tuple, str, int, float)), (fixture.name, value)
        assert nodes > 1, fixture.name


def test_every_fixture_equals_the_fresh_parse_of_its_source():
    for fixture in FIXTURES:
        source = source_of(fixture)
        if source.stem in KNOWN_UNPARSEABLE:
            continue                  # recorded as unparseable by test_corpus
        fresh = ToAst().transform(build_parser().parse(source.read_text(encoding="utf-8")))
        decoded = from_json(json.loads(fixture.read_text(encoding="utf-8")))
        assert decoded == fresh, fixture.name


# --- (c) each defect raises TermDecodeError naming the path --------------------

def test_unknown_class_name():
    message = defect(file_of({"__class__": "Bogus", "x": 1}))
    assert "items[0]" in message and "'Bogus'" in message


def test_missing_class_key():
    statement = {"__class__": "Statement",
                 "core": {"lhs": {"__class__": "Number", "value": 1},
                          "rhs": {"__class__": "Number", "value": 1}},
                 "annot": None}
    message = defect(file_of(statement))
    assert "items[0].core" in message and "__class__" in message


def test_unknown_field():
    message = defect(file_of({**METADATA, "extra": 1}))
    assert "items[0]" in message and "'extra'" in message


def test_missing_required_field():
    message = defect(file_of({"__class__": "Metadata", "key": "stage"}))
    assert "items[0]" in message and "'value'" in message


def test_missing_optional_field_is_still_missing():
    """`Statement.annot` defaults to None in the dataclass; the encoding
    writes the slot explicitly, so its absence is a defect."""
    statement = {"__class__": "Statement",
                 "core": {"__class__": "Residual",
                          "form": {"__class__": "Number", "value": 0}}}
    message = defect(file_of(statement))
    assert "items[0]" in message and "'annot'" in message


def test_array_in_a_single_slot():
    message = defect(file_of({**METADATA, "key": ["stage"]}))
    assert "items[0].key" in message


def test_mapping_in_a_sequence_slot():
    message = defect({"__class__": "FILE", "items": METADATA})
    assert "items" in message
    block = {"__class__": "Block",
             "tag": {"__class__": "Annotation", "entries": []},
             "body": METADATA}
    message = defect(file_of(block))
    assert "items[0].body" in message


def test_null_in_a_sequence_slot():
    message = defect({"__class__": "FILE", "items": None})
    assert "items" in message


def test_array_as_an_element_of_a_sequence_slot():
    message = defect(file_of([METADATA]))
    assert "items[0]" in message


def test_non_json_value_in_a_slot():
    message = defect(file_of({**METADATA, "key": ("stage",)}))
    assert "items[0].key" in message


def test_non_file_root():
    message = defect(METADATA)
    assert "root" in message and "Metadata" in message and "FILE" in message


def test_a_root_that_is_not_a_mapping():
    for root in [[file_of()], [], "FILE", 3, 0.5, True, None]:
        assert "root" in defect(root), repr(root)


def test_root_mapping_without_class_key():
    message = defect({"items": []})
    assert "root" in message and "__class__" in message


def test_a_class_name_from_outside_terms():
    for name in ["PosixPath", "Tree", "Lark", "Token", "Transformer", "MappingProxyType", "dataclass", "field",
                 "dict", "list", "object", "str", "FILE.items", "bellman.syntax.terms.FILE", ""]:
        message = defect(file_of({"__class__": name}))
        assert "items[0]" in message and repr(name) in message, name


def test_a_sort_name_is_not_a_constructor():
    for name in SORTS_IN_SOURCE:
        message = defect(file_of({"__class__": name}))
        assert "items[0]" in message and repr(name) in message, name


def test_a_class_key_that_is_not_a_string():
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
