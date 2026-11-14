"""A value field that the feasible set of a policy line reads is an input of
the policy builder.

The stage is the buffer-stock stage file with its feasible set written as
`Γ_c(x : ℝ₊₊) := {c : ℝ₊₊ | x - c >= L[>]}` and with `L[>] : ℝ @ !vlu` listed
on the policy header beside `V[>]`. The policy line
`c = argmax_{cp : Γ_c(m)}(…)` applies that set, so the line reads `L[>]`. The
signature of the policy builder lists the field, the stage records no
diagnostic under `unread-input` for the listing, and the route out of the
stage requires the field of the stage that follows it. The first two claims
are also made of the stage whose value block writes the field as it writes
the value.
"""
import pytest
from conftest import derived_buffer_stock_text, flat

from bellman.trellis import connection_report, elaborate_trellis


def replaced(text, *changes):
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


# the feasible set reads the continuation field, and the policy header lists it
READ_BY_THE_FEASIBLE_SET = (
    ("Γ_c(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}", "Γ_c(x : ℝ₊₊) := {c : ℝ₊₊ | x - c >= L[>]}"),
    (
        "[id=policy, (V[>] : ℝ @ !vlu) : !cntn ->",
        "[id=policy, (V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu) : !cntn ->",
    ),
)
# the value block and the arrival block write the field as they write the value
WRITTEN_AS_THE_VALUE_IS = (
    (
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = 𝑢(c) + β*V[>]               :: [id=value]\n",
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L[>] : ℝ @ !vlu, c) : !cntn"
        " -> (V : ℝ @ !vlu, L : ℝ @ !vlu) : !dcsn] {\n"
        "    V = 𝑢(c) + β*V[>]\n"
        "    L = L[>]\n",
    ),
    (
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
        "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n",
        "[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : ℝ @ !vlu) : !arvl] {\n"
        "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)\n"
        "    L[<] = E_{ψ,ξ}(L)\n",
    ),
)
BUFFER_STOCK = derived_buffer_stock_text()
WRITES_THE_FIELD = replaced(BUFFER_STOCK, *WRITTEN_AS_THE_VALUE_IS)
# the stage whose feasible set alone reads the field
READS_THE_FIELD = replaced(BUFFER_STOCK, *READ_BY_THE_FEASIBLE_SET)
# that stage, and the stage whose value block also writes the field
READING_STAGES = {
    "the feasible set alone reads the field": READS_THE_FIELD,
    "the value block also writes the field": replaced(WRITES_THE_FIELD, *READ_BY_THE_FEASIBLE_SET),
}
reading_stage = pytest.mark.parametrize("text", READING_STAGES.values(), ids=READING_STAGES.keys())


def route_between(earlier, later):
    """The printed line and the record of the one route of two periods joined
    by `{a: k}`, out of the stage text `earlier` into the stage text `later`.
    `periods[0]` is the later period."""
    occurrence = lambda text: {
        "stage": {"text": text, "origin": "buffer_stock.bl"},
        "calibration": {},
        "settings": {},
        "methods": {},
    }
    report = connection_report(
        elaborate_trellis(
            {
                "periods": [
                    {"stages": {"bs": occurrence(later)}, "connectors": []},
                    {"stages": {"bs": occurrence(earlier)}, "connectors": []},
                ],
                "inter_connectors": [{"a": "k"}],
            }
        )
    )
    (line,) = [line for line in str(report).splitlines() if line.startswith("route ")]
    (route,) = report.routes
    return line, route


@reading_stage
def test_the_signature_of_the_policy_builder_lists_the_field(elaborate_text, text):
    """`signature()` of the policy builder prints `𝐿≻` beside `𝑉≻` among its
    inputs."""
    stage = elaborate_text(text, "buffer_stock.bl")
    assert flat(str(stage.dcsn.builder.policy.signature())) == flat(
        "in   (𝑉≻, 𝐿≻) : Xa → ℝ × ℝ\nout  𝑐(m) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m) ∈ Γ_c(m)})"
    )


@reading_stage
def test_no_unread_input_is_recorded_for_the_listing(elaborate_text, text):
    """`diagnostics()` answers no diagnostic under `unread-input`."""
    stage = elaborate_text(text, "buffer_stock.bl")
    assert stage.diagnostics()["unread_inputs"] == ()


def test_the_route_into_a_period_that_does_not_supply_the_field_is_not_certified_and_names_it():
    """The later period is the buffer-stock stage file, which writes `V[<]`
    alone. The connection report prints the route as uncertified and names
    `L` as the component that the later period does not supply."""
    line, route = route_between(READS_THE_FIELD, BUFFER_STOCK)
    assert route.status == "uncertified"
    assert line == (
        "route periods[1].bs → periods[0].bs: uncertified, (a) → (k); the backward component "
        "buffer_stock:function:cntn:L is incompatible: every value periods[0].bs supplies "
        "answers another requirement of periods[1].bs, and none is left for "
        "buffer_stock:function:cntn:L"
    )


def test_the_route_into_a_period_that_writes_the_field_is_certified_with_the_field_paired():
    """The later period writes `L[<]` beside `V[<]`. The connection report
    prints the route as certified, and the route pairs each of the two fields
    that the earlier period requires with the field of its name."""
    line, route = route_between(READS_THE_FIELD, WRITES_THE_FIELD)
    assert line == "route periods[1].bs → periods[0].bs: certified, (a) → (k)"
    assert [(part.required, part.supplied, part.rule) for part in route.components] == [
        ("buffer_stock:function:cntn:V", "buffer_stock:function:arvl:V", "equal name"),
        ("buffer_stock:function:cntn:L", "buffer_stock:function:arvl:L", "equal name"),
    ]
