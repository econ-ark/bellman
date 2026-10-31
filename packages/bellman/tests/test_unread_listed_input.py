"""The acceptance file of the brief "a listed input no line reads becomes a
diagnostic, and the builder takes only the inputs the lines read" (AAS's
ruling of 17 October 2026; the second layer of the tests,
`packages/bellman/README.md` §8): one test for each of the brief's three
acceptance items on the package, and three on what follows from them; the
items that listed an unread marginal value were deleted under AMD-MB-001,
which retires the marginal field (decision MB-T44).

The rule: a value input a backward block's header lists and no line of the
block reads is admitted. It is left out of the block's inputs, so that the
block's signature, its builder and the formal arguments of the builder's
kernels are the same whether or not the header lists it; and the elaboration
records it as a diagnostic in the form of the connection diagnostics, under
the rule `unread-input`, which `stage.diagnostics()["unread_inputs"]`
answers and the encoding carries. The header text is unchanged and the card
prints it as written. A value input a line reads, and a control, are listed
and read as before; a value input a line reads and the header omits is still
refused under `signature-complete`. A block whose lines read no value input
keeps its header's value inputs as the formal input of its kernels, since the
header must list one (rule `value-input-role`), and records no diagnostic.
"""
import pytest
from conftest import DISC_TEXT, flat

from bellman.refusals import ConstructionError

# the policy header of `cons_savings_iid.bl`, whose one input its lines read
POLICY_HEADER = "[id=policy, (V[>] : ℝ @ !vlu) : !cntn ->"


def replaced(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def signatures(stage):
    """The printed signature of each backward builder of a stage, by name,
    and of its backward builders graph."""
    graph = stage.builder.bwd
    found = {name: flat(str(graph[name].signature())) for name in graph.list()}
    found["graph"] = flat(str(graph.signature()))
    return found


def test_item_2_a_listed_input_a_line_reads_is_no_diagnostic_and_its_builder_is_as_before(
        cons_savings_iid, cons):
    """The headers of `cons_savings_iid.bl` list nothing their lines do not
    read, the `!doc` line of the policy block reading `V[>]`: no diagnostic,
    and the builders' signatures are those the package printed before this
    change, with the values alone (AMD-MB-001). The value block of `cons.bl`
    reads its one listed input."""
    assert cons_savings_iid.diagnostics()["unread_inputs"] == ()
    found = signatures(cons_savings_iid)
    assert found["cntn_to_dcsn"] == flat("in   𝑉≻ : ℝ₊ → ℝ\nout  𝑉 : ℝ₊ → ℝ")
    assert found["policy"] == flat(
        "in   𝑉≻ : ℝ₊ → ℝ\nout  𝑐(w) : 𝒫({c ∈ (ℝ₊ → ℝ₊₊) | c(w) ∈ Γ(w)})"
    )
    assert signatures(cons)["cntn_to_dcsn"] == flat(
        "in   𝑉≻ : Xa → [−∞, ∞)\nout  𝑉 : Xm → [−∞, ∞)"
    )


def test_item_3_a_read_input_the_header_omits_is_still_refused_under_signature_complete(
        elaborate_text, text_of):
    """The policy block of `cons_savings_iid.bl` reading `V[>]`, its `!doc`
    line directly and its inverse Euler line through `D_{a}V[>]`, with the
    listing taken out of its header is refused under `signature-complete`
    at the first line that reads it, with the rule's existing message and
    correction."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(
            replaced(text_of("cons_savings_iid"), POLICY_HEADER, "[id=policy, () : !cntn ->"),
            "cons_savings_iid.bl",
        )
    assert (refused.value.rule, refused.value.address) == ("signature-complete", "policy.optimality")
    message = refused.value.message
    assert "reads V[>]" in message and "the value fields its lines read" in message
    assert "`(V[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn`" in message


def test_a_block_whose_lines_read_no_value_input_keeps_the_listed_input_as_its_formal_input(
        elaborate_text):
    """The discounting stage with its value line reading no value input,
    `V = β`, keeps the listed `V[>]` as the formal input of its kernel, as
    before, and records no diagnostic."""
    constant = elaborate_text(replaced(DISC_TEXT, "    V = β*V[>]\n", "    V = β\n"), "disc.bl")
    assert constant.diagnostics()["unread_inputs"] == ()
    assert signatures(constant)["cntn_to_dcsn"] == flat("in   𝑉≻ : ℝ₊ → ℝ\nout  𝑉 : ℝ₊ → ℝ")
