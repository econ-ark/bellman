"""The package's answers on a stage with a second value-type field, and on
texts near that form (the third layer of the tests,
`packages/bellman/README.md` §8).

A value-type field is a field listed with the role word `!vlu`, as the value
`V` is. Each test writes a stage file of an application with a second such
field, or one of its lines in a form the package refuses, and states the
answer of the public call: the rule, the address and the sentence of the
refusal, or the reading where the text is admitted.

The stage with two fields is the buffer-stock stage with a second field `L`
written as the value is: its value block lists `L[>]` and `L` and writes
`L = L[>]`, and its arrival block lists `L` and `L[<]` and writes
`L[<] = E_{ψ,ξ}(L)`.
"""

import pytest
from conftest import BRANCHING_STAGES, ROOT, derived_buffer_stock_text, flat, methodized

from bellman.refusals import ConstructionError

BUFFER_STOCK = "buffer_stock.bl"
# the value block and the arrival block of `buffer_stock.bl` as the
# repository writes them, and the same two blocks with the second field `L`
VALUE_BLOCK = (
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    "}"
)
ARRIVAL_BLOCK = (
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
    "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
    "}"
)
VALUE_BLOCK_WITH_L = (
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
    " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    "    L = L[>]                        :: [id=limit]\n"
    "}"
)
ARRIVAL_BLOCK_WITH_L = (
    "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl] {\n"
    "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
    "    L[<] = E_{ψ,ξ}(L)               :: [id=limit]\n"
    "}"
)
RET_CHOICE = BRANCHING_STAGES["ret_choice"]
PERFECT_FORESIGHT = (
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight"
)


def changed(text, *changes):
    """`text` with each pair (text as written, text as changed) replaced
    once."""
    for written, replacement in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, replacement)
    return text


def two_fields(*changes):
    """The text of the stage with two fields, with each pair of `changes`
    replaced once."""
    return changed(
        derived_buffer_stock_text(),
        (VALUE_BLOCK, VALUE_BLOCK_WITH_L),
        (ARRIVAL_BLOCK, ARRIVAL_BLOCK_WITH_L),
        *changes,
    )


def line_of(text, written):
    """The number of the one line of `text` that holds `written`."""
    (number,) = [n for n, line in enumerate(text.splitlines(), 1) if written in line]
    return number


def test_the_value_line_of_a_chosen_label_is_the_line_whose_tuple_the_policy_maximizes(
    elaborate_text,
):
    """`ret_choice.bl` with a second field `Θ` that the chosen label `d`
    selects, `Θ = (Θ_w[>], Θ_r[>])[d]`. The policy maximizes over the tuple
    of the line of `V`, so that line is the value line, and the stage is read
    with the line of `Θ` after it and with the line of `Θ` before it. A
    policy that writes the entries of that tuple in the other order is
    refused under `branch-tuple-mismatch` at the line of `V`, in either
    order of the two lines."""
    value_line = "    V = (V_w[>] - δ, V_r[>])[d]                   :: [id=choice_value]\n"
    second_line = "    Θ = (Θ_w[>], Θ_r[>])[d]                       :: [id=choice_limit]\n"
    text = changed(
        (ROOT / RET_CHOICE).read_text(encoding="utf-8"),
        (
            "(V_w[>] : [-inf, inf) @ !vlu, V_r[>] : [-inf, inf) @ !vlu, d) : !cntn"
            " -> (V : [-inf, inf) @ !vlu) : !dcsn] {\n",
            "(V_w[>] : [-inf, inf) @ !vlu, V_r[>] : [-inf, inf) @ !vlu,"
            " Θ_w[>] : ℝ @ !vlu, Θ_r[>] : ℝ @ !vlu, d) : !cntn"
            " -> (V : [-inf, inf) @ !vlu, Θ : ℝ @ !vlu) : !dcsn] {\n",
        ),
        (
            "(V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {\n"
            "    V[<] = V                                  :: [id=value]\n",
            "(V, Θ) : !dcsn -> (V[<] : [-inf, inf) @ !vlu, Θ[<] : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = V                                  :: [id=value]\n"
            "    Θ[<] = Θ                                  :: [id=limit]\n",
        ),
    )
    signature = flat(
        "in   𝑉_w≻ : ℝ₊ → [−∞, ∞)\n"
        "in   𝑉_r≻ : ℝ₊ → [−∞, ∞)\n"
        "in   𝛩_w≻ : ℝ₊ → ℝ\n"
        "in   𝛩_r≻ : ℝ₊ → ℝ\n"
        "out  (𝑉, 𝛩) : ℝ₊ → [−∞, ∞) × ℝ"
    )
    maximand = ("argmax_{d}(V_w[>] - δ, V_r[>])", "argmax_{d}(V_r[>], V_w[>] - δ)")
    for lines in (value_line + second_line, second_line + value_line):
        ordered = changed(text, (value_line, lines))
        stage = elaborate_text(ordered, RET_CHOICE)
        assert flat(str(stage.builder["cntn", "dcsn"].signature())) == signature
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(changed(ordered, maximand), RET_CHOICE)
        refusal = refused.value
        assert (refusal.rule, refusal.address) == (
            "branch-tuple-mismatch",
            "cntn_to_dcsn.choice_value",
        )
        assert refusal.message == (
            "the value line selects from (V_w[>] - δ, V_r[>]) by 'd', and the policy line "
            "policy.choice maximizes over (V_r[>], V_w[>] - δ); write the policy's maximand "
            "as the value line's tuple, in its order"
        )


@pytest.mark.parametrize(
    "block, written, bare",
    [
        pytest.param(
            "dcsn_to_arvl",
            ARRIVAL_BLOCK_WITH_L,
            "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
            "    L = L                           :: [id=limit]\n"
            "}",
            id="the arrival block",
        ),
        pytest.param(
            "cntn_to_dcsn",
            VALUE_BLOCK_WITH_L,
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L : ℝ @ !vlu, c) : !cntn"
            " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn] {\n"
            "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
            "    L = L                           :: [id=limit]\n"
            "}",
            id="the value block",
        ),
    ],
)
def test_a_backward_line_whose_two_sides_are_one_bare_name_is_refused_as_a_cycle(
    block, written, bare, elaborate_text
):
    """The stage with two fields whose arrival block lists `L` in place of
    `L[<]`, or whose value block lists `L` in place of `L[>]`, and writes
    `L = L`: refused under `definition-order` at the line, and the sentence
    names the two marked spellings."""
    text = two_fields((written, bare))
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, BUFFER_STOCK)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("definition-order", f"{block}.limit")
    assert (refusal.file, refusal.line) == (BUFFER_STOCK, line_of(text, "L = L "))
    advice = (
        "Write `L = L[>]` where the line reads the field at the continuation perch, or "
        "`L[<] = …` where it writes the field at the arrival perch, and list the field with "
        "that mark in the header of the block"
    )
    assert refusal.message == (
        f"the two sides of this line of block {block!r} are the one name L, so the line "
        "defines L by itself, the cycle L → L; a mark tells the fields of one name at two "
        "perches apart: `L[>]` is the field at the continuation perch and `L[<]` the field "
        f"at the arrival perch. {advice}"
    )
    assert refusal.write == advice


def test_a_backward_line_that_defines_a_control_by_itself_is_refused_with_its_reason_alone(
    elaborate_text,
):
    """The buffer-stock stage whose value block writes `c = c`, where `c` is
    the control that the header of the block lists: refused under
    `definition-order` at the line. The sentence gives the reason and names
    no marked spelling, and the refusal carries no action: the header of
    that block admits no marked control (`field-perch`)."""
    text = changed(
        derived_buffer_stock_text(),
        (
            VALUE_BLOCK,
            VALUE_BLOCK.replace(
                ":: [id=value]\n",
                ":: [id=value]\n    c = c                           :: [id=by_itself]\n",
            ),
        ),
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, BUFFER_STOCK)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("definition-order", "cntn_to_dcsn.by_itself")
    assert (refusal.file, refusal.line) == (BUFFER_STOCK, line_of(text, "c = c "))
    assert refusal.message == (
        "the two sides of this line of block 'cntn_to_dcsn' are the one name c, so the line "
        "defines c by itself, the cycle c → c; c is a control, and the lines of a backward "
        "block are read at the controls that its header lists"
    )
    assert refusal.write is None
    for marked in ("c[>]", "c[<]"):
        assert marked not in str(refusal)


@pytest.mark.parametrize(
    "stage, written, definition, sentence",
    [
        pytest.param(
            "tenure",
            "@stage: tenure\n",
            "XV := {x : ℝ | x > V_kp}",
            "the definition of the set 'XV' reads the name 'V_kp' in the set "
            "`{x : ℝ | x > V_kp}`, and the headers of the stage list the field V_kp with a "
            "mark alone, as `V_kp[>]`; a bare name reads the field that a header lists "
            "without a mark. Write `V_kp[>]` in place of `V_kp`",
            id="a set of tenure",
        ),
        pytest.param(
            "buffer_stock",
            "Xm := ℝ₊₊",
            "Xm := {x : ℝ | x > L}",
            "the definition of the set 'Xm' reads the name 'L' in the set `{x : ℝ | x > L}`, "
            "and the headers of the stage list the field L with a mark alone, as `L[>]`; a "
            "bare name reads the field that a header lists without a mark. Write `L[>]` in "
            "place of `L`",
            id="the set of resources of buffer_stock",
        ),
        pytest.param(
            "buffer_stock",
            "@stage: buffer_stock\n",
            "𝑓(x : ℝ) := x - L",
            "the definition of '𝑓' mentions 'L', and the headers of the stage list the field "
            "L with a mark alone, as `L[>]`; a bare name reads the field that a header lists "
            "without a mark. Write `L[>]` in place of `L`",
            id="a function of buffer_stock",
        ),
    ],
)
def test_a_set_or_a_function_that_reads_bare_a_field_listed_with_a_mark_alone_is_refused(
    stage, written, definition, sentence, elaborate_text, text_of
):
    """`tenure.bl`, whose headers list `V_kp[>]` alone, with a named set that
    reads `V_kp`; and the buffer-stock stage whose value block lists `L[>]`,
    with its set `Xm` or a function reading `L`. Each definition is the
    first item after the `@stage` line. Each text is refused under
    `name-in-scope` at the definition, with the file and the line, and the
    sentence names the marked spelling that the headers list."""
    if stage == "tenure":
        text = text_of("tenure")
    else:
        text = changed(
            derived_buffer_stock_text(),
            ("(V[>] : ℝ @ !vlu, c) : !cntn", "(V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"),
        )
    added = f"{written}{definition}\n" if written.startswith("@stage") else definition
    text = changed(text, (written, added))
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, f"{stage}.bl")
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("name-in-scope", "2")
    assert (refusal.file, refusal.line) == (f"{stage}.bl", line_of(text, definition))
    assert refusal.message == sentence
    assert refusal.write == sentence.rsplit(". ", 1)[1]


def test_the_refusal_of_an_arrival_line_with_no_expectation_names_every_shock_of_its_edge(
    elaborate_text,
):
    """The stage with two fields whose arrival line is `L[<] = L`. The edge
    from the arrival perch to the decision perch draws ψ and ξ, and the
    refusal under `shock-observed` advises the expectation over both; the
    line written as advised is read."""
    as_written = "    L[<] = E_{ψ,ξ}(L)               :: [id=limit]\n"
    text = two_fields((as_written, "    L[<] = L                        :: [id=limit]\n"))
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, BUFFER_STOCK)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("shock-observed", "dcsn_to_arvl.limit")
    advice = "Write the expectation over every shock of that edge, `E_{ψ,ξ}(…)`"
    assert refusal.message == (
        "the line is read at the arvl perch and mentions L, a field at the dcsn perch; the "
        "edge from the arvl perch to the dcsn perch draws the shock ξ, ψ, so the value of L "
        f"is not known at the arvl perch. {advice}"
    )
    assert refusal.write == advice
    assert elaborate_text(two_fields(), BUFFER_STOCK).name == "buffer_stock"


def test_an_output_that_an_explicit_block_of_a_methods_file_leaves_unwritten_is_refused_there(
    elaborate_text,
):
    """`perfect_foresight.bl` with a second field `Θ`, read with the methods
    file beside it as the repository writes that file, whose `!explicit`
    blocks write the value alone. `methodize` refuses the stage under
    `output-defined` at the entry of the methods file that types the block;
    the sentence names that block and says that its lines stand in place of
    the stage file's lines and that none defines `Θ`."""
    stage_file, methods_file = "perfect_foresight.bl", "methods.bl"
    text = changed(
        (ROOT / PERFECT_FORESIGHT / stage_file).read_text(encoding="utf-8"),
        (
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
            "    V = 𝑢(c) + β*V[>]               :: [id=value]\n",
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu, c) : !cntn"
            " -> (V : ℝ @ !vlu, Θ : ℝ @ !vlu) : !dcsn] {\n"
            "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
            "    Θ = Θ[>]                        :: [id=limit]\n",
        ),
        (
            "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n",
            "[id=dcsn_to_arvl, (V, Θ) : !dcsn -> (V[<] : ℝ @ !vlu, Θ[<] : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n"
            "    Θ[<] = Θ                        :: [id=limit]\n",
        ),
    )
    methods = (ROOT / PERFECT_FORESIGHT / methods_file).read_text(encoding="utf-8")
    stage = elaborate_text(text, stage_file)
    with pytest.raises(ConstructionError) as refused:
        methodized(stage, {"text": methods, "origin": methods_file})
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("output-defined", "cntn_to_dcsn")
    assert (refusal.file, refusal.line) == (
        methods_file,
        line_of(methods, "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit]"),
    )
    advice = (
        "Write in that block of methods.bl a line that defines Θ: `Θ = …`, or, if block "
        "'cntn_to_dcsn' is not meant to write Θ, remove Θ from the output side of its header"
    )
    assert refusal.message == (
        "the header of block 'cntn_to_dcsn' lists Θ on its output side, and no line defines "
        "Θ in the block `[id=cntn_to_dcsn]` of methods.bl, whose lines stand in place of the "
        f"stage file's lines of the block under !explicit. {advice}"
    )
    assert refusal.write == advice
    (listed,) = refusal.related
    assert (listed.role, listed.file, listed.line) == (
        "listed output",
        stage_file,
        line_of(text, "[id=cntn_to_dcsn,"),
    )
