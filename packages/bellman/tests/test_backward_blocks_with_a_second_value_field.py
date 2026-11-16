"""Backward blocks that write a second value field beside the value: the
cards and the kernels of their lines, the derivatives that their lines state
and read, and the refusals of their lines; with them, two tests of stages of
one value field, the rule on the card of the Aggregation of `growth.bl` and
the refusal of a control written `c = c`."""

import shutil

import pytest
from application_files import CONTROL_BRANCHING_STAGE_FILES, COPIED_FILES_FOLDER, HOUSING, ROOT
from printed_text import card_section_lines, flat
from stage_builders import stage_from_text
from stage_texts import buffer_stock_text, changed, corpus_text, line_of

from bellman.refusals import ConstructionError
from bellman.trellis import derivative_missing, load_recipe, specify_trellis

# the value block and the arrival block of the buffer-stock stage file
BUFFER_STOCK_VALUE_BLOCK = (
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L : (-inf, 0] @ !vlu @ !cnst, c) : !cntn"
    " -> (V : ℝ @ !vlu, L) : !dcsn] {\n"
    "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    "}"
)


BUFFER_STOCK_ARRIVAL_BLOCK = (
    "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : (-inf, 0] @ !vlu @ !cnst)"
    " : !arvl] {\n"
    "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
    "    L[<] = if σ_ψ > 0 then 0 else Γ*L/R :: [id=borrowing_bound]\n"
    "}"
)


# the headers of the value block and of the arrival block of the stage with
# two fields: the buffer-stock stage whose two backward blocks also list and
# write a second value field `L`
VALUE_HEADER_OF_TWO_FIELDS = (
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
    " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn] {\n"
)


ARRIVAL_HEADER_OF_TWO_FIELDS = (
    "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl] {\n"
)


# the two blocks of the stage with two fields, their lines carrying ids
VALUE_BLOCK_OF_TWO_FIELDS = (
    VALUE_HEADER_OF_TWO_FIELDS + "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    "    L = L[>]                        :: [id=limit]\n"
    "}"
)


ARRIVAL_BLOCK_OF_TWO_FIELDS = (
    ARRIVAL_HEADER_OF_TWO_FIELDS + "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
    "    L[<] = E_{ψ,ξ}(L)               :: [id=limit]\n"
    "}"
)


# the name of the file that the tests give the stage with two fields
BUFFER_STOCK_ORIGIN = "buffer_stock.bl"


RET_CHOICE = CONTROL_BRANCHING_STAGE_FILES["ret_choice"]


def two_fields_text(*changes):
    """The text of the stage with two fields, whose lines carry ids, with
    each pair (text as written, text as changed) of `changes` replaced once."""
    return changed(
        buffer_stock_text(),
        (BUFFER_STOCK_VALUE_BLOCK, VALUE_BLOCK_OF_TWO_FIELDS),
        (BUFFER_STOCK_ARRIVAL_BLOCK, ARRIVAL_BLOCK_OF_TWO_FIELDS),
        *changes,
    )


def two_fields_writing(*value_lines, arrival="L[<] = E_{ψ,ξ}(L)"):
    """The text of the stage with two fields whose value block writes
    `value_lines` in the order given and whose arrival block writes `L[<]` by
    the line `arrival`, no line carrying an id."""
    value_block = (
        VALUE_HEADER_OF_TWO_FIELDS + "".join(f"    {line}\n" for line in value_lines) + "}"
    )
    arrival_lines = ["V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)", arrival]
    arrival_block = (
        ARRIVAL_HEADER_OF_TWO_FIELDS + "".join(f"    {line}\n" for line in arrival_lines) + "}"
    )
    return changed(
        buffer_stock_text(),
        (BUFFER_STOCK_VALUE_BLOCK, value_block),
        (BUFFER_STOCK_ARRIVAL_BLOCK, arrival_block),
    )


@pytest.fixture(scope="module")
def stating_the_derivative_of_the_value():
    """The stage with two fields whose value block also states the derivative
    `D_{m}V = 𝑑𝑢(c)` and whose arrival line reads the derivative of `L`."""
    text = two_fields_writing(
        "V = 𝑢(c) + β*V[>]", "L = L[>]", "D_{m}V = 𝑑𝑢(c)", arrival="L[<] = E_{ψ,ξ}(D_{m}L)"
    )
    return stage_from_text(text, "two_fields.bl")


@pytest.fixture(scope="module")
def stating_the_derivative_of_the_second_field():
    """The stage with two fields whose value block also states the derivative
    `D_{m}L = 0`."""
    text = two_fields_writing("V = 𝑢(c) + β*V[>]", "L = L[>]", "D_{m}L = 0")
    return stage_from_text(text, "two_fields.bl")


def test_the_card_of_a_value_builder_prints_each_rule_under_the_output_that_it_writes():
    """The card of the value builder of the stage with two fields, whose
    block writes `L = L[>]` before the line of `V`, prints the rule of `𝑉`
    first and the rule of `𝐿` under it."""
    stage = stage_from_text(two_fields_writing("L = L[>]", "V = 𝑢(c) + β*V[>]"), "two_fields.bl")
    card = str(stage.builder["cntn", "dcsn"].denote())
    assert (
        "     rule: 𝑉(m) = 𝑢(𝑐(m)) + β · 𝑉≻(𝑔≻(m, 𝑐(m)))\n           𝐿(m) = 𝐿≻(𝑔≻(m, 𝑐(m)))\n"
    ) in card


def test_the_rule_on_the_card_of_an_aggregation_is_the_value_line_and_not_a_local_definition(
    read_only_stage_from_file,
):
    """The value block of `growth.bl`, a copy of a stage file kept with the
    tests in the folder `rendahl-2015`, begins with the local definition of
    `c`, and the rule on the card of its Aggregation is its line
    `V = 𝑢(c) + β*V[>]`."""
    growth = read_only_stage_from_file(ROOT / COPIED_FILES_FOLDER / "rendahl-2015" / "growth.bl")
    aggregation = str(growth.builder["cntn", "dcsn"].primitives["Aggregation"].denote())
    rule = flat("\n".join(card_section_lines(aggregation, "Rule")[1:]))
    # how the card prints the local name `c` inside the rule is not compared
    assert rule.startswith("𝑉=𝑢(") and "+β·𝑉≻(𝑔≻(k_d,z_d,𝑘_nxt))" in rule
    # a term of the local definition `c = z_d*𝑓(k_d) + (1-δ)*k_d - k_nxt`
    assert "z_d·𝑓(k_d)" not in rule


@pytest.mark.parametrize(
    "stage_name, rule",
    [
        pytest.param(
            "stating_the_derivative_of_the_value",
            "     rule: 𝑉 : Xm → ℝ\n           D_{m}𝑉(m) = 𝑑𝑢(𝑐(m))\n           𝐿 : Xm → ℝ\n\n",
            id="the derivative of V",
        ),
        pytest.param(
            "stating_the_derivative_of_the_second_field",
            "     rule: 𝑉 : Xm → ℝ\n           𝐿 : Xm → ℝ\n           D_{m}𝐿(m) = 0\n\n",
            id="the derivative of L",
        ),
    ],
)
def test_the_card_prints_a_derivative_line_under_the_value_that_its_left_side_names(
    stage_name, rule, request
):
    """The card of the value builder of the stage with two fields prints a
    derivative line under the value that its left side names alone."""
    builder = request.getfixturevalue(stage_name).builder["cntn", "dcsn"]
    assert rule in str(builder.denote())


@pytest.mark.parametrize(
    "stage_name, value_coordinates, second_coordinates",
    [
        pytest.param(
            "stating_the_derivative_of_the_value",
            ["buffer_stock:dcsn:m"],
            [],
            id="the derivative of V",
        ),
        pytest.param(
            "stating_the_derivative_of_the_second_field",
            [],
            ["buffer_stock:dcsn:m"],
            id="the derivative of L",
        ),
    ],
)
def test_the_sort_of_a_value_holds_the_coordinate_of_a_derivative_that_a_line_states_of_it(
    stage_name, value_coordinates, second_coordinates, request
):
    """The sort of each value output of the value builder of the stage with
    two fields holds the coordinate of the derivative that a line states of
    that value, and no other."""
    builder = request.getfixturevalue(stage_name).builder["cntn", "dcsn"]
    value, second = builder.signature().outputs
    assert [str(coordinate) for coordinate in value.sort.derivatives] == value_coordinates
    assert [str(coordinate) for coordinate in second.sort.derivatives] == second_coordinates


def test_a_derivative_read_of_a_value_whose_derivative_no_line_states_is_a_diagnostic(
    stating_the_derivative_of_the_value,
):
    """The arrival line `L[<] = E_{ψ,ξ}(D_{m}L)` of the stage with two fields,
    which reads the derivative of `L` where no line states that derivative,
    is recorded under `derivative-missing`."""
    (missing,) = stating_the_derivative_of_the_value.diagnostics()["derivative_missing"]
    assert (
        "the block 'dcsn_to_arvl' reads `D_{m}L`, and the value `L` carries no derivative in m"
    ) in missing.message


@pytest.mark.parametrize(
    "stage_name, outputs",
    [
        pytest.param("stating_the_derivative_of_the_value", ("D_{m}V",), id="the derivative of V"),
        pytest.param(
            "stating_the_derivative_of_the_second_field", ("D_{m}L",), id="the derivative of L"
        ),
    ],
)
def test_the_kernel_of_a_derivative_line_writes_the_derivative_that_its_left_side_names(
    stage_name, outputs, request
):
    """The last piece of the kernels of the value builder of the stage with
    two fields, the piece of its derivative line, writes the derivative that
    the left side of the line names."""
    builder = request.getfixturevalue(stage_name).builder["cntn", "dcsn"]
    assert builder.kernels().pieces[-1].outputs == outputs


# the value block and the arrival block of the terminal stage of the
# housing-frictions application, each also listing and writing a second
# value field `Θ`
SECOND_FIELD_OF_THE_TERMINAL_STAGE = (
    (
        "(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n",
        "(V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu) : !cntn"
        " -> (V : ℝ @ !vlu, Θ : ℝ @ !vlu) : !dcsn] {\n"
        "    Θ = Θ[>]\n",
    ),
    (
        "(V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n",
        "(V, Θ) : !dcsn -> (V[<] : ℝ @ !vlu, Θ[<] : ℝ @ !vlu) : !arvl] {\n    Θ[<] = Θ\n",
    ),
)


def test_the_derivative_of_a_value_passes_through_a_block_that_writes_a_second_field(tmp_path):
    """In the housing-frictions application whose terminal stage writes a
    second value field `Θ` beside its value, the arrival value `V[<]` still
    carries the derivatives that the methods file of that stage states, so
    that `derivative_missing` reports no derivative read of the trellis."""
    registry = tmp_path / "declaration"
    shutil.copytree(HOUSING, registry)
    terminal = registry / "stages" / "terminal" / "terminal.bl"
    text = changed(terminal.read_text(encoding="utf-8"), *SECOND_FIELD_OF_THE_TERMINAL_STAGE)
    terminal.write_text(text, encoding="utf-8")
    assert derivative_missing(specify_trellis(load_recipe(registry, "spec.yml"))) == ()


# the line of `V` of the value block of `ret_choice.bl`, which the policy's
# maximand matches, and a line of a second field `Θ` that the label `d` selects
CHOICE_VALUE_LINE = "    V = (V_w[>] - δ, V_r[>])[d]                   :: [id=choice_value]\n"


CHOICE_SECOND_LINE = "    Θ = (Θ_w[>], Θ_r[>])[d]                       :: [id=choice_limit]\n"


# the value block and the arrival block of `ret_choice.bl`, each also listing
# the second field `Θ`, and the arrival line that writes `Θ[<]`
SECOND_FIELD_OF_THE_CHOICE = (
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


@pytest.fixture(scope="module")
def ret_choice_with_a_second_field():
    """The text of `ret_choice.bl` whose value block and arrival block also
    list the second field `Θ`, before a line of the value block writes it."""
    text = (ROOT / RET_CHOICE).read_text(encoding="utf-8")
    return changed(text, *SECOND_FIELD_OF_THE_CHOICE)


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(
            CHOICE_VALUE_LINE + CHOICE_SECOND_LINE, id="the line of the second field after"
        ),
        pytest.param(
            CHOICE_SECOND_LINE + CHOICE_VALUE_LINE, id="the line of the second field before"
        ),
    ],
)
def test_the_value_line_of_a_choice_is_the_line_whose_tuple_the_policy_maximizes(
    lines, ret_choice_with_a_second_field
):
    """In `ret_choice.bl` with the second field `Θ`, the line of `V` is the
    value line, since the policy maximizes over its tuple: the stage
    elaborates, and a policy that writes the entries of that tuple in the
    other order is refused under `branch-tuple-mismatch` at that line."""
    ordered = changed(ret_choice_with_a_second_field, (CHOICE_VALUE_LINE, lines))
    stage = stage_from_text(ordered, RET_CHOICE)
    assert flat(str(stage.builder["cntn", "dcsn"].signature())) == flat(
        "in   𝑉_w≻ : ℝ₊ → [−∞, ∞)\n"
        "in   𝑉_r≻ : ℝ₊ → [−∞, ∞)\n"
        "in   𝛩_w≻ : ℝ₊ → ℝ\n"
        "in   𝛩_r≻ : ℝ₊ → ℝ\n"
        "out  (𝑉, 𝛩) : ℝ₊ → [−∞, ∞) × ℝ"
    )
    maximand = ("argmax_{d}(V_w[>] - δ, V_r[>])", "argmax_{d}(V_r[>], V_w[>] - δ)")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(ordered, maximand), RET_CHOICE)
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
            ARRIVAL_BLOCK_OF_TWO_FIELDS,
            "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n"
            "    L = L                           :: [id=limit]\n"
            "}",
            id="the arrival block",
        ),
        pytest.param(
            "cntn_to_dcsn",
            VALUE_BLOCK_OF_TWO_FIELDS,
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
    block, written, bare
):
    """A backward block of the stage with two fields that lists `L` without a
    mark and writes `L = L` is refused under `definition-order` at that line,
    with a sentence that names the two marked spellings of `L`."""
    text = two_fields_text((written, bare))
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, BUFFER_STOCK_ORIGIN)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("definition-order", f"{block}.limit")
    assert (refusal.file, refusal.line) == (BUFFER_STOCK_ORIGIN, line_of(text, "L = L "))
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


def test_a_backward_line_that_defines_a_control_by_itself_is_refused_with_its_reason_alone():
    """The value block of the buffer-stock stage that writes `c = c`, where
    `c` is the control that its header lists, is refused under
    `definition-order` at that line with a reason that names no marked
    spelling and with no action, since a backward header lists no marked
    control."""
    text = changed(
        buffer_stock_text(),
        (
            BUFFER_STOCK_VALUE_BLOCK,
            BUFFER_STOCK_VALUE_BLOCK.replace(
                ":: [id=value]\n",
                ":: [id=value]\n    c = c                           :: [id=by_itself]\n",
            ),
        ),
    )
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, BUFFER_STOCK_ORIGIN)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("definition-order", "cntn_to_dcsn.by_itself")
    assert (refusal.file, refusal.line) == (BUFFER_STOCK_ORIGIN, line_of(text, "c = c "))
    assert refusal.message == (
        "the two sides of this line of block 'cntn_to_dcsn' are the one name c, so the line "
        "defines c by itself, the cycle c → c; c is a control, and the lines of a backward "
        "block are read at the controls that its header lists"
    )
    assert refusal.write is None
    assert [marked for marked in ("c[>]", "c[<]") if marked in str(refusal)] == []


@pytest.fixture(scope="module")
def tenure_text():
    """The text of `tenure.bl` of the durables application, whose headers
    list the field `V_kp` as `V_kp[>]` alone."""
    return corpus_text("tenure")


@pytest.fixture(scope="module")
def buffer_stock_listing_l_with_a_mark():
    """The text of the buffer-stock stage whose value block also lists the
    field `L[>]`."""
    return changed(
        buffer_stock_text(),
        ("(V[>] : ℝ @ !vlu, c) : !cntn", "(V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"),
    )


# a definition that reads bare a field that the headers list with a mark
# alone: the fixture that gives the text, the stage, the text as written and
# as changed, the definition, and the sentence of the refusal, whose last
# clause is the action that the refusal carries
BARE_READS = [
    pytest.param(
        "tenure_text",
        "tenure",
        "@stage: tenure\n",
        "@stage: tenure\nXV := {x : ℝ | x > V_kp}\n",
        "XV := {x : ℝ | x > V_kp}",
        "the definition of the set 'XV' reads the name 'V_kp' in the set "
        "`{x : ℝ | x > V_kp}`, and the headers of the stage list the field V_kp with a "
        "mark alone, as `V_kp[>]`; a bare name reads the field that a header lists "
        "without a mark. Write `V_kp[>]` in place of `V_kp`",
        id="a set of tenure",
    ),
    pytest.param(
        "buffer_stock_listing_l_with_a_mark",
        "buffer_stock",
        "Xm := ℝ",
        "Xm := {x : ℝ | x > L}",
        "Xm := {x : ℝ | x > L}",
        "the definition of the set 'Xm' reads the name 'L' in the set `{x : ℝ | x > L}`, "
        "and the headers of the stage list the field L with a mark alone, as `L[>]`; a "
        "bare name reads the field that a header lists without a mark. Write `L[>]` in "
        "place of `L`",
        id="the set of resources of buffer_stock",
    ),
    pytest.param(
        "buffer_stock_listing_l_with_a_mark",
        "buffer_stock",
        "@stage: buffer_stock\n",
        "@stage: buffer_stock\n𝑓(x : ℝ) := x - L\n",
        "𝑓(x : ℝ) := x - L",
        "the definition of '𝑓' mentions 'L', and the headers of the stage list the field "
        "L with a mark alone, as `L[>]`; a bare name reads the field that a header lists "
        "without a mark. Write `L[>]` in place of `L`",
        id="a function of buffer_stock",
    ),
]


@pytest.mark.parametrize(
    "text_fixture, stage, written, replacement, definition, sentence", BARE_READS
)
def test_a_set_or_a_function_that_reads_bare_a_field_listed_with_a_mark_alone_is_refused(
    text_fixture, stage, written, replacement, definition, sentence, request
):
    """A named set or function, the first item after the `@stage` line, that
    reads bare a field that the headers list with a mark alone is refused
    under `name-in-scope` at the definition, with a sentence that names the
    marked spelling and ends with the action that the refusal carries."""
    text = changed(request.getfixturevalue(text_fixture), (written, replacement))
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, f"{stage}.bl")
    refusal = refused.value
    # a definition is addressed by its place among the items of the file, the
    # `@stage` line being the first
    assert (refusal.rule, refusal.address) == ("name-in-scope", "2")
    assert (refusal.file, refusal.line) == (f"{stage}.bl", line_of(text, definition))
    assert refusal.message == sentence
    assert refusal.write == sentence.rsplit(". ", 1)[1]


def test_the_refusal_of_an_arrival_line_with_no_expectation_names_every_shock_of_its_edge():
    """The arrival line `L[<] = L` of the stage with two fields is refused
    under `shock-observed` with the advice to write the expectation over ψ
    and ξ, the shocks of its edge, and the line written so is read."""
    as_written = "    L[<] = E_{ψ,ξ}(L)               :: [id=limit]\n"
    text = two_fields_text((as_written, "    L[<] = L                        :: [id=limit]\n"))
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, BUFFER_STOCK_ORIGIN)
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("shock-observed", "dcsn_to_arvl.limit")
    advice = "Write the expectation over every shock of that edge, `E_{ψ,ξ}(…)`"
    assert refusal.message == (
        "the line is read at the arvl perch and mentions L, a field at the dcsn perch; the "
        "edge from the arvl perch to the dcsn perch draws the shock ξ, ψ, so the value of L "
        f"is not known at the arvl perch. {advice}"
    )
    assert refusal.write == advice
    assert stage_from_text(two_fields_text(), BUFFER_STOCK_ORIGIN).name == "buffer_stock"
