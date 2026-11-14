"""Tests of a stage that writes a second value-type field, one test for each
claim, each the stage text, the public query and the printed value.

The stage with two fields is the buffer-stock stage file with a second
value-type field `L` written as the value `V` is: its value block lists
`L[>]` and `L` and writes `L = L[>]`, and its arrival block lists `L` and
`L[<]` and writes `L[<] = E_{ψ,ξ}(L)`.

The card of a builder is the text its `denote()` prints. It prints under each
output of a value block the line that writes that output, in whatever order
the block writes its lines.

A derivative line, `D_{m}V = 𝑑𝑢(c)`, is recorded on the value its left side
names and on no other value the block writes: on the card, in the `Sort`
record of the value, in the name of the derivative's kernel and in the
answer to a line that reads the derivative.

The derivative of a value passes from the decision value to the arrival
value through an arrival block whose line of the value is an identity, in a
block that also writes a second field.
"""
import shutil

from conftest import HOUSING, PRELIMINARY, ROOT, derived_buffer_stock_text, flat, section

from bellman.trellis import derivative_missing, load_recipe, specify_trellis

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


def two_fields_text(*value_lines, arrival="L[<] = E_{ψ,ξ}(L)"):
    """The text of the stage with two fields, its value block holding
    `value_lines` in the order given and its arrival block writing `L[<]` by
    the line `arrival`."""
    text = derived_buffer_stock_text()
    blocks = {
        VALUE_BLOCK: (
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
            " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn] {\n"
            + "".join(f"    {line}\n" for line in value_lines)
            + "}"
        ),
        ARRIVAL_BLOCK: (
            "[id=dcsn_to_arvl, (V, L) : !dcsn"
            " -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl] {\n"
            "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)\n"
            f"    {arrival}\n"
            "}"
        ),
    }
    for before, after in blocks.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    return text


def test_the_card_of_a_value_builder_prints_under_each_output_the_line_that_writes_it(
        elaborate_text):
    """The value block of the stage with two fields writes `L = L[>]` before
    `V = 𝑢(c) + β*V[>]` under a header that lists `(V, L)`: the card prints
    the line of `V` under `𝑉` and the line of `L` under `𝐿`. The value block
    of the corpus file `rendahl-2015/growth.bl` begins with the local
    definition `c = z_d*𝑓(k_d) + (1-δ)*k_d - k_nxt`: the rule the card prints
    for the value is its line `V = 𝑢(c) + β*V[>]`, and not the local
    definition. How the card prints the local name `c` inside that rule is
    not asserted."""
    stage = elaborate_text(two_fields_text("L = L[>]", "V = 𝑢(c) + β*V[>]"), "two_fields.bl")
    card = str(stage.builder["cntn", "dcsn"].denote())
    assert (
        "     rule: 𝑉(m) = 𝑢(𝑐(m)) + β · 𝑉≻(𝑔≻(m, 𝑐(m)))\n"
        "           𝐿(m) = 𝐿≻(𝑔≻(m, 𝑐(m)))\n"
    ) in card

    path = f"{PRELIMINARY}/rendahl-2015/growth.bl"
    growth = elaborate_text((ROOT / path).read_text(encoding="utf-8"), path)
    aggregation = str(growth.builder["cntn", "dcsn"].primitives["Aggregation"].denote())
    rule = flat("\n".join(section(aggregation, "Rule")[1:]))
    assert rule.startswith("𝑉=𝑢(") and "+β·𝑉≻(𝑔≻(k_d,z_d,𝑘_nxt))" in rule
    assert "z_d·𝑓(k_d)" not in rule


def test_a_derivative_line_is_recorded_on_the_value_its_left_side_names_and_on_no_other(
        elaborate_text):
    """The value block of the stage with two fields gains the derivative line
    `D_{m}V = 𝑑𝑢(c)`, and no line states a derivative of `L`: the card prints
    the line under `𝑉` alone, the `Sort` record of `V` holds the derivative
    in `m` and that of `L` holds none, and the arrival line
    `L[<] = E_{ψ,ξ}(D_{m}L)`, which reads the derivative of `L`, is answered
    under `derivative-missing`. With the line `D_{m}L = 0` in place of the
    derivative of `V`, the card prints it under `𝐿` alone and the kernel of
    the derivative is named `D_{m}L`."""
    stage = elaborate_text(
        two_fields_text(
            "V = 𝑢(c) + β*V[>]", "L = L[>]", "D_{m}V = 𝑑𝑢(c)", arrival="L[<] = E_{ψ,ξ}(D_{m}L)"
        ),
        "two_fields.bl",
    )
    builder = stage.builder["cntn", "dcsn"]
    assert (
        "     rule: 𝑉 : Xm → ℝ\n"
        "           D_{m}𝑉(m) = 𝑑𝑢(𝑐(m))\n"
        "           𝐿 : Xm → ℝ\n"
        "\n"
    ) in str(builder.denote())
    value, second = builder.signature().outputs
    assert [str(coordinate) for coordinate in value.sort.derivatives] == ["buffer_stock:dcsn:m"]
    assert second.sort.derivatives == ()
    (missing,) = stage.diagnostics()["derivative_missing"]
    assert (
        "the block 'dcsn_to_arvl' reads `D_{m}L`, and the value `L` carries no derivative in m"
    ) in missing.message

    of_second = elaborate_text(
        two_fields_text("V = 𝑢(c) + β*V[>]", "L = L[>]", "D_{m}L = 0"), "two_fields.bl"
    )
    builder = of_second.builder["cntn", "dcsn"]
    assert (
        "     rule: 𝑉 : Xm → ℝ\n"
        "           𝐿 : Xm → ℝ\n"
        "           D_{m}𝐿(m) = 0\n"
        "\n"
    ) in str(builder.denote())
    assert builder.kernels().pieces[-1].outputs == ("D_{m}L",)


def test_the_derivative_of_a_value_passes_through_a_block_that_writes_a_second_field(tmp_path):
    """The terminal stage of the housing-frictions application gains a second
    value-type field: its value block lists `Θ[>]` and `Θ` and writes
    `Θ = Θ[>]`, and its arrival block lists `Θ` and `Θ[<]` and writes
    `Θ[<] = Θ`. Its methods file still states `D_{y_f_d}V = 0` and
    `D_{y_h_d}V = 0`, and no other file of the application changes.
    `derivative_missing` reports no derivative reading of the two saving
    stages as unmet at the terminal stage, as it reports none for the
    application as the repository writes it: the arrival value `V[<]` carries
    the derivatives of the decision value through the line `V[<] = V`."""
    registry = tmp_path / "declaration"
    shutil.copytree(HOUSING, registry)
    stage_file = registry / "stages/terminal/terminal.bl"
    text = stage_file.read_text(encoding="utf-8")
    changes = {
        "(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n": (
            "(V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu) : !cntn"
            " -> (V : ℝ @ !vlu, Θ : ℝ @ !vlu) : !dcsn] {\n"
            "    Θ = Θ[>]\n"
        ),
        "(V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n": (
            "(V, Θ) : !dcsn -> (V[<] : ℝ @ !vlu, Θ[<] : ℝ @ !vlu) : !arvl] {\n"
            "    Θ[<] = Θ\n"
        ),
    }
    for before, after in changes.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    stage_file.write_text(text, encoding="utf-8")
    assert derivative_missing(specify_trellis(load_recipe(registry, "spec.yml"))) == ()
