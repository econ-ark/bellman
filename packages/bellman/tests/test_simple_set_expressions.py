"""Five acceptance items for products and equality in feasible sets.

Construction and inspection use the public stage API and the shared joint
choice fixture. Witness points check the mathematical conditions printed
from the object; they do not exercise a numerical equality solver.
"""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from conftest import JOINT_CHOICE, stage_from_text
from jsonschema import Draft202012Validator

from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.source import to_source

PRODUCT = (
    JOINT_CHOICE.replace("@stage: joint_choice", "@stage: joint_choice\nΓ(z : ℝ₊) := [0, z] × ℝ₊")
    .replace("x : ℝ", "x : ℝ₊")
    .replace("x_d : ℝ", "x_d : ℝ₊")
    .replace("u : ℝ × ℝ", "u : ℝ₊ × ℝ₊")
    .replace("argmax_{u}", "argmax_{u : Γ(x_d)}")
)
EQUALITY = PRODUCT.replace(
    "Γ(z : ℝ₊) := [0, z] × ℝ₊",
    "Γ(z : ℝ₊) := {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}",
).replace("u : ℝ₊ × ℝ₊", "u : ℝ₊ × ℝ₊ × ℝ₊")


def test_item_1_both_correspondences_elaborate_with_their_full_domains():
    """The exact declarations retain ordered factors, z and the Eq relation."""
    for text, kind, expected in (
        (PRODUCT, T.Product, "[0, z] × ℝ₊"),
        (EQUALITY, T.Comprehension, "{q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}"),
    ):
        stage = stage_from_text(text, "feasible.bl")
        definition = stage.definitions["joint_choice:correspondence:Γ"]
        core = definition.equations[0]
        assert isinstance(core, T.CorrDef)
        assert isinstance(core.body, kind)
        assert core.params[0].stem == "z"
        assert to_source(core.body) == expected
        if isinstance(core.body, T.Product):
            assert len(core.body.factors) == 2
        else:
            assert len(core.body.base.factors) == 3
            assert isinstance(core.body.conds[0].op, T.Eq)


def test_item_2_joint_feasibility_retains_all_coordinates_and_conditions():
    """At z=3, (1,2,0) is feasible; (1,1,0) and (1,2,-1) are not."""
    for text in (
        PRODUCT,
        EQUALITY,
        EQUALITY.replace("= z}", "= z, q[3] <= z}"),
        EQUALITY.replace("x_d", "q"),
    ):
        stage = stage_from_text(text, "joint_feasible.bl")
        choice = stage.definitions["policy.choice"].equations[0].rhs
        assert isinstance(choice.subs[0], T.In)
        assert to_source(choice.subs[0].set) == ("Γ(q)" if "Γ(q)" in text else "Γ(x_d)")
        assert len(stage.builder.policy.signature().outputs) == 1
        for answer in (
            stage.definitions.denote("joint_choice:correspondence:Γ"),
            stage.builder.policy.denote(),
        ):
            assert "UNRESOLVED" not in str(answer)
        printed = str(stage.definitions.denote("joint_choice:correspondence:Γ"))
        if text != PRODUCT:
            assert "q[1] + q[2] = z" in printed
            assert "ℝ₊ × ℝ₊ × ℝ₊" in printed
        if "q[3] <= z" in text:
            assert "q[3] ≤ z" in printed
    # These are the two retained restrictions: the three nonnegative
    # coordinates and equality of the first two coordinates' sum with z.
    points = ((1, 2, 0), (1, 1, 0), (1, 2, -1))
    assert [all(value >= 0 for value in q) and q[0] + q[1] == 3 for q in points] == [
        True,
        False,
        False,
    ]


def test_item_3_source_json_and_public_denotations_preserve_meaning():
    """Source and annotated AST agree; exports retain the relation."""
    schema = json.loads(
        files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text()
    )
    for text in (PRODUCT, EQUALITY):
        annotated = text.replace(
            "\n[id=arvl", ' :: [id=feasible, "the authored set"]\n[id=arvl', 1
        )
        parsed = parse_with_spans(annotated).term
        assert from_json(json.loads(json.dumps(to_json(parsed)))) == parsed
        core = next(item.core for item in parsed.items if isinstance(item, T.Statement))
        assert (
            parse_with_spans("@stage: check\n" + to_source(core) + "\n").term.items[1].core == core
        )
        stage = stage_from_text(annotated, "annotated_feasible.bl")
        exported = stage.encoding()
        Draft202012Validator(schema).validate(json.loads(json.dumps(exported)))
        encoded = next(
            record for record in exported["definitions"] if record["kind"] == "correspondence"
        )
        assert encoded["equations"][0]["term"] == to_json(core)
        for answer in (stage.denote(), stage.builder.policy.denote()):
            assert "UNRESOLVED" not in str(answer)
    for body in ("{0, …, J} × ℝ₊", "{0, κ} ⊂ ℤ × ℝ₊"):
        indexed = PRODUCT.replace(
            "Γ(z : ℝ₊) := [0, z] × ℝ₊", "J : ℕ\nκ : ℤ\nΓ(z : ℝ₊) := " + body
        ).replace("argmax_{u : Γ(x_d)}", "argmax_{u}")
        indexed_stage = stage_from_text(indexed)
        indexed_answer = indexed_stage.definitions.denote("joint_choice:correspondence:Γ").denoted[
            0
        ]
        assert "z" not in str(indexed_answer.mathematical_type)
        assert "ℤ × ℝ₊" in str(indexed_answer.mathematical_type)
        assert "UNRESOLVED" not in str(indexed_answer)
        factors = indexed_answer.expression.body.factors
        assert len(factors) == 2 and factors[1] == T.Named("ℝ₊")
        assert isinstance(factors[0], (T.IntegerRange, T.Points))
        assert ("J" if "J" in body else "κ") in str(factors[0])
    # An unused correspondence must also have a resolved result set. An
    # argument-dependent bound stays in the expression, not free in its type.
    unused = stage_from_text(PRODUCT.replace("argmax_{u : Γ(x_d)}", "argmax_{u}"))
    denoted = unused.definitions.denote("joint_choice:correspondence:Γ").denoted[0]
    assert "UNRESOLVED" not in str(denoted)
    assert "z" not in str(denoted.mathematical_type)
    assert "[0, z] × ℝ₊" in str(denoted.expression)
    bounded_base = EQUALITY.replace("q : ℝ₊ × ℝ₊ × ℝ₊", "q : [0, z] × ℝ₊ × ℝ₊").replace(
        "argmax_{u : Γ(x_d)}", "argmax_{u}"
    )
    bounded = stage_from_text(bounded_base)
    answer = bounded.definitions.denote("joint_choice:correspondence:Γ").denoted[0]
    assert "z" not in str(answer.mathematical_type)
    assert "UNRESOLVED" not in str(answer)
    assert "[0, z] × ℝ₊ × ℝ₊" in str(answer.expression)
    mixed = PRODUCT.replace("[0, z] × ℝ₊", "(0, z) × {low, high}").replace(
        "argmax_{u : Γ(x_d)}", "argmax_{u}"
    )
    mixed_stage = stage_from_text(mixed)
    assert "UNRESOLVED" not in str(mixed_stage.definitions.denote("joint_choice:correspondence:Γ"))


def test_item_4_old_forms_and_positioned_refusals_are_preserved():
    """Tuples remain expressions and invalid coordinates receive refusals."""
    for declaration, kind in (
        ("f(z : ℝ) := (z, z + 1)", T.FuncDef),
        ("Γ(z : ℝ) := (0, z]", T.CorrDef),
        ("Γ(z : ℝ) := [0, z)", T.CorrDef),
        ("Γ(z : ℝ) := [0, z]", T.CorrDef),
        ("Γ(z : ℝ) := {q : ℝ | q < z}", T.CorrDef),
        ("f(z : ℝ) := z + 1", T.FuncDef),
    ):
        parsed = parse_with_spans("@stage: old\n" + declaration + "\n").term
        core = next(item.core for item in parsed.items if isinstance(item, T.Statement))
        assert isinstance(core, kind)
        assert (
            parse_with_spans("@stage: old\n" + to_source(core) + "\n").term.items[1].core == core
        )
    for text, rule in (
        (EQUALITY.replace("q[2] = z", "q[4] = z"), "family-selection"),
        (EQUALITY.replace("q[2] = z", "q[2] = missing"), "name-in-scope"),
        (EQUALITY.replace("q[1] + q[2]", "q[0] + q[2]"), "family-selection"),
        (PRODUCT.replace("@stage: joint_choice", "@stage: joint_choice\nθ : ℝ, = 1"), "syntax"),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text, "invalid_set.bl")
        error = refused.value
        assert error.rule == rule
        assert (
            error.file == "invalid_set.bl" and error.line is not None and error.column is not None
        )
        if rule == "syntax":
            assert (error.line, error.column) == (2, 8)
