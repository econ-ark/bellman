"""The acceptance file of unit U3a of the build of specification 0.7, the
catalogue and the settings: one test for each item of the unit's brief,
named `test_item_<n>_<claim>`, on the corpus stages of `conftest.py` and on
stage texts written in the new form. A stage text that reads declared
settings is unioned with its methods file by the fixture `with_addition`,
and a methods source is a `.bl` addition, a mapping holding its text and its
origin. The refusals of the five rules the unit adds stand in the refusal
file, provoked from the package's own examples.
"""
from __future__ import annotations

import pytest

from bellman.factory.period_parameters import period_settings, shared_parameters
from bellman.factory.trellis import positions
from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import INVERSE_EULER, TWO_NODES
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import method_types
from bellman.syntax.source import to_source
from bellman.trellis import configure_trellis

# the inverse Euler form of the consumption stage with the endogenous grid
# method, its exogenous grid of savings and its handler written in the policy
# block's header, and the decision value's representation with its grid of
# resources in the value builder's header; the policy's Evaluation writes no
# grid, since the method computes its knots
EGM_STAGE = INVERSE_EULER.replace(
    "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {",
    "[id=policy, method : !egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn\n"
    "    | grid : !Cartesian(a=(a_min, a_max, n_a, !expmult(nest=grid_phi)))\n"
    '    | handler : "cons-port:egm" | evaluate.method : !Linear] {',
).replace(
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {",
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn\n"
    '    | evaluate.method : !Linear(extrap="clamp")\n'
    "    | evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))] {",
)

# the settings the two grids read, declared with their sets as a methods
# file declares them (the writer's sheet §6)
GRID_SETTINGS = """@methods: t
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : ℝ₊           :: ["lower bound of the savings grid"]
a_max : ℝ₊           :: ["upper bound of the savings grid"]
grid_phi : ℝ₊₊       :: ["nesting factor of the exponentially spaced savings grid"]
n_m : ℕ              :: ["number of points of the grid of resources"]
m_min : ℝ₊           :: ["lower bound of the grid of resources"]
m_max : ℝ₊           :: ["upper bound of the grid of resources"]
"""

VALUES = {"n_a": 30, "a_min": 0.0, "a_max": 20.0, "grid_phi": 3.0, "n_m": 50, "m_min": 0.1, "m_max": 10.0}

# the two-node stage with value function iteration on the backward decision
# builder, whose grid names the decision state by a spaced factor and the
# control by its feasible set with a count, the first node represented on a
# listed node set and the quadrature nodes of its expectation, and the
# quadrature at both nodes with one node count per shock
TWO_NODES_STAGE = TWO_NODES.replace(
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {",
    "[id=cntn_to_dcsn, method : !vfi(tol=tol_v), (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn\n"
    "    | grid : !Cartesian(k_d=(k_min, k_max, n_k), c=(Γ, n_c))\n"
    "    | first.evaluate.method : !Linear | first.evaluate.grid : !Cartesian(k_d=K_nodes, y=E_y_z)\n"
    "    | E_y_z.method : !gauss_hermite(n_y=n_y_nodes, n_z=n_z_nodes)] {",
)

TWO_NODES_SETTINGS = """@methods: two_nodes
tol_v : ℝ₊₊          :: ["tolerance of value function iteration"]
k_min : ℝ            :: ["lower bound of the capital grid"]
k_max : ℝ            :: ["upper bound of the capital grid"]
n_k : ℕ              :: ["number of points of the capital grid"]
n_c : ℕ              :: ["number of candidate shares"]
n_y_nodes : ℕ        :: ["quadrature nodes of the first shock"]
n_z_nodes : ℕ        :: ["quadrature nodes of the second shock"]
K_nodes : ℝ × ℝ × ℝ  :: ["the nodes of the first node's capital grid"]
"""

TWO_NODES_VALUES = {"tol_v": 1e-6, "k_min": -1.0, "k_max": 2.0, "n_k": 12, "n_c": 5, "n_y_nodes": 7, "n_z_nodes": 5,
                    "K_nodes": [-0.5, 0.5, 1.5]}


def addition(stage, *entries):
    """A methods source of the stage `stage`: an addition holding the typing
    entries `entries`, as a mapping of its text and its origin."""
    return {"text": f"@methods: {stage}\n" + "".join(f"{entry}\n" for entry in entries),
            "origin": f"{stage}.methods.bl"}


def argument(components, name):
    """The value of the keyword argument `name` of the method word typed at a
    place, as the stage file writes it."""
    return next(to_source(keyword.value) for keyword in components.method.arguments if keyword.key == name)


# --- item 1: the rows take keyword arguments ---


def test_item_1_a_row_lists_the_keywords_the_package_reads_and_admits_further_keywords(port):
    row = method_types["!monte_carlo"]
    assert row is method_types["!monte-carlo"]
    assert [(name, keyword.kind, keyword.required) for name, keyword in row.keywords.items()] == [
        ("n_paths", "positive integer", True), ("seed", "seed", False)]
    assert [(name, keyword.required) for name, keyword in method_types["!vfi"].keywords.items()] == [
        ("tol", False), ("n_c", False)]
    with pytest.raises(ConstructionError, match="without the keyword n_paths") as refused:
        copy_native(port).methodize(addition("port", "dcsn_to_cntn.method : !monte_carlo"))
    assert refused.value.rule == "method-admission"
    # a keyword the row does not list is admitted and kept for the handler,
    # and the hyphenated tag's row is read from the underscore spelling
    bound = copy_native(port).methodize(addition(
        "port", "n_sim : ℕ", "n_Ψ_nodes : ℕ", "n_θ_nodes : ℕ",
        'dcsn_to_cntn.method : !monte_carlo(n_paths=n_sim, antithetic="yes")',
        "E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)",
    ))
    assert method_types["!" + bound.methods["dcsn_to_cntn"].method.name] is method_types["!monte-carlo"]
    assert argument(bound.methods["dcsn_to_cntn"], "antithetic") == '"yes"'
    assert "antithetic" not in row.keywords
    assert method_types["!" + bound.methods["E_Ψ_θ"].method.name] is method_types["!gauss-hermite"]
    configured = bound.configure({"settings": {"n_sim": 100, "n_Ψ_nodes": 7, "n_θ_nodes": 5}})
    assert list(configured.settings) == ["n_sim", "n_Ψ_nodes", "n_θ_nodes"]
    assert str(configured.settings["n_Ψ_nodes"]).endswith("by !gauss_hermite")


# --- item 2: the grid, one kind with four factor shapes ---


def test_item_2_the_four_factor_shapes_bind_and_configure(with_addition):
    stage = with_addition(TWO_NODES_STAGE, TWO_NODES_SETTINGS)
    vfi, node = stage.methods["cntn_to_dcsn"], stage.methods["cntn_to_dcsn.first.evaluate"]
    assert (vfi.word, to_source(vfi.grid)) == ("!vfi", "!Cartesian(k_d=(k_min, k_max, n_k), c=(Γ, n_c))")
    assert (node.word, to_source(node.grid)) == ("!Linear", "!Cartesian(k_d=K_nodes, y=E_y_z)")
    # the entry in the block's header names the block's occurrences (F3)
    assert str(stage.methods["cntn_to_dcsn.E_y_z"]) == "!gauss_hermite(n_y=n_y_nodes, n_z=n_z_nodes)"
    configured = stage.configure({"settings": TWO_NODES_VALUES})
    assert configured.settings.n_c == 5
    rows = {(row["name"], row["read at"], row["grid"]) for row in configured.settings.list()}
    assert ("n_c", "cntn_to_dcsn", "!Cartesian") in rows
    assert ("n_k", "cntn_to_dcsn", "!Cartesian") in rows
    assert ("tol_v", "cntn_to_dcsn", "") in rows
    for name, bad, words in (("n_c", 1, "count 1"), ("K_nodes", [0.5, -0.5, 1.5], "strictly increasing")):
        with pytest.raises(ConstructionError, match=words) as refused:
            stage.configure({"settings": {**TWO_NODES_VALUES, name: bad}})
        assert refused.value.rule == "grid-bounds"


def test_item_2_the_rows_name_the_states_their_grid_lies_on_and_the_default_supplies_it(with_addition):
    assert (method_types["!egm"].grid, method_types["!Linear"].grid, method_types["!gauss-hermite"].grid) == (
        "cntn", "output", None)
    assert "on the states of the continuation perch" in str(method_types["!egm"])
    stage = with_addition(EGM_STAGE, GRID_SETTINGS)
    egm = stage.methods["policy"]
    assert (egm.word, egm.handler, to_source(egm.grid)) == (
        "!egm", "cons-port:egm", "!Cartesian(a=(a_min, a_max, n_a, !expmult(nest=grid_phi)))")
    # the policy's representation writes no grid entry: the default, the
    # knots the method computes, supplies it
    assert stage.methods["policy.evaluate"].grid is None
    value = stage.methods["cntn_to_dcsn.evaluate"]
    assert (value.word, to_source(value.grid)) == ("!Linear", "!Cartesian(m=(m_min, m_max, n_m))")
    assert argument(value, "extrap") == '"clamp"'
    configured = stage.configure({"settings": VALUES})
    assert str(configured.settings["grid_phi"]) == (
        "grid_phi = 3.0 : ℝ₊₊, read at policy by !egm for its grid !Cartesian")


def test_item_2_the_sparse_kind_is_reserved_by_name_and_refused_as_not_built(elaborate_text):
    with pytest.raises(ConstructionError, match="reserved by name and not built") as refused:
        elaborate_text(EGM_STAGE.replace("!Cartesian(a=", "!Smolyak(a="))
    assert refused.value.rule == "syntax"


# --- item 3: the settings ---


def test_item_3_a_declared_setting_is_listed_by_settings_and_never_by_par(with_addition):
    stage = with_addition(EGM_STAGE, GRID_SETTINGS)
    assert list(stage.par) == []
    assert list(stage.settings) == list(VALUES)
    assert str(stage.settings["n_a"]) == (
        "n_a : ℕ, unbound, read at policy by !egm for its grid !Cartesian")
    assert "settings" in stage.view() and "n_a : ℕ" in stage.view()
    configured = stage.configure({"settings": {**VALUES, "n_k": 8}})
    rows = configured.settings.list()
    assert [(row["name"], to_source(row["domain"]), row["value"]) for row in rows[:2]] == [
        ("n_a", "ℕ", 30), ("a_min", "ℝ₊", 0.0)]
    # a value the source supplies for a name no file declares is bound and
    # listed with no reader, so that nothing is dropped
    assert (rows[-1]["name"], rows[-1]["domain"], rows[-1]["read at"]) == ("n_k", None, "")
    assert configured.settings.n_a == 30 and list(configured.par) == []


def test_item_3_configure_refuses_at_the_declaration_a_value_outside_the_set_or_missing(with_addition):
    for values, rule, line, words in (
        ({**VALUES, "a_min": -1.0}, "setting-outside-set", 3, ("'a_min'", "-1.0", "ℝ₊")),
        ({**VALUES, "n_a": 2.5}, "setting-outside-set", 2, ("'n_a'", "2.5", "ℕ")),
        ({name: value for name, value in VALUES.items() if name != "n_m"}, "setting-unvalued", 6, ("'n_m'", "`n_m: <value>`")),
    ):
        with pytest.raises(ConstructionError) as refused:
            with_addition(EGM_STAGE, GRID_SETTINGS).configure({"settings": values})
        error = refused.value
        assert (error.rule, error.file, error.line, error.address) == (rule, "methods.bl", line, f"methods.bl:{line}")
        assert all(word in error.message for word in words), (words, error.message)


def test_item_3_a_name_declared_in_two_stages_of_one_period_is_one_setting(with_addition, elaborate_text):
    first = with_addition(EGM_STAGE, GRID_SETTINGS)
    second = with_addition(EGM_STAGE, GRID_SETTINGS)
    shared = shared_parameters({"a": first, "b": second}, "periods[0]")
    assert (shared["n_a"].kind, shared["n_a"].keys, to_source(shared["n_a"].domain)) == ("setting", ("a", "b"), "ℕ")
    with pytest.raises(FactoryError, match="n_a") as refused:
        shared_parameters({"a": first, "b": with_addition(EGM_STAGE, GRID_SETTINGS.replace("n_a : ℕ", "n_a : [0, 1]"))})
    assert refused.value.rule == "period-parameter-agreement"
    # the name declared as a parameter of the model in one stage and as a
    # setting in another names two things, which is refused
    parameter = elaborate_text(INVERSE_EULER.replace("@stage: t\n", "@stage: t\nn_a : ℕ\n"))
    with pytest.raises(FactoryError, match="as a parameter in one and as a setting in another"):
        shared_parameters({"a": first, "b": parameter})


def test_item_3_a_shared_setting_is_valued_once_for_the_period(with_addition):
    # two occurrences of one period, stage objects placed by hand, each
    # configured by its own settings: one value of the shared setting agrees,
    # two differing values are refused as a parameter's are, and the refusal
    # names the position and the kind
    first = with_addition(EGM_STAGE, GRID_SETTINGS).configure({"settings": VALUES})
    second = with_addition(EGM_STAGE, GRID_SETTINGS).configure({"settings": {**VALUES, "n_a": 40}})

    def period(*stages):
        return {"periods": [{"stages": dict(zip("ab", stages)), "connectors": []}], "inter_connectors": []}

    agreed = period(first, with_addition(EGM_STAGE, GRID_SETTINGS).configure({"settings": VALUES}))
    assert [place.stage.settings.n_a for place in positions(configure_trellis(agreed, agreed))] == [30, 30]
    differing = period(first, second)
    with pytest.raises(FactoryError, match="supply the setting 'n_a' with the values 30 and 40") as refused:
        configure_trellis(differing, differing)
    assert refused.value.rule == "period-parameter-agreement"
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['b']", "Binding kind: settings"]
    # a record whose settings source supplies no value for the shared setting
    # takes the period's, as a record's calibration takes a shared parameter's
    unvalued = with_addition(EGM_STAGE, GRID_SETTINGS)
    record = {"settings": {name: value for name, value in VALUES.items() if name != "n_a"}}
    found = [(0, "a", "periods[0].stages['a']", first), (0, "b", "periods[0].stages['b']", record)]
    supplied = period_settings(found, {0: {"a": first, "b": unvalued}})
    assert supplied[0, "a"] is None and supplied[0, "b"]["n_a"] == 30
    assert unvalued.configure({"settings": supplied[0, "b"]}).settings.n_a == 30
