"""Refusals of the language that stand beside the forms of supplied fields:
a shock that no header lists, a set of functions on a set that is no finite
index set, a table that is called, an output that no line defines, a bare
name beside the same name written with a mark, a forward block that lists a
field which the stage sends backward, and the rules of three further faults."""

import pytest
from test_modular_fields import CONSUMPTION, FUNCTION_VALUE, KEPT_BOUND, SECOND_FIELD

from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text

_UNLISTED_SHOCK = "@stage: consumption\ny : ℝ\ny ~ N(0, 1)"

_FUNCTION_CONSTANT = """@stage: probe
Xa := ℝ₊
β : (0,1)
𝑢(c : ℝ₊₊) := log(c)
Γ_c(x : ℝ₊₊) := (0, x]

[id=arvl_to_dcsn, (a : Xa) : !arvl -> (m : ℝ₊₊) : !dcsn] {
    m = a + 1
}
[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_n : Xa) : !cntn] {
    a_n = m - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, f : Xa → ℝ @ !vlu @ !cnst, c) : !cntn -> (V : ℝ @ !vlu, f) : !dcsn] {
    V = 𝑢(c) + β*V[>] + f(m - c)
}
[id=dcsn_to_arvl, (V, f) : !dcsn -> (V[<] : ℝ @ !vlu, f) : !arvl] {
    V[<] = V
}
[id=policy, (V[>], f) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>] + f(m - cp))
}
"""

_TABLE = """@stage: tab
Z := {1, 2}
F : Z → ℝ
[id=arvl_to_dcsn, (z : Z) : !arvl -> (z_d : Z) : !dcsn] {
    z_d = z
}
[id=dcsn_to_cntn, (z_d) : !dcsn -> (z_e : Z) : !cntn] {
    z_e = z_d
}
[id=cntn_to_dcsn, (W[>] : ℝ @ !vlu) : !cntn -> (W : ℝ @ !vlu) : !dcsn] {
    W = W[>] + F[z_d]
}
[id=dcsn_to_arvl, (W) : !dcsn -> (W[<] : ℝ @ !vlu) : !arvl] {
    W[<] = W
}
"""


_AGE_TABLE = """@stage: pension
Age := {1, 2}
Next := {2, 3}
Y_tab : Age → ℝ

[id=dcsn_to_cntn, (m : ℝ) : !dcsn -> (a : ℝ) : !cntn] {
    a = m
}
[id=cntn_to_dcsn, (age[>] : Next @ !vlu @ !cnst) : !cntn
    -> (age : Age @ !vlu @ !cnst, pension : ℝ @ !vlu @ !cnst) : !dcsn] {
    age = age[>] - 1
    pension = Y_tab[age]
}
"""


def _refusal(text):
    """The refusal that the elaboration of `text` raises."""
    with pytest.raises(ConstructionError) as refusal:
        elaborate_text(text, "probe.bl")
    return refusal.value


@pytest.mark.parametrize(
    ("base", "line"),
    (
        (CONSUMPTION, "W = c + W[>]/2 + y"),
        (SECOND_FIELD, "W = c + W[>]/2\n    B = y"),
    ),
    ids=("the maximized value", "a second field"),
)
def test_a_value_line_that_reads_a_shock_no_header_lists_is_refused(base, line):
    """A shock that has a law and that no header lists is no input of a
    block. A value line that reads it is refused under `signature-complete`,
    as a line that reads any name its header does not list."""
    text = base.replace("@stage: consumption", _UNLISTED_SHOCK).replace("W = c + W[>]/2", line)
    refusal = _refusal(text)
    assert refusal.rule == "signature-complete"
    assert "y" in refusal.message


def test_a_set_of_functions_on_a_continuous_set_types_a_value_field_alone():
    """`Xa → ℝ` with `Xa` no finite index set is the declared set of a
    constant value-type field, whose value is one function. Declared for a
    parameter, the same set is refused under `readable-form`."""
    stage = elaborate_text(_FUNCTION_CONSTANT, "probe.bl")
    assert {identity.perch for identity in stage.fields() if identity.field == "f"} == {
        "arvl", "dcsn", "cntn"
    }
    parameter = SECOND_FIELD.replace(
        "@stage: consumption", "@stage: consumption\ng : ℝ → ℝ"
    ).replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = g(c)")
    refusal = _refusal(parameter)
    assert refusal.rule == "readable-form"
    assert "no finite index set" in refusal.message


def test_a_table_is_selected_with_brackets_and_is_not_called():
    """A collection on a finite index set is a table: `F[z_d]` selects its
    entry, and the call `F(z_d)` is refused, since the table is a declared
    value and no function."""
    elaborate_text(_TABLE, "tab.bl")
    refusal = _refusal(_TABLE.replace("F[z_d]", "F(z_d)"))
    assert refusal.rule == "definition-order"
    assert "'F'" in refusal.message


def test_an_output_that_no_line_defines_is_refused_as_such():
    """A header that takes in `L[>]` and lists `L` on its output side keeps
    no name, since a marked name and a bare name are two fields. With no line
    for `L` the stage is refused under `output-defined`, and not for a
    dependence of the constant that no line states."""
    text = KEPT_BOUND.replace(
        "L : (-inf, 0] @ !vlu @ !cnst, c)", "L[>] : (-inf, 0] @ !vlu @ !cnst, c)"
    )
    refusal = _refusal(text)
    assert refusal.rule == "output-defined"
    assert "no line of the block defines L" in refusal.message


def test_a_bare_name_is_the_field_that_the_header_lists_bare():
    """A header that lists `W[>]` among its inputs and `W` among its outputs
    names two fields. A bare `W` on a later line of the block is the decision
    field, so the divisor `W` of `B = 1/W` is recorded as a condition on the
    decision field, which is declared on ℝ and may be zero."""
    text = (
        SECOND_FIELD.replace("(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ₊₊ @ !vlu, c)")
        .replace("W = c + W[>]/2", "W = c - W[>]/2\n    B = 1/W")
        .replace("cp + W[>]/2", "cp - W[>]/2")
    )
    stage = elaborate_text(text, "probe.bl")
    found = [
        condition.explanation
        for condition in stage.obligations()
        if condition.condition == "arithmetic-definedness"
    ]
    assert found == ["The divisor W at cntn_to_dcsn.2 must be nonzero."]


def test_a_table_key_written_bare_has_the_set_of_the_field_listed_bare():
    """Where a block takes in `age[>]` on one set and writes `age` on another,
    the key of `Y_tab[age]` is the field written, and its declared set is
    compared with the table's index set."""
    elaborate_text(_AGE_TABLE, "pension.bl")
    later = (
        _AGE_TABLE.replace("age[>] : Next", "age[>] : Age")
        .replace("(age : Age @ !vlu @ !cnst,", "(age : Next @ !vlu @ !cnst,")
        .replace("age = age[>] - 1", "age = age[>] + 1")
    )
    refusal = _refusal(later)
    assert refusal.rule == "family-selection"
    assert "{2, 3}" in refusal.message


@pytest.mark.parametrize(
    ("block", "text"),
    (
        (
            "arvl_to_dcsn",
            SECOND_FIELD.replace("(k : ℝ) : !arvl", "(k : ℝ, B) : !arvl").replace(
                "m = k + 1", "m = k + B"
            ),
        ),
        (
            "dcsn_to_cntn",
            SECOND_FIELD.replace("(m, c : ℝ₊ @ !ctrl) : !dcsn", "(m, B, c : ℝ₊ @ !ctrl) : !dcsn")
            .replace("a = m - c", "a = m - c + B")
            .replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = 1"),
        ),
    ),
    ids=("the arrival field", "the decision field"),
)
def test_a_forward_block_lists_no_field_that_the_stage_sends_backward(block, text):
    """A backward builder pulls its inputs back along the law of the forward
    block between its two perches. A forward block that lists the field which
    that builder writes would make the builder read its own output, so the
    listing is refused under `header-coordinate`."""
    refusal = _refusal(text)
    assert refusal.rule == "header-coordinate"
    assert f"the forward block {block!r} lists B" in refusal.message


def test_the_word_cnst_on_a_state_is_refused_under_the_rule_of_constants():
    """`!cnst` types a value-type field alone."""
    refusal = _refusal(CONSUMPTION.replace("(k : ℝ) : !arvl", "(k : ℝ @ !cnst) : !arvl"))
    assert refusal.rule == "constant-dependence"
    assert "k carries !cnst" in refusal.message


def test_a_function_valued_field_called_with_two_arguments_is_ill_typed():
    """A field on the set of functions ℝ → ℝ takes one argument."""
    refusal = _refusal(FUNCTION_VALUE.replace("B = f(c)", "B = f(c, m)"))
    assert refusal.rule == "well-typed"
    assert "supplies 2 arguments" in refusal.message


def test_branches_of_different_kinds_are_named_as_branches():
    """A formula by cases whose branches are a tuple and a number is refused
    with a sentence about its two branches, not about the sides of a line."""
    text = SECOND_FIELD.replace(
        "W = c + W[>]/2", "W = c + W[>]/2\n    B = if m > 0 then (1, 2) else 3"
    )
    refusal = _refusal(text)
    assert refusal.rule == "well-typed"
    assert "the branch after `else`" in refusal.message
    assert "the branches of a formula by cases are of one kind" in refusal.message
