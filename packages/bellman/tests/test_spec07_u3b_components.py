"""The acceptance file of unit U3b of the build of specification 0.7, the
classifier components, the places and the two levels: one test for each of
the acceptance items 1 to 3 of §U3 of the implementation specification that
this part builds, named `test_item_<n>_<claim>`, each the stage text plus the
public query plus the expected printed value, on the corpus stages of
`conftest.py` and on inline specimens from the case studies: buffer-stock's
policy block with the three lines of the endogenous grid method and
`policy.method : !egm`, the value builder of durables' `Port2` with `!vfi`
and a derivative line, and a two-state value with two derivative terms. Item
4 of §U3, the settings declared in a methods file, belongs to the catalogue
part of the unit. The later checks here cover grids with no method,
configured values when an addition is replaced, and signature equality.
"""
from __future__ import annotations

import pytest
from conftest import ROOT

from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage

# the entries and the lines of the buffer-stock case study's addition, with
# the declarations of the settings its grids read
BUFFER_STOCK_ADDITION = """@methods: buffer_stock
n_ψ_nodes : ℕ
n_ξ_nodes : ℕ
a_min : ℝ₊
a_max : ℝ₊
n_a : ℕ
k_min : ℝ₊
k_max : ℝ₊
n_k : ℕ

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | evaluate.method : !Linear] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
    | evaluate.method : !Linear
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
"""

# the entries and the derivative line of durables' `Port2` case study, whose
# value builder takes `!vfi` and gains a derivative line
PORT2_ADDITION = """@methods: Port2
n_Ψ_nodes : ℕ
n_θ_nodes : ℕ
k_min : ℝ₊
k_max : ℝ₊
n_k : ℕ

[id=cntn_to_dcsn] {
    D_{k_d}V = E_{Ψ,θ}(D_{m_next}V[>]*(ς*Ψ + (1-ς)*R))   :: [id=marginal]
}

cntn_to_dcsn.method : !vfi
cntn_to_dcsn.handler : "cons-port:share_search"
cntn_to_dcsn.grid : !Cartesian(k_d=(k_min, k_max, n_k, !expmult))
cntn_to_dcsn.value.E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)
cntn_to_dcsn.marginal.E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)
cntn_to_dcsn.evaluate[V].method : !Linear
cntn_to_dcsn.evaluate[V].grid : !Cartesian(k_d=(k_min, k_max, n_k, !expmult))
"""

# a value with two state coordinates whose block states a derivative in each,
# each term represented by an entry of its own, written in the stage file; the
# settings the grid names are declared by the addition
TWO_STATE_SETTINGS = "@methods: two\nx_min : ℝ\nx_max : ℝ\nn_x : ℕ\ny_min : ℝ\ny_max : ℝ\nn_y : ℕ\n"
TWO_STATE = """@stage: two
β : (0,1)
[id=arvl_to_dcsn, (x : ℝ, y : ℝ) : !arvl -> (x_d : ℝ, y_d : ℝ) : !dcsn] {
    x_d = x
    y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d) : !dcsn -> (a : ℝ, b : ℝ) : !cntn] {
    a = x_d
    b = y_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn
    | evaluate[V].method : !Linear
    | evaluate[D_{x_d}V].method : !pchip
    | evaluate[D_{x_d}V].grid : !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))
    | evaluate[D_{y_d}V].method : !Linear] {
    V = β*V[>]
    D_{x_d}V = β*D_{a}V[>]
    D_{y_d}V = β*D_{b}V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""

PORT2 = "applications/durables/declaration/stages/Port2/Port2.bl"
BUFFER_STOCK_METHODS = "applications/buffer-stock/declaration/stages/buffer_stock/methods.bl"
PENSION_CHOICE = "packages/bellman/tests/additions/new-applications/B-retirement-choice-pension"


def addition(text, origin="methods.bl"):
    return {"text": text, "origin": origin}


def test_item_1_every_entry_binds_at_the_place_its_check_records(buffer_stock, cons_methodized):
    """The buffer-stock addition binds its entries at the places the case
    study's `check.md` records, and `methods`, `places()` and `signature()`
    answer them; the cons addition binds likewise."""
    stage = buffer_stock.methodize(addition(BUFFER_STOCK_ADDITION))
    assert list(stage.methods) == [
        "dcsn_to_arvl.E_ψ_ξ",
        "dcsn_to_arvl.evaluate",
        "policy",
        "policy.evaluate",
    ]
    assert str(stage.methods["policy"]) == '!egm   !Cartesian(a=(a_min, a_max, n_a))'
    assert str(stage.methods["dcsn_to_arvl.E_ψ_ξ"]) == "!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)"
    assert str(stage.methods["dcsn_to_arvl.evaluate"]) == (
        "!Linear   !Cartesian(k=(k_min, k_max, n_k))"
    )
    assert str(stage.methods["policy.evaluate"]) == "!Linear"
    addresses = [row["address"] for row in stage.places()]
    assert {"policy", "policy.evaluate", "policy.evaluate[c]", "dcsn_to_arvl.E_ψ_ξ",
            "dcsn_to_arvl.value.E_ψ_ξ", "dcsn_to_arvl.marginal.E_ψ_ξ", "dcsn_to_arvl.evaluate",
            "dcsn_to_arvl.evaluate[V[<]]", "dcsn_to_arvl.evaluate[D_{k}V[<]]"} <= set(addresses)
    # the signature prints the two components after the field component
    printed = str(stage.builder.policy.signature()).splitlines()
    assert printed[-2:] == [
        "method     !egm",
        "grid       !Cartesian(a=(a_min, a_max, n_a))",
    ]
    # the block-level head names every occurrence of the operator in the block
    arrival = stage.builder["dcsn", "arvl"]
    expectation = arrival.primitives["value:Expectation:1"]
    assert list(expectation.methods) == ["dcsn_to_arvl.E_ψ_ξ"]
    assert list(arrival.methods) == ["dcsn_to_arvl.E_ψ_ξ", "dcsn_to_arvl.evaluate"]
    # the cons addition of the fixtures binds its four places, the handler
    # beside the method where one is written (D2)
    assert list(cons_methodized.methods) == [
        "arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn.evaluate", "policy",
    ]
    assert str(cons_methodized.methods["dcsn_to_cntn"]) == '"cons-port:transition_fwd"'
    assert str(cons_methodized.methods["policy"]) == (
        '!egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"'
    )


def test_item_2_the_two_levels_of_a_solution_method_with_rows(buffer_stock, elaborate_text):
    """With `!egm` in the component the operative policy holds the method's
    rows and `stage.declared`, the stage file elaborated alone, the
    maximization; an appended derivative line stands in the operative
    builder; with `!vfi` and no row both levels hold the declared lines;
    without a solution method an appended line is an authored line, refused
    where it defines a field twice."""
    stage = buffer_stock.methodize(addition(BUFFER_STOCK_ADDITION))
    # the candidate line `c[>] = …` is an alias the fold folds into the grid
    # line's row, so the method's three lines form two rows and the Evaluation
    assert [key for key in stage.builder.policy.list()] == [
        "g_cntn_to_dcsn:Aggregation", "cons_choice:Pullback", "Evaluation",
    ]
    assert [key for key in stage.declared.policy.list()] == [
        "Pullback", "optimality:Aggregation", "optimality:Argmax", "Evaluation",
    ]
    # the declared level is the stage file elaborated alone (specification
    # 0.7 §4 rule 6), so its signature carries no component the addition types
    assert "method" not in str(stage.declared.policy.signature())
    assert str(stage.builder.policy.signature()).splitlines()[-2] == "method     !egm"
    assert [c.condition for c in stage.obligations() if c.condition == "egm-eligibility"]
    # the appended derivative line stands in the operative value builder, and
    # the declared one holds the stage file's lines alone
    operative, declared = stage.builder["cntn", "dcsn"], stage.declared["cntn", "dcsn"]
    assert [key for key in operative.list()] == ["Pullback", "Aggregation", "Evaluation"]
    assert "D_{m}𝑉(m) = 𝑑𝑢(𝑐(m))" in str(operative.denote())
    assert [key for key in declared.list()] == ["Pullback", "Aggregation", "Evaluation"]
    assert "D_{m}𝑉(m)" not in str(declared.denote())
    # `!vfi` with no row leaves the declared lines at the operative level
    port2 = elaborate_text((ROOT / PORT2).read_text(encoding="utf-8"), PORT2)
    port2.methodize(addition(PORT2_ADDITION, "methods.Port2.bl"))
    assert str(port2.methods["cntn_to_dcsn"]) == (
        '!vfi   !Cartesian(k_d=(k_min, k_max, n_k, !expmult))   "cons-port:share_search"'
    )
    assert list(port2.builder["cntn", "dcsn"].list()) == list(port2.declared["cntn", "dcsn"].list())
    assert "cntn_to_dcsn.evaluate[D_{k_d}V]" in [row["address"] for row in port2.places()]
    # a block without a solution method reads an appended line as authored
    with pytest.raises(ConstructionError) as refused:
        buffer_stock.methodize(
            addition("@methods: buffer_stock\n[id=policy] {\n    c = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>]) :: [id=x]\n}\n")
        )
    assert refused.value.rule == "defined-once"
    # a block of an initial diagram reads the lines its own box holds: the
    # derivative line the application's addition appends is reached from
    # the block by its key, and its card prints the line at its position in
    # the addition, while the stage file's line keeps its own position
    stage = buffer_stock.methodize(
        addition((ROOT / BUFFER_STOCK_METHODS).read_text(encoding="utf-8"), BUFFER_STOCK_METHODS)
    )
    block = stage.initial.backward["cntn_to_dcsn"]
    assert list(block.list().names) == ["cntn_to_dcsn.value", "cntn_to_dcsn.marginal"]
    lines = (ROOT / BUFFER_STOCK_METHODS).read_text(encoding="utf-8").splitlines()
    number, = [n for n, line in enumerate(lines, 1) if "D_{m}V = 𝑑𝑢(c)" in line]
    appended = f"Source  methods.bl\n  {number}  D_{{m}}V = 𝑑𝑢(c)"
    assert appended in str(block["marginal"].denote())
    card = str(block.denote())
    assert "Source  buffer_stock.bl\n  35  V = 𝑢(c) + β*V[>]" in card and appended in card
    assert "D_{m}V" not in str(stage.declared["cntn", "dcsn"].denote())
    # the two builders an addition adds whole are blocks of the initial
    # diagrams and list their lines (unit U2, item 5)
    folder = ROOT / PENSION_CHOICE
    pension = elaborate_stage(
        load_stage(folder / "stage/choice.bl", [folder / "additions/pension_choice.bl"])
    )
    assert list(pension.initial.backward["dcsn_to_arvl"].list().names) == [
        "dcsn_to_arvl.survival_value", "dcsn_to_arvl.marginal_assets", "dcsn_to_arvl.marginal_pension",
    ]
    assert list(pension.initial.forward["arvl_to_dcsn"].list().names) == [
        "arvl_to_dcsn.assets", "arvl_to_dcsn.pension",
    ]


def test_item_3_a_refined_grid_binds_one_place_per_derivative_term(with_addition):
    """`evaluate[D_{k}V[<]].grid` on a value with two state derivatives binds
    one place per term, each with its own basis and grid (F47, D4)."""
    stage = with_addition(TWO_STATE, TWO_STATE_SETTINGS)
    assert list(stage.methods) == [
        "cntn_to_dcsn.evaluate[V]",
        "cntn_to_dcsn.evaluate[D_{x_d}V]",
        "cntn_to_dcsn.evaluate[D_{y_d}V]",
    ]
    assert str(stage.methods["cntn_to_dcsn.evaluate[D_{x_d}V]"]) == (
        "!pchip   !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))"
    )
    assert str(stage.methods["cntn_to_dcsn.evaluate[D_{y_d}V]"]) == "!Linear"
    listed = [row["address"] for row in stage.places() if row["address"].startswith("cntn_to_dcsn.evaluate")]
    assert listed == [
        "cntn_to_dcsn.evaluate",
        "cntn_to_dcsn.evaluate[V]",
        "cntn_to_dcsn.evaluate[D_{x_d}V]",
        "cntn_to_dcsn.evaluate[D_{y_d}V]",
    ]
    evaluation = stage.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Evaluation"]
    assert str(evaluation.signature()).splitlines()[2:] == [
        "method     !Linear  [V]",
        "method     !pchip  [D_{x_d}V]",
        "grid       !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))",
        "           [D_{x_d}V]",
        "method     !Linear  [D_{y_d}V]",
    ]


def test_a_grid_without_a_method_binds_and_checks_its_coordinates(elaborate_text):
    text = TWO_STATE.replace(
        "    | evaluate[D_{x_d}V].grid : !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))\n",
        "",
    )
    stage = elaborate_text(text, "two.bl")
    grid = "cntn_to_dcsn.evaluate.grid : !Cartesian(x_d=(x_min, x_max, n_x))\n"
    stage.methodize(addition(TWO_STATE_SETTINGS + grid))
    assert str(stage.methods["cntn_to_dcsn.evaluate"]) == (
        "!Cartesian(x_d=(x_min, x_max, n_x))"
    )
    assert str(stage.methods["cntn_to_dcsn.evaluate[D_{x_d}V]"]).startswith("!pchip")
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(addition(TWO_STATE_SETTINGS + grid.replace("x_d=", "absent=")))
    assert (refused.value.rule, refused.value.address) == (
        "grid-coordinate", "cntn_to_dcsn.evaluate"
    )


@pytest.mark.parametrize("values, declarations, rule, corrected", [
    ({"n_k": -1}, "n_k : ℕ\n", "setting-outside-set", {"n_k": 3}),
    ({}, "n_k : ℕ\n", "setting-unvalued", {"n_k": 3}),
    (
        {"k_min": 0.1, "k_max": 1, "n_k": 1},
        "k_min : ℝ\nk_max : ℝ\nn_k : ℕ\n"
        "dcsn_to_arvl.evaluate.method : !Linear\n"
        "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n",
        "grid-bounds", {"n_k": 3},
    ),
    (
        {"tol": -1}, "tol : ℝ\ndcsn_to_arvl.method : !vfi(tol=tol)\n",
        "method-option-value", {"tol": 1e-6},
    ),
], ids=("outside-set", "unvalued", "grid-count", "method-option"))
def test_methodize_checks_previously_configured_values(
        elaborate_text, values, declarations, rule, corrected):
    path = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    stage = elaborate_text((ROOT / path).read_text(encoding="utf-8"), path)
    stage.configure(values)
    before = stage.encoding()
    source = addition("@methods: buffer_stock\n" + declarations)
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(source)
    assert refused.value.rule == rule
    assert stage.encoding() == before
    stage.configure(corrected)
    stage.methodize(source)
    assert dict(stage.bindings.settings) == {**values, **corrected}


def test_signature_equality_includes_the_typed_components(elaborate_text):
    path = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    stage = elaborate_text((ROOT / path).read_text(encoding="utf-8"), path)
    bare = stage.builder["dcsn", "arvl"].signature()
    source = addition("@methods: buffer_stock\ndcsn_to_arvl.method : !vfi\n")
    stage.methodize(source)
    typed = stage.builder["dcsn", "arvl"].signature()
    assert bare != typed
    assert not bare == typed
    assert (bare.inputs, bare.outputs) == (typed.inputs, typed.outputs)
    inputs, outputs = typed
    assert (inputs, outputs) == (typed.inputs, typed.outputs)
    stage.methodize(source)
    equal = stage.builder["dcsn", "arvl"].signature()
    assert equal == typed
    assert len({bare, typed, equal}) == 2
    with pytest.raises(AttributeError):
        typed.components = ()
