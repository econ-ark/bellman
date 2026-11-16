"""The encoding of a stage, `stage.encoding()`: the JSON-compatible mapping
of one version, the one schema that describes it, the check of an encoding
read as plain JSON, and the encoding of the answers of a stage's operations."""

import functools
import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest
from application_files import CONS_CALIBRATION, CORPUS, FIRST_CALIBRATIONS, stage_file_id
from snapshot.record import ELABORATED_FILES
from stage_builders import name_term, stage_from_file, stage_from_text
from stage_texts import SMALL_CONS, SMALL_CONS_METHODS
from two_sets import one_row_by_default

from bellman.display import cards, encoding_checks
from bellman.display.answer_encoding import KINDS, encode_answer
from bellman.display.encoding_checks import operators, validate_encoding
from bellman.native.records import ExpressionType, ResolvedName
from bellman.stage import elaborate_stage
from bellman.syntax import layout, terms
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.typing import typed_expressions

# Strict JSON: `json.dumps(..., allow_nan=False)` writes the encoding, which
# then holds no infinity and no NaN as a number, and the text read back is
# the same mapping, as the printed encoding read back is.

# The reserved key `$bellman`: the encoding writes a nonfinite float that an
# author gives, in a binding or in the provenance, as `{"$bellman": ["float",
# "inf"]}`, and a mapping of the author that holds the reserved key itself as
# `{"$bellman": ["mapping", ...]}`.

# A document reference, `{"ref": "document", "id": ...}`, names an entry of
# the stage, such as a declaration, whose fields stand once beside the answer
# that refers to it.

# A bound reference, `{"ref": "bound", "depth": ..., "position": ...}`, names
# a variable that a function or an operator binds: the depth is the number of
# scopes between the reference and that binding, and the position is the
# place of the variable among those that the binding introduces.

# `validate_encoding` of `bellman.display.encoding_checks` checks an encoding
# read as plain JSON against the schema and against the rules that the
# schema cannot state, and `operators` lists the row of each operation of an
# encoding; the module imports nothing of the package.


# the three spellings of a nonfinite float in the encoding
NONFINITE = ("inf", "-inf", "nan")


# the block of a stage of one backward block, whose one line reads the
# continuation value
ONE_BACKWARD_BLOCK = """[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}
"""


# a stage of one backward block, whose encoding holds a box, a wire type, a
# function that binds a variable, a reference to that variable and a
# document reference
ONE_BACKWARD = "@stage: one_backward\n" + ONE_BACKWARD_BLOCK


# the same block with one parameter declared in a union of two intervals and
# one declared as the positive reals without the point 1
UNION_AND_DIFFERENCE = (
    "@stage: one_backward\nρ : (0,1) \\/ (1, inf)\nσ : ℝ₊₊ \\ {1}\n" + ONE_BACKWARD_BLOCK
)


# a stage of one backward block whose continuation value has the set alias
# Xv as its type
ALIASED = """@stage: aliased
Xv := ℝ
[id=cntn_to_dcsn, (V[>] : Xv @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}
"""


# a stage whose policy writes its first-order condition with a clause
CLAUSE = """@stage: clause
[id=dcsn_to_cntn, (m_d : ℝ₊₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m_d - c
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    1/c = D_{a}V[>] ⟂ m_d - c >= 0 :: [id=euler]
}
"""


# the settings that `SMALL_CONS_METHODS` declares, which its grid names
SMALL_CONS_SETTINGS = {"n_m": 8, "m_min": 0.1, "m_max": 10.0}


# the methods of the small stage with the program of a handler: a linear
# representation on a grid of m_d at the Evaluation of the builder
# `cntn_to_dcsn`, the program `test:interpolate` of its handler, and the three
# settings that the grid names
HANDLER_METHODS = {
    "text": (
        "@methods: cons\n"
        "n_points : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
        "cntn_to_dcsn.evaluate.method : !Linear\n"
        'cntn_to_dcsn.evaluate.handler : "test:interpolate"\n'
        "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_points))\n"
    ),
    "origin": "cons.methods.bl",
}


# the versions that the three tables of the encoding of a version read, each
# a fixture of the session: five symbolic stages of the applications, then
# the consumption stage calibrated, calibrated and methodized, calibrated,
# methodized and configured, and methodized alone
VERSIONS = (
    "cons",
    "port",
    "ez_savings",
    "cons_savings_iid",
    "sa_savings",
    "cons_calibrated",
    "cons_methodized",
    "cons_configured",
    "cons_methodized_without_calibration",
)


def calibrated_at(value, domain):
    """The stage of one forward block whose parameter `r` is declared in
    `domain`, calibrated at `r = value`."""
    text = (
        f"@stage: parameters\nr : {domain}\n"
        "[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n"
    )
    return stage_from_text(text).calibrate({"r": value})


def with_provenance(value):
    """The stage of `ONE_BACKWARD` elaborated from a record whose provenance
    holds `value` under the key `review_value`."""
    return elaborate_stage(
        {
            "stage": {"text": ONE_BACKWARD, "origin": "one_backward.bl"},
            "calibration": {},
            "settings": {},
            "methods": [],
            "provenance": {"review_value": value},
        }
    )


def authored_values(spelling):
    """The four values that an author writes for one spelling of a nonfinite
    float, by name: the float, its spelling as a string, the float in the
    form of the reserved key, and a mapping that holds the three in a list
    and the second form of the reserved key under that key."""
    tag = {"$bellman": ["float", spelling]}
    escaped = {"$bellman": ["mapping", [["$bellman", ["float", spelling]]]]}
    return {
        "float": float(spelling),
        "string": spelling,
        "tag": tag,
        "nested": {"plain": [float(spelling), spelling, tag], "$bellman": escaped},
    }


def small_stage_with_a_handler_and_settings(settings):
    """A stage of `SMALL_CONS` of its own, methodized with `HANDLER_METHODS`
    and configured with `settings`."""
    return stage_from_text(SMALL_CONS, "cons.bl").methodize(HANDLER_METHODS).configure(settings)


def nonfinite_settings(spelling):
    """The three settings of `HANDLER_METHODS` beside the nonfinite setting
    `n_m` and the setting `extra`, a mapping that holds the reserved key."""
    return {
        "n_points": 8,
        "m_min": 0.1,
        "m_max": 10.0,
        "n_m": float(spelling),
        "extra": {"$bellman": ["float", spelling]},
    }


def box_named(encoding, name):
    """The box called `name` of the backward builders graph of `encoding`."""
    return next(box for box in encoding["builders"]["backward"]["boxes"] if box["name"] == name)


def mappings_within(value):
    """Each mapping within the JSON value `value`, `value` itself first, in
    the order of a walk that reads each mapping before what it holds."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from mappings_within(child)
    elif isinstance(value, list):
        for child in value:
            yield from mappings_within(child)


def first_mapping(encoding, **entries):
    """The first mapping of the answers of `encoding`, its section `derived`,
    that holds each of `entries`."""
    return next(
        mapping
        for mapping in mappings_within(encoding["derived"])
        if all(mapping.get(key) == item for key, item in entries.items())
    )


def mathematical_content(value):
    """The encoded answer `value` without the keys `method` and `methods` of
    its mappings, each part that pairs a value with its identities keeping
    only the identities that the value reaches by document references."""
    if isinstance(value, list):
        return [mathematical_content(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {"identities", "value"}:
            part = mathematical_content(value["value"])
            table = {row["id"]: row for row in value["identities"]}
            reached = {
                node["id"] for node in mappings_within(part) if node.get("ref") == "document"
            }
            pending = list(reached)
            while pending:
                for node in mappings_within(table[pending.pop()]):
                    if node.get("ref") == "document" and node["id"] not in reached:
                        reached.add(node["id"])
                        pending.append(node["id"])
            return {"value": part, "identities": [table[name] for name in sorted(reached)]}
        return {
            key: mathematical_content(item)
            for key, item in value.items()
            if key not in ("method", "methods")
        }
    return value


def real_state(name):
    """The resolved name of a real-valued state called `name`, at no perch."""
    real = ExpressionType(kind="scalar", domain="primitive:real")
    return ResolvedName(name, value_type=real, role="state", perch=None)


def nested_function(first, second, returned):
    """The function of the real state `first` whose value is the function of
    the real state `second` that returns the symbol `returned`."""
    inner = typed_expressions.Lambda(
        bindings=((real_state(second), terms.Named("ℝ")),), body=name_term(returned)
    )
    return typed_expressions.Lambda(bindings=((real_state(first), terms.Named("ℝ")),), body=inner)


def quantified(head, name):
    """The operator `head`, `forall` or `exists`, over the real state `name`
    in ℝ, of the symbol `name`."""
    return terms.Operator(
        head, subs=(terms.In(real_state(name), terms.Named("ℝ")),), args=(name_term(name),)
    )


def joint_argmax(first, second):
    """The argmax over `first` in C and over `second` in the reals at most
    `first`, of the sum of the two."""
    at_most_first = terms.Comprehension(
        bound="x",
        base=terms.Named("ℝ"),
        conds=(terms.Rel(name_term("x"), terms.Le(), name_term(first)),),
    )
    return terms.Operator(
        "argmax",
        subs=(terms.In(first, terms.Named("C")), terms.In(second, at_most_first)),
        args=(terms.Add(name_term(first), name_term(second)),),
    )


def selection(head):
    """The operator `head` whose one subscript selects the name `x`, of the
    symbol `f`."""
    return terms.Operator(head, subs=(terms.Var("x"),), args=(name_term("f"),))


def differing_sections(encoding, other):
    """The name of each section whose content differs between the encodings
    `encoding` and `other`, in sorted order."""
    sections = sorted(encoding.keys() | other.keys())
    return [section for section in sections if encoding.get(section) != other.get(section)]


@pytest.fixture(scope="module")
def schema():
    """The one schema of the encoding, the file
    `stage-encoding-2.6.schema.json` of `bellman.display`, as a mapping."""
    path = files("bellman.display").joinpath("stage-encoding-2.6.schema.json")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def term_constructors():
    """The constructors of the terms: each dataclass that
    `bellman.syntax.terms` defines."""
    return [
        value
        for value in vars(terms).values()
        if isinstance(value, type) and is_dataclass(value) and value.__module__ == terms.__name__
    ]


@pytest.fixture(scope="module")
def small_stage():
    """The small stage `SMALL_CONS`, of one forward block, `a = m_d`, and one
    backward block, `V = V[>]/(1-ρ)`, symbolic."""
    return stage_from_text(SMALL_CONS, "cons.bl")


@pytest.fixture(scope="module")
def small_stage_calibrated():
    """The small stage calibrated at ρ = 6."""
    return stage_from_text(SMALL_CONS, "cons.bl").calibrate(FIRST_CALIBRATIONS["cons"])


@pytest.fixture(scope="module")
def small_stage_methodized_alone():
    """The small stage methodized with `SMALL_CONS_METHODS` alone."""
    return stage_from_text(SMALL_CONS, "cons.bl").methodize(SMALL_CONS_METHODS)


@pytest.fixture(scope="module")
def small_stage_configured():
    """The small stage calibrated at ρ = 6, methodized with
    `SMALL_CONS_METHODS` and configured with `SMALL_CONS_SETTINGS`."""
    calibrated = stage_from_text(SMALL_CONS, "cons.bl").calibrate(FIRST_CALIBRATIONS["cons"])
    return calibrated.methodize(SMALL_CONS_METHODS).configure(SMALL_CONS_SETTINGS)


@pytest.fixture(scope="module")
def small_stage_with_a_handler_and_an_infinite_setting():
    """The small stage methodized with `HANDLER_METHODS` and configured with
    the three settings that the methods file declares, the infinite setting
    `n_m` and the setting `extra`, a mapping that holds the reserved key."""
    return small_stage_with_a_handler_and_settings(nonfinite_settings("inf"))


@pytest.fixture(scope="module")
def stage_with_provenance():
    """`stage_with_provenance(written, spelling)`: the stage of `ONE_BACKWARD`
    whose provenance holds the value called `written` of
    `authored_values(spelling)`, elaborated once for the module."""
    return functools.cache(
        lambda written, spelling: with_provenance(authored_values(spelling)[written])
    )


@pytest.fixture(scope="module")
def one_backward_encoding():
    """The encoding of `ONE_BACKWARD`, which each test copies before it
    changes it."""
    return stage_from_text(ONE_BACKWARD, "one_backward.bl").encoding()


@pytest.fixture(scope="module")
def aliased_stage():
    """The stage of `ALIASED`."""
    return stage_from_text(ALIASED, "aliased.bl")


@pytest.fixture(scope="module")
def clause_stage():
    """The stage of `CLAUSE`."""
    return stage_from_text(CLAUSE, "clause.bl")


@pytest.fixture(scope="module")
def union_and_difference_stage():
    """The stage of `UNION_AND_DIFFERENCE`."""
    return stage_from_text(UNION_AND_DIFFERENCE, "one_backward.bl")


# --- the encoding of a version: strict JSON, its printed form, its version ---


@pytest.mark.parametrize(
    "name",
    one_row_by_default(VERSIONS)
    + [
        pytest.param("small_stage_configured"),
        pytest.param("clause_stage", id="a-policy-with-a-clause"),
    ],
)
def test_the_encoding_of_each_version_is_a_strict_json_document_of_the_schema(
    name, request, encoding_validator
):
    """The encoding of each version reads back unchanged from strict JSON, as
    a document that the schema admits."""
    encoding = request.getfixturevalue(name).encoding()
    assert (
        json.loads(json.dumps(encoding, allow_nan=False)) == json.loads(str(encoding)) == encoding
    )
    encoding_validator.validate(encoding)


@pytest.mark.parametrize("name", one_row_by_default(VERSIONS))
def test_the_encoding_prints_as_strict_json_indented_with_sorted_keys(name, request):
    """The encoding of each version prints, and is represented, as strict
    JSON indented by two spaces, with sorted keys and with characters such as
    ρ written as they are."""
    encoding = request.getfixturevalue(name).encoding()
    assert repr(encoding) == str(encoding)
    assert str(encoding) == json.dumps(
        encoding, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False
    )


@pytest.mark.parametrize("name", one_row_by_default(VERSIONS))
def test_each_call_of_encoding_answers_a_new_mapping_that_no_earlier_answer_shares(name, request):
    """Each call of `encoding()` answers a new mapping equal to the last,
    which a change of an earlier answer does not reach."""
    stage = request.getfixturevalue(name)
    answer = stage.encoding()
    again = stage.encoding()
    assert again == answer and again is not answer
    answer["definitions"].clear()
    assert stage.encoding() == again


@pytest.mark.parametrize(
    "name,word",
    [
        pytest.param("small_stage_methodized_alone", "methods", id="methodized-alone"),
        pytest.param("small_stage_configured", "specified", id="calibrated-methodized-configured"),
    ],
)
def test_the_encoding_names_the_version_of_its_stage(name, word, request):
    """The encoding of a bound version of the small stage names the version
    by the word for the bindings that it holds."""
    assert request.getfixturevalue(name).encoding()["version"] == word


def test_the_builders_box_in_a_methodized_version_holds_the_method_and_grid_of_its_evaluation(
    small_stage_methodized_alone,
):
    """The box of the builder `cntn_to_dcsn` of the methodized small stage
    holds the method `Linear` and the grid on m_d, typed at its Evaluation."""
    components = box_named(small_stage_methodized_alone.encoding(), "cntn_to_dcsn")["methods"][0]
    assert (components["at"], components["method"]["name"]) == ("cntn_to_dcsn.evaluate", "Linear")
    assert [factor["coordinate"] for factor in components["grid"]["factors"]] == ["m_d"]


def test_the_encoding_of_a_configured_version_writes_the_settings_bound_on_it(
    small_stage_configured,
):
    """The section `bindings` of the encoding of the configured small stage
    holds the settings that the version binds."""
    assert set(small_stage_configured.bindings.settings) == {"n_m", "m_min", "m_max"}
    encoding = small_stage_configured.encoding()
    assert encoding["bindings"]["settings"] == dict(small_stage_configured.bindings.settings)


# --- the values that an author writes: nonfinite floats, the reserved key ---


@pytest.mark.parametrize(
    "value,domain,spelling",
    [
        pytest.param(float("inf"), "[0, inf]", "inf", id="inf"),
        pytest.param(float("-inf"), "[-inf, 0]", "-inf", id="minus-inf"),
    ],
)
def test_the_encoding_writes_an_infinity_that_a_calibration_binds_with_the_reserved_key(
    value, domain, spelling
):
    """The encoding of a stage calibrated at an infinity that the parameter's
    declared domain admits writes the value in the form of the reserved
    key."""
    stage = calibrated_at(value, domain)
    assert stage.bindings.calibration["r"] == value
    assert stage.encoding()["bindings"]["calibration"]["r"] == {"$bellman": ["float", spelling]}


@pytest.mark.parametrize(
    "value,domain",
    [
        pytest.param(float("inf"), "[0, inf]", id="inf"),
        pytest.param(float("-inf"), "[-inf, 0]", id="minus-inf"),
    ],
)
def test_a_stage_calibrated_at_an_infinity_encodes_to_strict_json_of_the_schema(
    value, domain, encoding_validator
):
    """The encoding of a stage calibrated at an infinity reads back unchanged
    from strict JSON, as a document that the schema admits."""
    encoding = calibrated_at(value, domain).encoding()
    assert "r" in encoding["bindings"]["calibration"]
    assert (
        json.loads(json.dumps(encoding, allow_nan=False)) == json.loads(str(encoding)) == encoding
    )
    encoding_validator.validate(encoding)


# the four values of `authored_values`, by name
AUTHORED = (
    pytest.param("float", id="the-float"),
    pytest.param("string", id="its-spelling-as-a-string"),
    pytest.param("tag", id="the-float-in-the-form-of-the-reserved-key"),
    pytest.param("nested", id="a-mapping-of-the-three-and-the-reserved-key"),
)


@pytest.mark.parametrize("spelling", NONFINITE)
@pytest.mark.parametrize("written", AUTHORED)
def test_the_encoding_writes_each_authored_value_of_the_provenance_in_its_own_form(
    written, spelling, stage_with_provenance
):
    """The encoding writes a nonfinite float of the provenance in the form of
    the reserved key, its spelling as the same string, and a mapping that
    holds the reserved key in the second form of that key."""
    tag = {"$bellman": ["float", spelling]}
    escaped = {"$bellman": ["mapping", [["$bellman", ["float", spelling]]]]}
    escaped_again = {"$bellman": ["mapping", [["$bellman", escaped["$bellman"]]]]}
    expected = {
        "float": tag,
        "string": spelling,
        "tag": escaped,
        "nested": {
            "$bellman": [
                "mapping",
                [["plain", [tag, spelling, escaped]], ["$bellman", escaped_again]],
            ]
        },
    }[written]
    encoding = stage_with_provenance(written, spelling).encoding()
    assert encoding["provenance"]["review_value"] == expected


@pytest.mark.parametrize("spelling", NONFINITE)
@pytest.mark.parametrize("written", AUTHORED)
def test_a_stage_with_an_authored_provenance_value_encodes_to_strict_json_of_the_schema(
    written, spelling, stage_with_provenance, encoding_validator
):
    """The encoding of a stage whose provenance holds an authored value reads
    back unchanged from strict JSON, as a document that the schema admits."""
    encoding = stage_with_provenance(written, spelling).encoding()
    assert "review_value" in encoding["provenance"]
    strict = json.dumps(encoding, allow_nan=False, sort_keys=True)
    assert json.loads(strict) == json.loads(str(encoding)) == encoding
    encoding_validator.validate(encoding)


@pytest.mark.parametrize("spelling", NONFINITE)
def test_the_four_authored_values_of_one_spelling_give_four_different_encodings(
    spelling, stage_with_provenance
):
    """The float, its spelling, its form in the reserved key and the mapping
    of the three give the provenance four encodings that differ as strict
    JSON texts."""
    texts = [
        json.dumps(
            stage_with_provenance(written, spelling).encoding(), allow_nan=False, sort_keys=True
        )
        for written in authored_values(spelling)
    ]
    assert len(set(texts)) == len(texts)


@pytest.mark.parametrize("spelling", NONFINITE)
def test_the_encoding_writes_a_nonfinite_setting_and_a_mapping_setting_with_the_reserved_key(
    spelling,
):
    """The encoding of a configured version writes the nonfinite setting
    `n_m` and the setting `extra`, which holds the reserved key, in the forms
    of that key, and the finite settings as they are."""
    encoding = small_stage_with_a_handler_and_settings(nonfinite_settings(spelling)).encoding()
    assert encoding["bindings"]["settings"] == {
        "n_points": 8,
        "m_min": 0.1,
        "m_max": 10.0,
        "n_m": {"$bellman": ["float", spelling]},
        "extra": {"$bellman": ["mapping", [["$bellman", ["float", spelling]]]]},
    }


@pytest.mark.parametrize("spelling", NONFINITE)
def test_a_version_configured_with_a_nonfinite_setting_encodes_to_strict_json_of_the_schema(
    spelling, encoding_validator
):
    """The encoding of a version configured with a nonfinite setting reads
    back unchanged from strict JSON, as a document that the schema admits."""
    encoding = small_stage_with_a_handler_and_settings(nonfinite_settings(spelling)).encoding()
    assert "n_m" in encoding["bindings"]["settings"]
    assert (
        json.loads(json.dumps(encoding, allow_nan=False)) == json.loads(str(encoding)) == encoding
    )
    encoding_validator.validate(encoding)


def test_the_encoding_writes_the_components_typed_at_a_place_under_its_bindings(
    small_stage_with_a_handler_and_an_infinite_setting,
):
    """The section `bindings` of the encoding of a version configured with an
    infinite setting writes the components typed at the Evaluation of
    `cntn_to_dcsn`: the method word and the grid as terms, and the program of
    the handler."""
    encoding = small_stage_with_a_handler_and_an_infinite_setting.encoding()
    components = encoding["bindings"]["methods"]["cntn_to_dcsn.evaluate"]
    assert components["method"] == {"__class__": "Word", "name": "Linear", "arguments": []}
    assert components["grid"]["__class__"] == "Cartesian"
    assert [factor["coordinate"] for factor in components["grid"]["factors"]] == ["m_d"]
    assert components["handler"] == "test:interpolate"


def test_the_box_of_a_builder_holds_the_components_that_the_bindings_write_at_its_place(
    small_stage_with_a_handler_and_an_infinite_setting,
):
    """The box of `cntn_to_dcsn` in the encoding of a version configured with
    an infinite setting holds, with their place, the components that the
    section `bindings` writes at its Evaluation."""
    encoding = small_stage_with_a_handler_and_an_infinite_setting.encoding()
    components = encoding["bindings"]["methods"]["cntn_to_dcsn.evaluate"]
    assert box_named(encoding, "cntn_to_dcsn")["methods"] == [
        {"at": "cntn_to_dcsn.evaluate", **components}
    ]


# --- the refusals of the schema ---


def unchanged(encoding):
    """No change: the encoding as the package writes it."""


def with_a_list_of_methods_on_a_box(encoding):
    """The first box of the backward builders graph given an empty list of
    methods."""
    encoding["builders"]["backward"]["boxes"][0]["methods"] = []


def without_the_list_of_methods_of_a_box(encoding):
    """The first box of the backward builders graph without its list of
    methods."""
    del encoding["builders"]["backward"]["boxes"][0]["methods"]


def with_the_source_text_of_the_parent(encoding):
    """The provenance of the parent version given its source text."""
    encoding["provenance"]["parent"]["text"] = "source text"


def with_the_reserved_key_in_a_method_entry(encoding):
    """The first method entry of the box of `cntn_to_dcsn` given the reserved
    key."""
    box_named(encoding, "cntn_to_dcsn")["methods"][0]["$bellman"] = ["float", "inf"]


def with_an_unknown_key_at(path):
    """The change that adds the key `unknown`, which the schema does not
    name, at the place `path` of an encoding."""

    def change(encoding):
        place = encoding
        for key in path:
            place = place[key]
        place["unknown"] = None

    return change


# each version of the small stage as the package writes it, which the schema
# admits, and then the same version after one change, which it refuses: the
# fixture of the version, the change and whether the schema admits the result
SCHEMA_CHANGES = [
    pytest.param("small_stage", unchanged, True, id="symbolic"),
    pytest.param(
        "small_stage",
        with_a_list_of_methods_on_a_box,
        False,
        id="symbolic-with-a-list-of-methods-on-a-box",
    ),
    pytest.param(
        "small_stage", with_an_unknown_key_at(()), False, id="symbolic-with-an-unknown-key"
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("definitions", 0)),
        False,
        id="symbolic-with-an-unknown-key-in-a-definition",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("definitions", 0, "equations", 0)),
        False,
        id="symbolic-with-an-unknown-key-in-an-equation-of-a-definition",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("builders", "backward", "boxes", 0)),
        False,
        id="symbolic-with-an-unknown-key-in-a-box",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("builders", "backward", "wires", 0)),
        False,
        id="symbolic-with-an-unknown-key-in-a-wire",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("bindings",)),
        False,
        id="symbolic-with-an-unknown-key-in-the-bindings",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("obligations", 0)),
        False,
        id="symbolic-with-an-unknown-key-in-a-condition",
    ),
    pytest.param(
        "small_stage",
        with_an_unknown_key_at(("diagnostics",)),
        False,
        id="symbolic-with-an-unknown-key-in-the-diagnostics",
    ),
    pytest.param("small_stage_configured", unchanged, True, id="configured"),
    pytest.param(
        "small_stage_configured",
        without_the_list_of_methods_of_a_box,
        False,
        id="configured-with-a-box-without-its-list-of-methods",
    ),
    pytest.param(
        "small_stage_configured",
        with_the_source_text_of_the_parent,
        False,
        id="configured-with-the-source-text-of-its-parent",
    ),
    pytest.param(
        "small_stage_with_a_handler_and_an_infinite_setting",
        unchanged,
        True,
        id="with-a-handler-and-an-infinite-setting",
    ),
    pytest.param(
        "small_stage_with_a_handler_and_an_infinite_setting",
        with_the_reserved_key_in_a_method_entry,
        False,
        id="with-a-handler-and-an-infinite-setting-and-the-reserved-key-in-a-method-entry",
    ),
]


@pytest.mark.parametrize("name,change,admitted", SCHEMA_CHANGES)
def test_the_schema_admits_an_encoding_as_written_and_refuses_it_after_one_change(
    name, change, admitted, request, encoding_validator
):
    """The schema admits the encoding of each version of the small stage as
    the package writes it, and refuses it after one change that breaks a rule
    of the schema."""
    encoding = request.getfixturevalue(name).encoding()
    change(encoding)
    assert encoding_validator.is_valid(encoding) is admitted


# --- the kinds of the terms ---


def test_the_encoding_writes_each_constructor_of_the_terms_under_its_own_kind(
    term_constructors,
):
    """`KINDS`, the table of the kind under which the encoding writes each
    class, holds `terms.<name>` for each constructor of the terms."""
    # a guard that the constructors of the terms were found
    assert len(term_constructors) > 100
    assert [
        constructor.__name__
        for constructor in term_constructors
        if KINDS.get(constructor) != f"terms.{constructor.__name__}"
    ] == []


def test_the_schema_admits_the_kind_of_each_constructor_of_the_terms_as_a_node(
    term_constructors, schema
):
    """One of the two lists of kinds of the schema, those of the nodes with
    fields and of the nodes that bind variables, names the kind of each
    constructor of the terms, so that a constructor added to the grammar is
    not left out."""
    named = {
        kind
        for node in ("ordinaryNode", "scopedNode")
        for kind in schema["$defs"][node]["properties"]["node"]["enum"]
    }
    # a guard that the constructors of the terms were found
    assert len(term_constructors) > 100
    assert [
        constructor.__name__
        for constructor in term_constructors
        if f"terms.{constructor.__name__}" not in named
    ] == []


def test_the_schema_lists_the_fields_of_each_constructor_of_the_terms_in_order(
    term_constructors, schema
):
    """The table `x-constructors` of the schema lists, for the kind of each
    constructor of the terms, the fields of the constructor in their
    order."""
    # a guard that the constructors of the terms were found
    assert len(term_constructors) > 100
    assert [
        constructor.__name__
        for constructor in term_constructors
        if schema["x-constructors"].get(f"terms.{constructor.__name__}")
        != [field.name for field in fields(constructor)]
    ] == []


# --- the check of an encoding read as plain JSON ---


# six stages of the applications, one in the default set; the five stages
# `cons`, `port`, `ez_savings`, `cons_savings_iid` and `sa_savings` in the
# complete set; and, in the default set, two stage texts of this file and the
# two branching stages `tenure` and `retiree_death`, whose encodings hold
# branches
VALIDATED_STAGES = (
    one_row_by_default(
        (
            "buffer_stock",
            "adjuster_cons_with_egm_lines",
            "worker_saving",
            "retiree_saving",
            "keeper_saving",
            "adjuster_saving",
        )
    )
    + [
        pytest.param(name, marks=pytest.mark.complete_set)
        for name in ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings")
    ]
    + [
        pytest.param("clause_stage", id="a-policy-with-a-clause"),
        pytest.param("union_and_difference_stage", id="a-union-and-a-difference"),
        pytest.param("tenure"),
        pytest.param("retiree_death"),
    ]
)


@pytest.mark.parametrize("name", VALIDATED_STAGES)
def test_validate_encoding_accepts_the_encoding_of_each_stage(name, request):
    """The encoding of each stage, of the applications or of a stage text, is
    a document of the one schema, 2.6, which `validate_encoding` accepts."""
    encoding = request.getfixturevalue(name).encoding()
    assert encoding["schema"].endswith("/stage-encoding/2.6")
    validate_encoding(encoding)


@pytest.mark.parametrize("constructor", ["SetUnion", "SetDifference"])
def test_the_encoding_writes_a_declared_union_or_difference_as_a_term_of_its_constructor(
    constructor, union_and_difference_stage
):
    """The encoding of a stage that declares a parameter in a union or in a
    difference of sets writes the set as a term of that constructor."""
    written = json.dumps(union_and_difference_stage.encoding(), ensure_ascii=False)
    assert f'"__class__": "{constructor}"' in written


@pytest.mark.parametrize("constructor", ["SetUnion", "SetDifference"])
def test_the_encoding_writes_a_declared_union_or_difference_in_an_answer_as_a_node(
    constructor, union_and_difference_stage
):
    """The answers in the encoding of a stage that declares a parameter in a
    union or in a difference of sets write the set as a node of the kind of
    that constructor."""
    written = json.dumps(union_and_difference_stage.encoding(), ensure_ascii=False)
    assert f'"node": "terms.{constructor}"' in written


def test_the_json_of_the_parsed_term_of_a_stage_text_reads_back_to_the_same_term():
    """The term that the parser builds from a stage text with a union and a
    difference of sets, written by `to_json` as JSON text, reads back by
    `from_json` to the same term."""
    term, _ = parse_with_spans(UNION_AND_DIFFERENCE, "one_backward.bl")
    assert from_json(json.loads(json.dumps(to_json(term)))) == term


def without_a_declaration(encoding):
    """A document reference changed to name no identity of the encoding."""
    first_mapping(encoding, ref="document")["id"] = "missing-declaration"


def with_a_part_too_many_outside_a_function(encoding):
    """A function given a part read outside its scope that it does not
    have."""
    first_mapping(encoding, node="semantic.Lambda")["outside"].append(None)


def with_a_shape_on_a_function(encoding):
    """A function given a shape, the pattern of the variables that it binds,
    which only a set comprehension or an operator writes."""
    first_mapping(encoding, node="semantic.Lambda")["shape"] = [None]


def with_a_source_entry_that_lists_no_wire(encoding):
    """An entry that lists no wire added to the backward builders graph in
    `structural_sources` of the section `derived`, where the encoding lists
    each wire that starts inside a graph, written by no box and carried by no
    input of the graph."""
    encoding["derived"]["structural_sources"]["builders"]["backward"].append(
        {"path": [], "kind": "Spider", "outputs": []}
    )


def with_an_unknown_field_of_a_wire_type(encoding):
    """A wire type given a field that its kind does not have."""
    first_mapping(encoding, node="records.WireType")["fields"]["invented"] = None


def with_a_bound_reference_outside_every_scope(encoding):
    """A bound reference moved 999 scopes outward."""
    first_mapping(encoding, ref="bound")["depth"] = 999


def with_a_box_input_that_is_no_wire(encoding):
    """A box of the backward builders graph given an input that is no wire of
    the graph."""
    encoding["builders"]["backward"]["boxes"][0]["in"].append("missing-wire")


def with_an_identity_written_twice(encoding):
    """The first identity of the stage's answer written a second time with a
    different stage."""
    table = encoding["derived"]["stage"]["identities"]
    duplicate = deepcopy(table[0])
    duplicate["fields"]["stage"] = "different-stage"
    table.append(duplicate)


@pytest.mark.parametrize(
    "change,message",
    [
        pytest.param(
            without_a_declaration,
            "document identity 'missing-declaration' is not defined",
            id="a-document-reference-to-no-identity",
        ),
        pytest.param(
            with_a_part_too_many_outside_a_function,
            "semantic.Lambda has scope arity",
            id="a-function-with-a-part-too-many-outside-its-scope",
        ),
        pytest.param(
            with_a_shape_on_a_function,
            "semantic.Lambda has no bound-subject shape",
            id="a-function-with-a-shape",
        ),
        pytest.param(
            with_a_source_entry_that_lists_no_wire,
            "structural_sources/builders/backward/0/outputs: schema minItems",
            id="a-source-entry-that-lists-no-wire",
        ),
        pytest.param(
            with_an_unknown_field_of_a_wire_type,
            "records.WireType fields are",
            id="a-wire-type-with-a-field-of-no-kind",
        ),
        pytest.param(
            with_a_bound_reference_outside_every_scope,
            r"bound reference \(999, 0\) is outside its scope",
            id="a-bound-reference-outside-every-scope",
        ),
        pytest.param(
            with_a_box_input_that_is_no_wire,
            "box ports are absent from the graph wire table",
            id="a-box-input-that-is-no-wire",
        ),
        pytest.param(
            with_an_identity_written_twice,
            "document identity 'cntn_to_dcsn' has conflicting fields",
            id="an-identity-written-twice-with-different-fields",
        ),
    ],
)
def test_validate_encoding_refuses_an_encoding_changed_in_one_place(
    change, message, one_backward_encoding
):
    """`validate_encoding` refuses the encoding of `ONE_BACKWARD` with one
    change, naming the fault, where it accepts the encoding as the package
    writes it."""
    validate_encoding(one_backward_encoding)
    changed = deepcopy(one_backward_encoding)
    change(changed)
    with pytest.raises(ValueError, match=message):
        validate_encoding(changed)


# the discounting stage in the default set, and the five stages `cons`,
# `port`, `ez_savings`, `cons_savings_iid` and `sa_savings` in the complete
# set
@pytest.mark.parametrize(
    "name",
    one_row_by_default(
        ("disc_with_k_next", "cons", "port", "ez_savings", "cons_savings_iid", "sa_savings"),
        default="disc_with_k_next",
    ),
)
def test_the_operator_row_of_each_primitive_holds_the_parts_of_its_encoded_answer(name, request):
    """`operators` gives, for each primitive of the two builders graphs of
    the stage, a row whose rule, inputs, outputs and conditions are those of
    the encoded answer of the primitive."""
    stage = request.getfixturevalue(name)
    document = json.loads(json.dumps(stage.encoding(), allow_nan=False))
    rows = {row["address"]: row for row in operators(document)}
    expected = []
    for graph in (stage.builder.bwd, stage.builder.fwd):
        for primitive in graph.primitives.list():
            answer = graph.primitives[primitive].denote()
            parts = encode_answer(answer)["value"]["fields"]
            expected.append(
                (
                    answer.title.address,
                    [parts["expression"], parts["inputs"], parts["outputs"], parts["conditions"]],
                )
            )
    assert len(expected) > 0
    found = [
        (address, [rows[address][key] for key in ("rule", "inputs", "outputs", "conditions")])
        for address, _ in expected
    ]
    assert found == expected


# the stage whose continuation value has a set alias as its type in the
# default set, and the two stages of the applications whose wire types name a
# declaration, `cons` and `cons_savings_iid`, in the complete set
@pytest.mark.parametrize(
    "name",
    one_row_by_default(("aliased_stage", "cons", "cons_savings_iid"), default="aliased_stage"),
)
def test_each_declaration_that_a_wire_type_names_is_a_document_reference(name, request):
    """Each declaration that the type of a wire names, in the answers of the
    encoding, is a document reference."""
    document = json.loads(json.dumps(request.getfixturevalue(name).encoding(), allow_nan=False))
    declarations = [
        reference
        for node in mappings_within(document["derived"])
        if node.get("node") == "records.WireType"
        for reference, _ in node["fields"]["declarations"]
    ]
    assert len(declarations) > 0
    assert [reference for reference in declarations if reference.get("ref") != "document"] == []


def test_the_check_of_an_encoding_run_without_the_package_lists_the_row_of_a_pullback(
    cons, tmp_path
):
    """The module `bellman.display.encoding_checks`, run as a program by a
    Python that cannot import the package, lists the row of the pullback of
    `cntn_to_dcsn` from a file that holds the encoding of `cons`."""
    path = tmp_path / "cons.json"
    path.write_text(json.dumps(cons.encoding(), ensure_ascii=False))
    # the program puts the folder of jsonschema on the module path, asserts
    # that the package cannot be imported, and runs the module as a program
    program = (
        "import importlib.util,runpy,sys; sys.path.append(sys.argv.pop(1)); "
        "assert importlib.util.find_spec('bellman') is None; "
        "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    arguments = [
        str(Path(jsonschema.__file__).parents[1]),
        str(Path(encoding_checks.__file__)),
        str(path),
    ]
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", program, *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    rows = json.loads(result.stdout)
    address = cons.builder.bwd["cntn_to_dcsn", "Pullback"].denote().title.address
    row = next(row for row in rows if row["address"] == address)
    assert row["kind"] == "Pullback"
    assert row["rule"]["node"] == "semantic.Lambda"
    assert row["inputs"] and row["outputs"]


# --- the encoding of an answer: bound variables and the parts of a term ---


@pytest.mark.parametrize(
    "term,renamed",
    [
        pytest.param(
            nested_function("x", "y", "x"),
            nested_function("a", "b", "a"),
            id="a-function-of-a-function",
        ),
        pytest.param(quantified("forall", "x"), quantified("forall", "y"), id="forall"),
        pytest.param(quantified("exists", "x"), quantified("exists", "y"), id="exists"),
        pytest.param(
            joint_argmax("c", "h"), joint_argmax("a", "b"), id="an-argmax-of-two-controls"
        ),
    ],
)
def test_renaming_the_variables_that_a_term_binds_leaves_its_encoding_unchanged(term, renamed):
    """A term and the same term with the variables that it binds renamed have
    equal encodings."""
    assert encode_answer(term) == encode_answer(renamed)


def test_nested_functions_returning_the_inner_or_the_outer_variable_have_different_encodings():
    """Two nested functions of x and y, one returning x and one returning y,
    have different encodings."""
    assert encode_answer(nested_function("x", "y", "x")) != encode_answer(
        nested_function("x", "y", "y")
    )


def test_the_variable_of_the_outer_of_two_nested_functions_is_a_bound_reference_one_scope_out():
    """The variable x of the outer of two nested functions, read in the
    inner one, is written as the bound reference of depth 1 and position 0."""
    encoding = encode_answer(nested_function("x", "y", "x"))
    assert {"ref": "bound", "depth": 1, "position": 0} in list(mappings_within(encoding))


def test_an_integral_binds_its_variable_in_its_body_and_not_in_its_measure():
    """The symbol x is a bound reference in the body of the integral over x
    and an unresolved name in its measure, which is read outside its
    scope."""
    integral = typed_expressions.Integral(
        binding=(real_state("x"), terms.Named("ℝ")), measure=name_term("x"), body=name_term("x")
    )
    value = encode_answer(integral)["value"]
    # the parts that an integral reads outside its scope: the domain, then
    # the measure
    assert value["outside"][1]["fields"]["symbol"]["fields"]["name"]["ref"] == "unresolved"
    assert value["body"][0]["fields"]["symbol"]["fields"]["name"]["ref"] == "bound"


def test_the_encoding_keeps_the_order_of_the_conditions_of_a_comprehension():
    """The set of x in ℝ with x ≥ 0 and x ≤ 1, and the same set with its two
    conditions in the other order, have different encodings."""
    bounded = terms.Comprehension(
        bound=real_state("x"),
        base=terms.Named("ℝ"),
        conds=(
            terms.Rel(name_term("x"), terms.Ge(), terms.Number(0)),
            terms.Rel(name_term("x"), terms.Le(), terms.Number(1)),
        ),
    )
    reversed_conditions = replace(bounded, conds=bounded.conds[::-1])
    assert encode_answer(bounded) != encode_answer(reversed_conditions)


# the four operators whose subscript may select a declared name, which the
# encoding writes outside every scope
SELECTING_HEADS = ("D", "E", "argmax", "solve")


@pytest.mark.parametrize("head", SELECTING_HEADS)
def test_an_operator_whose_subscript_selects_a_name_is_written_as_a_node_with_fields(head):
    """An operator whose subscript selects the name x is written as a node of
    the kind `terms.Operator` with fields."""
    # the schema gives fields to a node that binds no variable; a node that
    # binds variables holds its parts outside and inside its scope instead
    value = encode_answer(selection(head))["value"]
    assert value["node"] == "terms.Operator"
    assert "fields" in value


@pytest.mark.parametrize("head", SELECTING_HEADS)
def test_two_operators_whose_subscripts_select_different_names_have_different_encodings(head):
    """An operator whose subscript selects the name x and the same operator
    selecting y have different encodings."""
    left = selection(head)
    assert encode_answer(left) != encode_answer(replace(left, subs=(terms.Var("y"),)))


@pytest.mark.parametrize("head", SELECTING_HEADS)
def test_a_name_that_a_subscript_selects_is_not_the_variable_of_an_enclosing_function(head):
    """Within a function of x, the name x that the subscript of an operator
    selects is written as an unresolved name, not as the bound variable."""
    function = typed_expressions.Lambda(
        bindings=((real_state("x"), terms.Named("ℝ")),), body=selection(head)
    )
    enclosed = encode_answer(function)
    selected = enclosed["value"]["body"][0]["fields"]["subs"][0]["fields"]["name"]
    assert selected == {"ref": "unresolved", "target": "x", "reason": "definition not retained"}


def test_a_later_domain_of_a_quantifier_reads_its_first_variable_and_an_enclosing_one_by_depth():
    """In a function of x over the set of y such that, for all z in ℝ and w
    in z + x, w holds, the domain of w refers to z at depth 0 and to x at
    depth 2."""
    x, y, z, w = map(real_state, ("x", "y", "z", "w"))
    second_domain = terms.Add(name_term("z"), name_term("x"))
    quantifier = terms.Operator(
        "forall",
        subs=(terms.In(z, terms.Named("ℝ")), terms.In(w, second_domain)),
        args=(name_term("w"),),
    )
    subject = terms.Group(inner=y, classifiers=(quantifier,))
    function = typed_expressions.Lambda(
        bindings=((x, terms.Named("ℝ")),),
        body=terms.Comprehension(bound=subject, base=terms.Named("ℝ"), conds=()),
    )
    comprehension = encode_answer(function)["value"]["body"][0]
    operator = comprehension["shape"]["fields"]["classifiers"][0]
    # the parts that an operator reads outside its scope: its head, then the
    # domain of each variable that it binds, in order, so that part 2 is the
    # domain of w
    # the scopes around the domain of w, from the inside: the quantifier, the
    # set of y, the function of x
    references = [
        (node["depth"], node["position"])
        for node in mappings_within(operator["outside"][2])
        if node.get("ref") == "bound"
    ]
    assert references == [(0, 0), (2, 0)]


def test_the_encoding_of_a_coordinate_depends_on_the_value_type_of_its_name():
    """A coordinate of the real state x and the same coordinate of a positive
    real state x have different encodings."""
    coordinate = terms.Coordinate(stem=real_state("x"), at=None, classifiers=())
    positive_real = ExpressionType(kind="scalar", domain="primitive:positive-real")
    positive = replace(coordinate, stem=replace(coordinate.stem, value_type=positive_real))
    assert encode_answer(coordinate) != encode_answer(positive)


def test_the_domain_of_the_second_control_of_an_argmax_reads_the_first_as_a_bound_variable():
    """In the argmax over c in C and h in the reals at most c, the domain of h
    refers to c as the bound reference of depth 1 and position 0."""
    # the parts that an operator reads outside its scope: its head, then the
    # domain of each variable that it binds, in order, so that part 2 is the
    # domain of h
    later_domain = encode_answer(joint_argmax("c", "h"))["value"]["outside"][2]
    assert {"ref": "bound", "depth": 1, "position": 0} in list(mappings_within(later_domain))


def test_encode_answer_writes_an_answer_without_calling_a_function_that_prints_it(
    cons, monkeypatch
):
    """`encode_answer` writes the answer of `cntn_to_dcsn` to the same
    encoding while each function that prints an expression, a layout or a
    card fails the test when it is called."""
    answer = cons.builder.bwd["cntn_to_dcsn"].denote()
    expected = encode_answer(answer)

    def forbidden(*args, **kwargs):
        pytest.fail("the encoding of an answer called a function that prints it")

    monkeypatch.setattr(typed_expressions, "format_expression", forbidden)
    monkeypatch.setattr(layout, "render", forbidden)
    monkeypatch.setattr(cards, "card_body_lines", forbidden)
    monkeypatch.setattr(cards, "card_of", forbidden)
    assert encode_answer(answer) == expected


def test_the_encoding_of_an_answer_reads_back_unchanged_from_strict_json(cons):
    """The encoding of the answer of `cntn_to_dcsn` reads back unchanged from
    strict JSON."""
    encoding = encode_answer(cons.builder.bwd["cntn_to_dcsn"].denote())
    assert json.loads(json.dumps(encoding, allow_nan=False)) == encoding


def test_the_answer_of_an_operation_with_another_expression_has_another_encoding(small_stage):
    """The answer of the pullback of `cntn_to_dcsn` and the same answer with
    the number 0 as its expression differ in their mathematical content."""
    answer = small_stage.builder.bwd["cntn_to_dcsn", "Pullback"].denote()
    changed = replace(answer, expression=terms.Number(0))
    assert mathematical_content(encode_answer(answer)) != mathematical_content(
        encode_answer(changed)
    )


# --- what a calibration changes in the encoding ---


def test_calibration_leaves_the_encoded_definitions_unchanged(small_stage, small_stage_calibrated):
    """The definitions of the encoding of the small stage are the same before
    and after its calibration."""
    symbolic, calibrated = small_stage.encoding(), small_stage_calibrated.encoding()
    assert symbolic["bindings"]["calibration"] != calibrated["bindings"]["calibration"]
    assert symbolic["definitions"] == calibrated["definitions"]


def test_calibration_changes_the_encoded_conditions(small_stage, small_stage_calibrated):
    """The conditions of the encoding of the small stage, its obligations,
    differ before and after its calibration."""
    assert (
        small_stage.encoding()["obligations"] != small_stage_calibrated.encoding()["obligations"]
    )


def test_calibration_leaves_the_rule_of_each_operator_row_unchanged(
    small_stage, small_stage_calibrated
):
    """The rules of the operator rows that `operators` lists of the encoding
    of the small stage are the same before and after its calibration."""
    symbolic, calibrated = small_stage.encoding(), small_stage_calibrated.encoding()
    assert symbolic["bindings"]["calibration"] != calibrated["bindings"]["calibration"]
    assert [row["rule"] for row in operators(symbolic)] == [
        row["rule"] for row in operators(calibrated)
    ]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_two_elaborations_of_a_stage_file_give_equal_encodings(src):
    """The stage file elaborated twice, each time anew, gives two stages
    whose encodings are equal in every section."""
    first, second = stage_from_file(src).encoding(), stage_from_file(src).encoding()
    assert differing_sections(first, second) == []


def test_a_calibration_changes_the_section_bindings_of_the_encoding_of_a_stage_file():
    """Of two stages elaborated from `cons.bl`, the one calibrated after its
    elaboration has an encoding whose section `bindings` differs."""
    # this shows that the comparison of sections in the test above finds a
    # section that differs
    stage, calibrated = stage_from_file(CORPUS["cons"]), stage_from_file(CORPUS["cons"])
    calibrated.calibrate(CONS_CALIBRATION)
    assert "bindings" in differing_sections(stage.encoding(), calibrated.encoding())
