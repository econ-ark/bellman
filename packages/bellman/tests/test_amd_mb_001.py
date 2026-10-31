"""The acceptance file of unit A of the build of AMD-MB-001, the language: the
derivative term on a value field and the roles `!mrgnvl` and `!sndmrgnvl`
retired. One test per item of the amendment's §11 that this unit carries,
named `test_item_<n>_<claim>`. The decisions the unit took are the rows MB-A
of the development repository's decisions file `MB-A-the-language.md`.
"""

from __future__ import annotations

import pytest

from bellman.refusals import ConstructionError
from bellman.stage.grains import construction_table, wire_table
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source

# a consumption stage of the explicit way of writing whose policy block reads
# one term of the continuation value; `TERM` is the spelling under test and
# `_discrete_text` adds a discrete state through the three perches
POLICY = (
    "@stage: t\n"
    "𝑢(c : ℝ₊₊) := c^(1-2)/(1-2)\n"
    "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-2)\n"
    "𝑑𝑢 := D_{c}(𝑢)\n"
    "[id=arvl_to_dcsn, (m[<] : ℝ₊) : !arvl -> (m : ℝ₊) : !dcsn] {\n    m = m[<]\n}\n"
    "[id=dcsn_to_cntn, (m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
    "    a = m - c\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + V[>]  :: [id=value]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
    "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
    "    c[>] = 𝑑𝑢𝑖𝑛𝑣(TERM)  :: [id=InvEuler]\n"
    "    m[>] = a + c[>]     :: [id=grid]\n"
    "    c = c[>]            :: [id=identification]\n}\n"
)


# a stage with no control whose decision builder states a composite derivative
# line, an expectation of a derivative term of the continuation value times a
# parameter, the form of the portfolio stages (the typing reads the line as a
# statement about the output value, with no unknown; MB-A13)
COMPOSITE = (
    "@stage: t\n"
    "R : ℝ₊₊\n"
    "θ : ℝ₊₊\n"
    "θ ~ LogNormal(0, 1)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, θ) : !dcsn -> (m : ℝ₊₊) : !cntn] {\n    m = k_d*R + θ\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V        = E_{θ}(V[>])          :: [id=value]\n"
    "    D_{k_d}V = E_{θ}(D_{m}V[>]*R)   :: [id=marginal]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
)


# a portfolio stage of the applications' form: the share ς is the control, two
# shocks are drawn on the way to the continuation perch, and the decision
# builder's derivative line integrates a derivative term of the continuation
# value over both (MB-A17)
PORTFOLIO = (
    "@stage: t\n"
    "R : ℝ₊₊\n"
    "Ψ : ℝ₊₊\n"
    "θ : ℝ₊₊\n"
    "Ψ ~ LogNormal(0, 1)\n"
    "θ ~ LogNormal(0, 1)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, ς : !ctrl @ [0, 1], Ψ, θ) : !dcsn -> (m_next : ℝ₊₊) : !cntn] {\n"
    "    m_next = k_d*(ς*Ψ + (1 - ς)*R) + θ\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, ς) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V        = E_{Ψ,θ}(V[>])                                 :: [id=value]\n"
    "    D_{k_d}V = E_{Ψ,θ}(D_{m_next}V[>]*(ς*Ψ + (1 - ς)*R))   :: [id=marginal]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
    "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (ς : [0, 1] @ !ctrl) : !dcsn] {\n"
    "    ς = solve_{ς}(E_{Ψ,θ}(D_{m_next}V[>]*(Ψ - R)))   :: [id=foc]\n}\n"
)
GAUSS_HERMITE = {
    "stage": "t",
    "methods": [{"on": "E_Ψ_θ", "method": "!gauss-hermite", "settings": {"n_nodes": [7, 7]}}],
}


def _text(term):
    return POLICY.replace("TERM", term)


def _parsed(term):
    """The parsed file of `POLICY` with `term` as the argument read."""
    return parse_with_spans(_text(term), "t.bl")[0]


def _discrete_text(term):
    """`POLICY` with a discrete state `k` on {0, 1} carried through the three
    perches, so that the continuation perch has a discrete coordinate."""
    text = _text(term)
    for written, changed in (
        (
            "(m[<] : ℝ₊) : !arvl -> (m : ℝ₊) : !dcsn] {\n    m = m[<]\n}",
            "(m[<] : ℝ₊, k[<] : {0, 1}) : !arvl -> (m : ℝ₊, k : {0, 1}) : !dcsn] {\n"
            "    m = m[<]\n    k = k[<]\n}",
        ),
        (
            "(m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = m - c\n}",
            "(m, c : !ctrl @ ℝ₊₊, k) : !dcsn -> (a : ℝ₊, k[>] : {0, 1}) : !cntn] {\n"
            "    a = m - c\n    k[>] = k\n}",
        ),
    ):
        assert text.count(written) == 1, written
        text = text.replace(written, changed)
    return text


def _refusal(term, text=None):
    """The refusal of the stage of `POLICY`, or of `text`, with `term` read, or
    None where it elaborates."""
    from conftest import stage_from_text

    try:
        stage_from_text(_text(term) if text is None else text)
    except ConstructionError as error:
        return error
    return None


def test_item_3_a_derivative_term_on_a_field_reads_as_the_parenthesized_call():
    """`D_{a}V[>]`, `D_{m}V` and `D_{a}V[<]` lower to the term the
    parenthesized spelling lowers to (amendment §4.2, D2)."""
    assert _parsed("D_{a}V[>]") == _parsed("D_{a}(V[>])")
    assert _parsed("D_{m}V") == _parsed("D_{m}(V)")
    assert _parsed("D_{a}V[<]") == _parsed("D_{a}(V[<])")
    assert _parsed("D_{a}V[>]") != _parsed("D_{a}(V)")
    # the term elaborates where its subscript names a state of the perch at
    # which the value is read, and the operator on a declared function stands
    assert _refusal("D_{a}V[>]") is None
    # a subscript naming no state of that perch, or a discrete state
    refused = _refusal("D_{q}V[>]")
    assert (refused.rule, refused.address) == ("derivative-coordinate", "policy.InvEuler")
    assert "'q'" in refused.message and "cntn" in refused.message and " a" in refused.message
    refused = _refusal("D_{k}V[>]", _discrete_text("D_{k}V[>]"))
    assert refused.rule == "derivative-coordinate" and "discrete" in refused.message
    assert _refusal("D_{c}V[>]").rule == "derivative-coordinate"
    # the inverse Euler row's kernel takes the derivative term it reads as one
    # named argument, and its function evaluates the author's right side at the
    # value the caller supplies (MB-A16; nothing is differentiated)
    from conftest import stage_from_text

    reading = stage_from_text(_text("D_{a}V[>]"))
    row = kernel(reading, "policy.grid:Aggregation")
    assert [name for name, _ in row.arguments] == ["V≻", "a", "D_{a}(V≻)"]
    assert compile_kernel(reading, "policy.grid:Aggregation")(0.0, 1.0, 4.0) == (4.0**-2, 1 + 4.0**-2)
    # a derivative of a value the block does not list is refused as an unlisted
    # read is (amendment §4.2)
    assert _refusal("D_{m}V").rule == "signature-complete"


def test_item_1a_the_oracle_stage_file_elaborates_with_values_alone_and_the_policy_reads_the_value():
    """The oracle of unit A, `applications/portfolio-choice/declaration/stages/cons/cons.bl`
    rewritten by the amendment's §4.1: its headers list values and controls
    alone, its decision builder's second line is the derivative line
    `D_{m_d}V = 𝑑𝑢(c)`, and the stage elaborates with the policy builder's
    signature (V[>]) ↦ c; the decision builder's Evaluation records the
    derivative line as a stated derivative in the coordinate `m_d`, the value
    wire it writes lists that coordinate under `Sort.derivatives`, the line is
    no retained relation, and `stage.obligations()` lists `marginal-reading`
    for it (amendment §4.3, §5.1, §5.2; D4)."""
    from conftest import ROOT, stage_from_text

    path = "applications/portfolio-choice/declaration/stages/cons/cons.bl"
    text = (ROOT / path).read_text(encoding="utf-8")
    assert "!mrgnvl" not in text and "!sndmrgnvl" not in text
    assert "    D_{m_d}V = 𝑑𝑢(c)" in text
    stage = stage_from_text(text, path)
    signature = str(stage.dcsn.builder.policy.signature())
    assert signature.splitlines()[0].split()[:2] == ["in", "𝑉≻"]
    assert signature.splitlines()[1].split()[1].startswith("𝑐(m_d)")
    assert "dV" not in signature

    rows = [
        row
        for row in construction_table(stage).primitive_rows
        if row.kind == "Evaluation" and row.builder == "cntn_to_dcsn"
    ]
    assert len(rows) == 1 and len(rows[0].outputs) == 1
    ((coordinate, term, address, source),) = rows[0].derivatives
    assert (coordinate.field, address) == ("m_d", "cntn_to_dcsn.marginal")
    # a bare field name prints in parentheses, since the printer cannot tell it
    # from a function name; a marked field prints bare, `D_{a}V[>]` (MB-A11)
    assert (to_source(term), source) == ("𝑑𝑢(c)", "D_{m_d}(V) = 𝑑𝑢(c)")
    assert wire_table(stage).sort_of(rows[0].outputs[0]).derivatives == (coordinate,)
    conditions = {item.condition for item in stage.obligations()}
    assert "retained-relation" not in conditions
    listed = [item for item in stage.obligations() if item.condition == "marginal-reading"]
    assert [entry.address for item in listed for entry in item.entries] == ["cntn_to_dcsn.marginal"]
    assert "envelope conditions" in listed[0].explanation
    # the stated derivative compiles as the piece `marginal:Derivative:1`, whose
    # arguments are those of the builder's G and whose output is the right side
    # evaluated there (MB-A14)
    piece = kernel(stage, "marginal:Derivative:1")
    assert [name for name, _ in piece.arguments] == ["V≻", "m_d", "c"]
    assert (piece.outputs, piece.parameters) == (("D_{m_d}V",), ("ρ",))
    assert compile_kernel(stage, "marginal:Derivative:1")(0.0, 2.0, 0.5, 2.0) == 0.5 ** (-2.0)
    assert [p.name for p in stage.builder["cntn", "dcsn"].kernels().pieces][-1] == "marginal:Derivative:1"
    # the composite derivative line, an expectation of a derivative term of the
    # continuation value times a parameter, elaborates and is recorded alike
    from conftest import stage_from_text

    composite = stage_from_text(COMPOSITE)
    rows = [
        row
        for row in construction_table(composite).primitive_rows
        if row.kind == "Evaluation" and row.builder == "cntn_to_dcsn"
    ]
    ((coordinate, term, address, source),) = rows[0].derivatives
    assert (coordinate.field, address) == ("k_d", "cntn_to_dcsn.marginal")
    assert to_source(term) == "E_{θ}(D_{m}V[>]*R)"
    conditions = [item.condition for item in composite.obligations()]
    assert "marginal-reading" in conditions and "retained-relation" not in conditions
    # a stage-wide quadrature entry binds at the expectation of the derivative
    # line with its two shocks counted, and the stage configures
    portfolio = stage_from_text(PORTFOLIO)
    portfolio.methodize(GAUSS_HERMITE)
    assert "cntn_to_dcsn.marginal:Expectation:1   !gauss-hermite" in str(portfolio.methods)
    portfolio.configure({"settings": {}})
    # the derivative line's right side is one expectation: the piece compiles its
    # integrand with the shocks among its arguments and names them (MB-A18)
    piece = kernel(portfolio, "marginal:Derivative:1")
    assert [name for name, _ in piece.arguments] == ["ς", "Ψ", "θ", "D_{m_next}V[>]"]
    assert piece.integrated == ("Ψ", "θ") and "integrated over Ψ, θ" in str(piece)
    integrand = compile_kernel(portfolio, "marginal:Derivative:1")
    assert integrand(0.5, 1.2, 1.0, 3.0, 1.1) == pytest.approx(3.0 * (0.5 * 1.2 + 0.5 * 1.1))
    assert [p.integrated for p in portfolio.builder["cntn", "dcsn"].kernels().pieces][-1] == ("Ψ", "θ")


# --- unit B: the trellis ---

# a consumption stage that declares no arrival perch, whose decision perch is
# its entry perch (D8, P2), and whose policy line reads a derivative of the
# continuation value; `TERM` is the derivative term under test
CONS_ENTRY = (
    "@stage: cons\n"
    "ρ : (1, inf)\n"
    "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n"
    "𝑑𝑢 := D_{c}(𝑢)\n"
    "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n"
    "[id=dcsn_to_cntn, (m : ℝ₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
    "    a = m - c\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + V[>]\n}\n"
    "[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {\n"
    "    c = 𝑑𝑢𝑖𝑛𝑣(TERM)\n}\n"
)

# a discounting stage that declares no arrival perch, whose decision value
# `V` is the value it exports
DISC_ENTRY = (
    "@stage: disc\n"
    "β : (0,1)\n"
    "[id=dcsn_to_cntn, (k : ℝ₊) : !dcsn -> (k_next : ℝ₊) : !cntn] {\n"
    "    k_next = k\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = β*V[>]\n}\n"
)

# a discounting stage that keeps its arrival builder, `V[<] = V`, and states
# the derivative of its decision value: the stated derivative passes through
# the arrival builder, whose line is an identity of the value and whose law
# between the perches is the identity in the coordinate (D3, the plan's P1)
DISC_ARRIVAL = (
    "@stage: disc\n"
    "β : (0,1)\n"
    "𝑤(k : ℝ₊) := k^(-2)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n"
    "    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d) : !dcsn -> (k_next : ℝ₊) : !cntn] {\n"
    "    k_next = k_d\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = β*V[>]\n"
    "    D_{k_d}V = β*𝑤(k_d)\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
    "    V[<] = V\n}\n"
)


def _two_stage_trellises(term, representation=None, disc_text=DISC_ENTRY):
    """The two orders of a two-period trellis of `CONS_ENTRY`, reading
    `term`, and the discounting stage `disc_text`, the consumption stage's
    continuation joined to the discounting stage's entry state `k` and the
    discounting stage's continuation to the consumption stage's decision
    state `m`; with `representation`, that method is bound on the discounting
    stage's value builder, at its Evaluation."""
    from conftest import stage_from_text

    from bellman.factory.trellis import elaborate_trellis

    found = []
    for order in (("cons", "disc"), ("disc", "cons")):
        cons = stage_from_text(CONS_ENTRY.replace("TERM", term), "cons.bl")
        disc = stage_from_text(disc_text, "disc.bl")
        if representation is not None:
            disc.methodize({"methods": [{"on": "cntn_to_dcsn", "method": representation}]})
        stages = {"cons": cons, "disc": disc}
        within = {"cons.a": "disc.k"} if order[0] == "cons" else {"disc.k_next": "cons.m"}
        between = {"k_next": "m"} if order[0] == "cons" else {"a": "k"}
        period = {"stages": {key: stages[key] for key in order}, "connectors": [within]}
        found.append(
            elaborate_trellis({"periods": [period, dict(period)], "inter_connectors": [between]})
        )
    return found


def test_item_4_derivative_missing_is_reported_in_both_orders_and_silent_where_the_value_is_represented():
    """`derivative_missing` answers, in both orders of the two-stage trellis,
    one `derivative-missing` diagnostic, naming the stage whose value
    carries no derivative, its value and the coordinate: the discounting
    stage's `V = β*V[>]` passes the value through under its identity law
    (D3), so the requirement of the later period's consumption stage, whose
    continuation the inter-period connector joins to the earlier period
    (`inter_connectors[0]` joins `periods[1]` to `periods[0]`), moves along
    the next route to the earlier period's consumption stage, whose decision
    value carries none, which is the one reported; the earlier period's own
    reading reaches the trellis's end and falls to the terminal data
    (amendment §5.3, D3, D5, D6; plan R5). Nothing is reported where `!pchip`, whose row
    evaluates the first derivative, is bound on the discounting stage's value
    builder. The stages declare no arrival perch, so the trellis joins each
    continuation to the next stage's decision state and reads its decision
    value as the value it exports (P2), and every route is certified on the
    values alone."""
    from bellman.factory.connections import connection_report
    from bellman.trellis import derivative_missing

    for trellis in _two_stage_trellises("D_{a}V[>]"):
        routes = connection_report(trellis).routes
        assert [route.status for route in routes] == ["certified"] * len(routes)
        found = derivative_missing(trellis)
        assert [item.rule for item in found] == ["derivative-missing"]
        [item] = found
        assert item.address == "periods[0].stages['cons']"
        assert "stage 'cons'" in item.message and "pass-through of disc" in item.message
        assert "`D_{a}V[>]`" in item.message
        assert item.candidates == ("cons:function:dcsn:V", "m")
    for trellis in _two_stage_trellises("D_{a}V[>]", representation="!pchip"):
        assert derivative_missing(trellis) == ()
    # the stated derivative of the decision value passes through an arrival
    # builder whose line is an identity of the value, under the identity law
    # `k_d = k` (D3, P1), so the reading is met
    for trellis in _two_stage_trellises("D_{a}V[>]", disc_text=DISC_ARRIVAL):
        assert derivative_missing(trellis) == ()


def test_item_4b_a_second_derivative_read_of_a_value_represented_by_linear_is_reported():
    """A block that reads the second derivative `D_{a}D_{a}V[>]` of a value
    represented by `!Linear`, whose row evaluates the first derivative alone,
    is reported under `derivative-missing` and not silently met, at the
    stage the pass-through of D3 carries the requirement to (amendment
    §5.2; plan §2.5, Matsya's test (h)); with `!pchip` on the value the
    reading is met. The test writes the term as `D_{a}(D_{a}V[>])`, since
    the grammar's field alternative admits no nested call after the subscript
    (decisions MB-B7)."""
    from bellman.trellis import derivative_missing

    for trellis in _two_stage_trellises("D_{a}(D_{a}V[>])", representation="!Linear"):
        found = derivative_missing(trellis)
        assert [item.rule for item in found] == ["derivative-missing"]
        assert all("`D_{a}D_{a}V[>]`" in item.message for item in found)
        # the discounting stage's value, represented by `!Linear`, evaluates no
        # second derivative and passes the requirement through (D3) to the
        # second period's consumption stage, which is reported
        assert all(item.candidates == ("cons:function:dcsn:V", "m", "m") for item in found)
    for trellis in _two_stage_trellises("D_{a}(D_{a}V[>])", representation="!pchip"):
        assert derivative_missing(trellis) == ()
