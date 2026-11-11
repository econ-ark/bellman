"""The acceptance file of AMD-MT-003, grids, function representations and
explicit solutions: one test for each of its six acceptance items, named
`test_item_<n>_<claim>`, each reading public stage queries and, for the
applications, their comparison functions; no test reads a private record.

1. Grid declarations, owned by unit A: the source forms of `!Cartesian`,
   `!Points` and `!Fibred` parsed and configured; an actual fibred joint grid
   with its points stated, against the family of grids indexed by the states
   that a feasible factor gives without `!Fibred`; the finite predicates
   written after `require` succeeding and refusing; equality in a valid
   context; partial obligations; the refusal of unsupported joint sampling;
   and the independent operator grid kept by `stage.methods`,
   `stage.places()` and the public views.
2. Representation admission, owned by unit B, whose preparation assertions
   unit D completes: late registration, the four data sources as public
   method records, typed refusals, preserved sites, opaque incoming
   functions, combined and successive selections with the removal of
   `!egm`, table alignment, the refusal of a representation grid at a closed
   form and full-domain obligations; then the actual preparation of an
   authored table and of a registered family that accepts only its own
   nodes from the selected pairs of the endogenous grid method.
3. Explicit and derived definitions, owned by units B and C: the compiled
   outputs of an explicit block and every exclusion, the formula-only block
   refused under `!egm` and `!time_iteration`; cycles, unavailable names,
   arithmetic failures and calibration overrides of derived definitions,
   and the negative derived lognormal scale refused through public
   calibration.
4. Perfect-foresight economics and numerics, owned by unit D.
5. Buffer stock and the consistency of the applications, owned by units D
   and D2: the log-mean μ_ξ of buffer stock derived from its parameters,
   and the entry points of the applications.
6. Inspection and regression evidence, owned by units D and E: the generated
   method and grid references and the executed notebook of the
   perfect-foresight application.

The test of item 2 calls `_selection_checks`, unit B's, and
`_preparation_checks`, unit D's; the test of item 3 calls `_explicit_checks`,
unit B's, and `_derived_checks`, unit C's; the test of item 5 calls
`_buffer_stock_checks`, unit D2's, and `_entry_point_checks`, unit D's;
the test of item 6 calls `_reference_checks`, unit E1's, and
`_notebook_checks`, unit D's. Each helper that reads fixtures takes the
test's `request` and reads them through it. The fixtures stand in the
labeled sections of `conftest.py`; permanent diagnostics stand in
`test_refusals.py` and public behavior in `test_behaviour.py`.
"""

import inspect
import json
import math

import mpmath
import numpy as np
import pytest

from bellman.native.hypergraphs import copy_native
from bellman.native.records import MethodOption
from bellman.refusal_examples import EXPLICIT_POLICY, TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage import admitted_methods, method_types
from bellman.stage.grids import same_grid
from bellman.stage.representations import (
    RepresentationFamily,
    families,
    register,
    unregister,
)
from conftest import (
    CORPUS,
    DERIVED_BUFFER_STOCK,
    GRID_VALUES,
    PERFECT_FORESIGHT_CALIBRATION,
    PERFECT_FORESIGHT_ORIGIN,
    ROOT,
    TWO_CONTROL_GRID_STAGE,
    TWO_STATE_GRID_STAGE,
    closed_form_check,
    methodized,
    perfect_foresight_text,
    stage_from_text,
)

# --- item 1, unit A ---


def test_item_1_points_and_fibred_grids_are_written_configured_constructed_and_checked(
    grid_stage,
):
    """The three grid forms parse, print as written and configure; the fibred
    grid of example E09 at a `!vfi` builder, with B = {1, 2}, Γ_c(m) = [0, m]
    and two control nodes, is the four pairs (1, 0), (1, 1), (2, 0) and
    (2, 2), which `kernels()` answers, while the same feasible factor written
    in `!Cartesian` without `!Fibred` is a family of grids indexed by the
    states, which `kernels()` reports as no one grid; the fibred grid's
    finite requirements hold or refuse as its points decide, an outer one on
    the joint grid and one inside the fibre on each fibre; an unknown and a
    contradictory requirement refuse; the equal supports of two constructions
    compare equal in a common valid context, supports whose exact nodes differ
    compare unequal, and a construction keeps distinct exact nodes that are
    one floating-point number, so that equality tells them apart; an omitted
    factor keeps its obligation,
    which no step refuses and the construction reports; a fibre of two
    controls reports unsupported joint sampling; and the methods, the places,
    the signature and the settings keep the grid at the operator that writes
    it."""
    vfi = "cntn_to_dcsn.method : !vfi\n"
    fibred = "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))"

    def grids(stage):
        return stage.builder["cntn", "dcsn"].kernels().grids

    # the three forms, each printed as written; the fibred grid of E09
    stage = grid_stage(vfi + f"cntn_to_dcsn.grid : {fibred}\n")
    assert str(stage.methods["cntn_to_dcsn"]) == f"!vfi   {fibred}"
    assert grids(stage) is None
    stage.configure(GRID_VALUES)
    (joint,) = grids(stage).values()
    assert (joint.word, joint.coordinates) == ("Fibred", ("m", "c"))
    assert joint.points == ((1, 0), (1, 1), (2, 0), (2, 2))
    for grid, declarations, settings, points in (
        ("!Cartesian(m=(m_lo, m_hi, n_m), require=!UniformCartesian)", "", {}, ((1,), (2,))),
        (
            "!Points(nodes=P, require=!UniformCartesian)",
            "P : ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊\n",
            {"P": [3.0, 1.0, 2.0, 1.0]},
            ((3,), (1,), (2,)),
        ),
        ("!Points(require=!Empty)", "", {}, ()),
    ):
        written = grid_stage(vfi + f"cntn_to_dcsn.grid : {grid}\n", declarations)
        assert str(written.methods["cntn_to_dcsn"]) == f"!vfi   {grid}"
        written.configure({**GRID_VALUES, **settings})
        assert grids(written)["cntn_to_dcsn"].points == points

    # a feasible factor written in !Cartesian without !Fibred is a family of
    # grids of the control indexed by the states, and no one grid; !Fibred
    # pairs the same factor with a base and gives the joint grid above
    family = grid_stage(
        vfi + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m), c=(Γ_c, n_c))\n"
    )
    family.configure(GRID_VALUES)
    (indexed,) = grids(family).values()
    assert indexed.diagnostic["rule"] == "grid-requirement"
    words = "a family of grids of the control c, one at each state, and no one grid"
    assert words in indexed.reason

    # the finite requirements, on the joint grid outside the fibre and on each
    # fibre inside it: the hull {1, 2} × {0, 1, 2} holds (1, 2)
    for grid, n_c, points in (
        (fibred[:-1] + ", require=!NonCartesian)", 2, joint.points),
        (
            "!Fibred(base=!Points(nodes=B), "
            "fibre=!Cartesian(c=(Γ_c, n_c), require=!UniformCartesian))",
            3,
            ((1, 0), (1, 0.5), (1, 1), (2, 0), (2, 1), (2, 2)),
        ),
        ("!Fibred(base=!Points, fibre=!Cartesian(c=(Γ_c, n_c)), require=!Empty)", 2, ()),
    ):
        holds = grid_stage(vfi + f"cntn_to_dcsn.grid : {grid}\n")
        holds.configure({**GRID_VALUES, "n_c": n_c})
        assert grids(holds)["cntn_to_dcsn"].points == points
    cartesian = grid_stage(vfi + f"cntn_to_dcsn.grid : {fibred[:-1]}, require=!Cartesian)\n")
    with pytest.raises(ConstructionError) as refused:
        cartesian.configure(GRID_VALUES)
    assert (refused.value.rule, refused.value.address) == ("grid-requirement", "cntn_to_dcsn")
    assert "{1, 2} × {0, 1, 2}, holds (1, 2)" in refused.value.message

    # an unknown and a contradictory requirement refuse where they are written
    for written, words in (
        ("require=!Bogus", "is no predicate word"),
        ("require=(!Empty, !Cartesian)", "contradict each other"),
    ):
        with pytest.raises(ConstructionError) as refused:
            grid_stage(vfi + f"cntn_to_dcsn.grid : !Points(nodes=B, {written})\n")
        assert (refused.value.rule, refused.value.line) == ("grid-requirement", 10)
        assert words in refused.value.message

    # equality in a common valid context: a product of factors and the same
    # points listed in another order, on (m, z)
    product = grid_stage(
        vfi
        + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m), z=(z_lo, z_hi, n_z))\n"
        + "cntn_to_dcsn.evaluate.method : !Linear\n"
        + "cntn_to_dcsn.evaluate.grid : !Points(nodes=P)\n",
        "P : X2 × X2 × X2 × X2\n",
        text=TWO_STATE_GRID_STAGE,
    )
    product.configure({**GRID_VALUES, "P": [[2.0, 1.0], [1.0, -1.0], [2.0, -1.0], [1.0, 1.0]]})
    found = grids(product)
    assert found["cntn_to_dcsn"].points == ((1, -1), (1, 1), (2, -1), (2, 1))
    assert same_grid(found["cntn_to_dcsn"], found["cntn_to_dcsn.evaluate"])
    product.configure({"P": [[2.0, 1.0], [1.0, -1.0], [2.0, -1.0], [2.0, 1.0]]})
    found = grids(product)
    assert not same_grid(found["cntn_to_dcsn"], found["cntn_to_dcsn.evaluate"])
    with pytest.raises(ValueError, match="common valid context"):
        same_grid(found["cntn_to_dcsn"], joint)

    # equality compares the exact constructions: the middle of three equally
    # spaced nodes from 0.1 to 0.2 is no floating-point number, and the points
    # that list its nearest one are another support
    spaced = grid_stage(vfi + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m))\n")
    spaced.configure({**GRID_VALUES, "m_lo": 0.1, "m_hi": 0.2, "n_m": 3})
    listed = grid_stage(vfi + "cntn_to_dcsn.grid : !Points(nodes=P)\n", "P : ℝ₊ × ℝ₊ × ℝ₊\n")
    listed.configure({**GRID_VALUES, "P": [0.1, 0.15000000000000002, 0.2]})
    assert not same_grid(grids(spaced)["cntn_to_dcsn"], grids(listed)["cntn_to_dcsn"])

    # distinct exact nodes that are one floating-point number remain distinct:
    # the middle of three nodes from 1 to 1.0000000000000002 has the nearest
    # floating-point number 1.0, and the grid of its two end nodes is another
    # support; the integers 2**53 and 2**53 + 1, one floating-point number,
    # are two points of a listed grid
    realized = {}
    for n_m in (3, 2):
        close = grid_stage(vfi + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m))\n")
        close.configure({**GRID_VALUES, "m_lo": 1.0, "m_hi": 1.0000000000000002, "n_m": n_m})
        realized[n_m] = grids(close)["cntn_to_dcsn"]
    assert len({point[0] for point in realized[3].points}) == 3
    assert len({float(point[0]) for point in realized[3].points}) == 2
    assert not same_grid(realized[3], realized[2])
    large = grid_stage(vfi + "cntn_to_dcsn.grid : !Points(nodes=P)\n", "P : ℝ₊ × ℝ₊\n")
    large.configure({**GRID_VALUES, "P": [2**53, 2**53 + 1]})
    assert grids(large)["cntn_to_dcsn"].points == ((2**53,), (2**53 + 1,))

    # an omitted factor keeps its obligation: no step refuses it, and the
    # construction reports it, for a grid and for the base of a fibred grid
    for entries in (
        "cntn_to_dcsn.evaluate.method : !Linear\n"
        "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m), "
        "require=!UniformCartesian)\n",
        vfi + "cntn_to_dcsn.grid : !Fibred(base=!Cartesian(m=(m_lo, m_hi, n_m)), "
        "fibre=!Cartesian(c=(Γ_c, n_c)))\n",
    ):
        partial = grid_stage(entries, text=TWO_STATE_GRID_STAGE)
        partial.configure(GRID_VALUES)
        (obligation,) = grids(partial).values()
        assert obligation.diagnostic["rule"] == "grid-requirement"
        assert "no factor for the coordinate z" in obligation.reason

    # a fibre of two controls, whose feasible sets are coupled
    coupled = grid_stage(
        vfi + "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), "
        "fibre=!Cartesian(c=(Γ_c, n_c), h=(Γ_h, n_c)))\n",
        text=TWO_CONTROL_GRID_STAGE,
    )
    coupled.configure(GRID_VALUES)
    (unsupported,) = grids(coupled).values()
    assert "joint sampling is unsupported" in unsupported.reason

    # the grid stands at the operator that writes it, in each public view
    assert "cntn_to_dcsn.evaluate" not in stage.methods
    assert {"address": "cntn_to_dcsn", "kind": "builder"} in [dict(row) for row in stage.places()]
    assert str(stage.builder["cntn", "dcsn"].signature()).splitlines()[-2:] == [
        "method     !vfi",
        f"grid       {fibred}",
    ]
    assert [
        (row["read at"], row["by"], row["grid"])
        for row in stage.settings.list()
        if row["name"] == "n_c"
    ] == [("cntn_to_dcsn", "!vfi", "!Fibred")]
    assert list(grids(stage)) == ["cntn_to_dcsn"]


# --- item 2: the selection checks, unit B ---


# the endogenous grid method of the consumption-savings stage with independent
# income, its grid of savings and its three lines, with no representation at
# the policy builder's Evaluation, and the envelope line of the decision value
CONS_SAVINGS_EGM = """n_a : ℕ
a_min : ℝ₊
a_max : ℝ₊
[id=policy, method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}
[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}
"""

# a representation at the policy builder's Evaluation of that stage, with a
# grid on the decision state w or with none
EVALUATION_GRID = """n_w : ℕ
w_min : ℝ₊
w_max : ℝ₊
policy.evaluate.grid : !Cartesian(w=(w_min, w_max, n_w))
"""


def _representation(word, grid=True):
    """The entries that type `word` at the policy builder's Evaluation of
    the consumption-savings stage, with the grid on w where `grid`."""
    return f"policy.evaluate.method : !{word}\n" + (EVALUATION_GRID if grid else "")


# the declarations of the settings of a grid on m at the Evaluation of the
# explicit policy builder of the perfect-foresight stage
EXPLICIT_GRID_SETTINGS = "n : ℕ\nlo : Xm\nhi : Xm\n"


def _explicit_policy(entries):
    """The text of the addition `EXPLICIT_POLICY` after its first line, the
    header of whose policy block also writes `entries`."""
    return EXPLICIT_POLICY.split("\n", 1)[1].replace(
        "[id=policy, policy.method : !explicit]",
        f"[id=policy, policy.method : !explicit | {entries}]",
    )


def _refusal(call):
    """The ConstructionError `call` raises."""
    with pytest.raises(ConstructionError) as refused:
        call()
    return refused.value


def _selection_checks(request):
    """The admission and selection parts of item 2 (build contract §3): the
    registry with its base families and a family registered late; the four
    data sources as public method records; typed refusals and the refusals
    of a source a family does not accept; the representation sites of a
    node; an incoming function read through its kernel argument alone;
    combined and successive selections with the removal of `!egm`; a
    version that keeps a removed family, and the family registered again,
    listed by the method table and bound at the Evaluation of an explicit
    policy builder; the authored table compared with its grid at
    configuration; the authored closed form bound at that Evaluation with no
    setting, and refused with a grid; and the obligations a representation
    owes on the domain where it is evaluated."""
    cons_savings_iid = request.getfixturevalue("cons_savings_iid")
    perfect_foresight = request.getfixturevalue("perfect_foresight")
    explicit = request.getfixturevalue("perfect_foresight_explicit")
    nodal = request.getfixturevalue("nodal_family")

    # the registry: the three base families with empty argument records,
    # rows of the method table, which reads the registry when it is read;
    # the fixture's family registered after the import has its row and is
    # admitted at an Evaluation; a second registration of a word, and a word
    # of another method, are refused
    assert list(families())[:3] == ["Linear", "pchip", "closed-form"]
    for tag in ("!Linear", "!pchip", "!closed_form"):
        assert (
            method_types[tag].kind == "representation" and dict(method_types[tag].keywords) == {}
        )
    assert (
        families()["Linear"].sources
        == families()["pchip"].sources
        == ("table", "pairs", "own nodes")
    )
    assert families()["closed-form"].sources == ("expression",)
    assert method_types["!closed_form"].grid is None and families()["closed-form"].grid is None
    assert "!nodal" in method_types
    assert "!nodal" in admitted_methods(cons_savings_iid, "policy.evaluate")
    with pytest.raises(ValueError, match="already names a registered"):
        register(nodal)
    with pytest.raises(ValueError, match="names the method !egm"):
        register(RepresentationFamily("egm", {}, ("own nodes",), derivatives=(), stored="nodes"))

    # the four sources: an authored table, the pairs of an !egm builder's
    # closing Evaluation, the expression of an !explicit builder and of a
    # declared function, and the family's own nodes
    table = stage_from_text(perfect_foresight_text(table=True), PERFECT_FORESIGHT_ORIGIN)
    table = methodized(
        table,
        "KN : ℝ × ℝ × ℝ\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : !Cartesian(k=KN)\n",
    )
    pairs = methodized(cons_savings_iid, _representation("Linear", grid=False), CONS_SAVINGS_EGM)
    own = methodized(
        cons_savings_iid,
        "n_b : ℕ\nb_min : ℝ₊\nb_max : ℝ₊\n"
        "dcsn_to_arvl.evaluate[V[<]].method : !Linear\n"
        "dcsn_to_arvl.evaluate[V[<]].grid : !Cartesian(b=(b_min, b_max, n_b))\n",
    )
    local = methodized(cons_savings_iid, "𝑢.method : !closed_form\n")
    assert [
        table.methods["dcsn_to_arvl.table.evaluate"].source,
        pairs.methods["policy.evaluate"].source,
        explicit.methods["policy.evaluate"].source,
        local.methods["𝑢"].source,
        own.methods["dcsn_to_arvl.evaluate[V[<]]"].source,
    ] == ["table", "pairs", "expression", "expression", "own nodes"]

    # typed refusals: a registered family's typed argument is required at
    # binding and checked at configuration; a source the family does not
    # accept is refused and selects no other case
    spline = register(
        RepresentationFamily(
            "spline",
            {
                "degree": MethodOption(
                    "positive integer", required=True, description="The degree of the spline."
                )
            },
            ("own nodes",),
            derivatives=(),
            stored="The coefficients of the spline.",
        )
    )
    try:
        refused = _refusal(
            lambda: methodized(cons_savings_iid, "dcsn_to_arvl.evaluate.method : !spline\n")
        )
        assert refused.rule == "method-admission" and "degree" in refused.message
        typed = methodized(
            cons_savings_iid, "d : ℤ\ndcsn_to_arvl.evaluate.method : !spline(degree=d)\n"
        )
        assert _refusal(lambda: copy_native(typed).configure({"settings": {"d": 0}})).rule == (
            "method-option-value"
        )
        copy_native(typed).configure({"settings": {"d": 3}})
    finally:
        unregister(spline.word)
    for stage, text, words in (
        (table, "dcsn_to_arvl.table.evaluate.method : !closed_form\n", "accepts no table"),
        (cons_savings_iid, "cntn_to_dcsn.evaluate.method : !closed_form\n", "supplies none"),
        (cons_savings_iid, "𝑑𝑢.method : !closed_form\n", "supplies none"),
    ):
        refused = _refusal(lambda: methodized(stage, text))
        assert refused.rule == "representation-source" and words in refused.message, text
    refused = _refusal(
        lambda: methodized(
            cons_savings_iid, _representation("closed_form", grid=False), CONS_SAVINGS_EGM
        )
    )
    assert (
        refused.rule == "representation-source" and "!egm selects policy pairs" in refused.message
    )

    # the sites of a node: its head and its Evaluation each admit a
    # representation, both concern the function the node computes, held by
    # its Evaluation, and the two together are refused
    two = stage_from_text(TWO_NODES)
    assert {"cntn_to_dcsn.first", "cntn_to_dcsn.first.evaluate"} <= {
        row["address"] for row in two.places()
    }
    for place in ("cntn_to_dcsn.first", "cntn_to_dcsn.first.evaluate"):
        held = methodized(two, f"{place}.method : !Linear\n")
        assert held.methods[place].source == "own nodes"
    refused = _refusal(
        lambda: methodized(
            two,
            "cntn_to_dcsn.first.method : !Linear\ncntn_to_dcsn.first.evaluate.method : !pchip\n",
        )
    )
    assert (
        refused.rule == "component-typed-twice"
        and "the node `cntn_to_dcsn.first`" in refused.message
    )

    # an incoming function is read through its kernel argument alone: the
    # closed form of the decision value's line reads the expression, and its
    # kernel takes the continuation value V[>] as a supplied argument,
    # whatever method represents the continuation value V[>]
    for word in ("Linear", "pchip"):
        opaque = methodized(
            cons_savings_iid,
            f"cntn_to_dcsn.value.method : !closed_form\ndcsn_to_arvl.evaluate.method : !{word}\n",
        )
        assert opaque.methods["cntn_to_dcsn.value"].source == "expression"
        kernel = opaque.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Aggregation"].kernel()
        assert "V≻" in dict(kernel.arguments)

    # combined and successive selections: the family that accepts only its
    # own nodes keeps its grid under !egm whether the two entries are read
    # together or the representation first, and the removal of !egm leaves it
    # bound; a family that reads the pairs refuses the grid both ways, and
    # without a grid reads the pairs, then its own nodes once !egm is removed
    nodal_egm = (_representation("nodal"), CONS_SAVINGS_EGM)
    linear_egm = (_representation("Linear"), CONS_SAVINGS_EGM)
    combined = methodized(cons_savings_iid, *nodal_egm)
    successive = methodized(cons_savings_iid, _representation("nodal"))
    successive = methodized(successive, *nodal_egm)
    assert str(combined.methods) == str(successive.methods)
    assert (
        combined.methods["policy.evaluate"].source,
        str(combined.methods["policy.evaluate"]),
    ) == ("own nodes", "!nodal   !Cartesian(w=(w_min, w_max, n_w))")
    successive = methodized(successive, _representation("nodal"))
    assert successive.methods["policy.evaluate"].source == "own nodes"
    first = methodized(cons_savings_iid, _representation("Linear"))
    for call in (
        lambda: methodized(cons_savings_iid, *linear_egm),
        lambda: methodized(first, *linear_egm),
    ):
        refused = _refusal(call)
        assert refused.rule == "grid-coordinate" and "reads the policy pairs" in refused.message
    bare = methodized(cons_savings_iid, _representation("Linear", grid=False), CONS_SAVINGS_EGM)
    assert bare.methods["policy.evaluate"].source == "pairs"
    bare = methodized(bare, _representation("Linear", grid=False))
    assert bare.methods["policy.evaluate"].source == "own nodes"

    # a version keeps the family it was bound with: after the family is
    # removed, the version answers and configures as bound, and a new
    # binding that names it is refused; registered again, the family is a
    # row of the method table and binds with its grid at the Evaluation of
    # the explicit policy builder, whose block writes c
    kept = methodized(cons_savings_iid, *nodal_egm)
    unregister(nodal.word)
    assert "!nodal" not in method_types and kept.methods["policy.evaluate"].source == "own nodes"
    kept.configure(
        {"settings": {"n_w": 5, "w_min": 0.1, "w_max": 5.0, "n_a": 5, "a_min": 0.0, "a_max": 5.0}}
    )
    assert _refusal(lambda: methodized(cons_savings_iid, *nodal_egm)).rule == "syntax"
    register(nodal)
    assert "!nodal" in method_types
    again = methodized(
        perfect_foresight,
        EXPLICIT_GRID_SETTINGS
        + _explicit_policy(
            "policy.evaluate.method : !nodal | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
        ),
    )
    held = again.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!nodal", "own nodes", None)

    # the authored table and its grid at configuration: equal finite
    # supports, the two signed zeros one point, establish the obligation;
    # a different support is refused, with no sorting and no tolerance
    table.calibrate(
        {
            "calibration": {
                **PERFECT_FORESIGHT_CALIBRATION,
                "K": [0.0, 1.0, 2.0],
                "Y": [1.0, 2.0, 4.0],
            }
        }
    )
    support = [
        (item.condition, item.status)
        for item in table.obligations()
        if item.condition == "table-grid-support"
    ]
    assert support == [("table-grid-support", "required")]
    table.configure({"settings": {"KN": [-0.0, 1.0, 2.0]}})
    assert [
        item.status for item in table.obligations() if item.condition == "table-grid-support"
    ] == ["established"]
    refused = _refusal(lambda: copy_native(table).configure({"settings": {"KN": [0.0, 1.0, 3.0]}}))
    assert refused.rule == "representation-source" and "exactly the table's finite support" in (
        refused.message
    )

    # the closed form authored at the Evaluation of the explicit policy
    # builder, whose block writes c, binds there from the expression and
    # not as the generated closed form; configured from an empty settings
    # source, the version lists no setting; written with a representation
    # grid, the closed form is refused
    closed = "policy.evaluate.method : !closed_form"
    authored = methodized(perfect_foresight, _explicit_policy(closed))
    held = authored.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!closed_form", "expression", None)
    authored.configure({"settings": {}})
    assert list(authored.settings.list()) == []
    gridded = EXPLICIT_GRID_SETTINGS + _explicit_policy(
        f"{closed} | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
    )
    refused = _refusal(lambda: methodized(perfect_foresight, gridded))
    assert refused.rule == "grid-coordinate" and "!closed_form reads no grid" in refused.message

    # the obligations on the domain: every representation is evaluated where
    # its data support the function, an expression on its stated domain and
    # nodes inside their interval or through an identified extension; a
    # family sampled from the pairs owes their reconstruction
    domain = {
        item.explanation
        for item in explicit.obligations()
        if item.condition == "evaluation-domain"
    }
    assert domain == {
        "The authored expression is defined, with its stated conditions, at every "
        "point of the represented function's domain at which the function is "
        "evaluated."
    }
    assert [
        item.condition
        for item in combined.obligations()
        if item.condition in ("evaluation-domain", "pair-reconstruction")
    ] == ["evaluation-domain", "pair-reconstruction"]
    assert any(
        "identified extension" in item.explanation
        for item in own.obligations()
        if item.condition == "evaluation-domain"
    )


# --- item 2: the preparation checks, unit D ---


# the representation of the closed-form decision value by PCHIP on its own
# grid of resources, an addition read with the application's methods.bl,
# which overrides the closed form `!explicit` generates at that Evaluation
OWN_NODES = """n_m : ℕ
m_lo : Xm
m_hi : Xm
cntn_to_dcsn.evaluate.method : !pchip
cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m))
"""


def _preparation_checks(request):
    """The preparation parts of item 2 (build contract §§3, 4): each of the
    four data sources prepared for numerical use by the application's
    module, from the source the version's method record selects. A table
    whose grid is configured before the calibration that values its knots
    leaves the exact comparison to preparation, which refuses a different
    support and builds the evaluator from an equal one, the two signed zeros
    one point, and compares a spaced grid through its exact nodes; the
    selected pairs of the endogenous grid method give the Linear evaluator
    of the policy; the closed form gives the compiled
    kernel of its expression; a PCHIP representation of the closed-form
    decision value samples it on its own realized grid, and its preparation
    is refused where the conversion of the grid's exact nodes to
    floating-point numbers merges two of them; and a registered
    family that accepts only its own nodes, at the closing Evaluation of the
    `!egm` builder, is prepared from the scalar Linear reconstruction of the
    selected pairs, sampled on its grid."""
    solves = request.getfixturevalue("perfect_foresight_solves")
    nodal = request.getfixturevalue("nodal_family")
    check, closed = solves.check, solves.closed
    exact = check.closed_form(closed)

    # an authored table and its grid, compared exactly at preparation
    table = stage_from_text(perfect_foresight_text(table=True), PERFECT_FORESIGHT_ORIGIN)
    table = methodized(
        table,
        "KN : ℝ × ℝ × ℝ\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : !Cartesian(k=KN)\n",
    )
    calibration = {
        "calibration": {
            **PERFECT_FORESIGHT_CALIBRATION,
            "K": [0.0, 1.0, 2.0],
            "Y": [1.0, 2.0, 4.0],
        }
    }
    prepared = {}
    for grid in ([0.0, 1.0, 3.0], [-0.0, 1.0, 2.0]):
        version = copy_native(table)
        version.configure({"settings": {"KN": grid}})
        version.calibrate(calibration)
        try:
            prepared[grid[-1]] = check.prepare_table(
                version, "dcsn_to_arvl.table.evaluate", "K", "Y"
            )
        except ValueError as error:
            prepared[grid[-1]] = str(error)
    assert "exactly the table's finite support" in prepared[3.0]
    assert (prepared[2.0].word, prepared[2.0].source) == ("!Linear", "table")
    assert prepared[2.0].evaluator([0.0, 0.5, 1.5, 2.0]).tolist() == [1.0, 1.5, 3.0, 4.0]

    # a spaced grid beside the table, compared with its exact nodes: the
    # middle of three nodes from 0.1 to 0.2 is no floating-point number, so
    # the knot 0.15000000000000002, its nearest one, is refused; the nodes
    # from 0 to 1 are floating-point numbers, and the equal table is prepared
    spaced = stage_from_text(perfect_foresight_text(table=True), PERFECT_FORESIGHT_ORIGIN)
    spaced = methodized(
        spaced,
        "k_lo : ℝ\nk_hi : ℝ\nn_k : ℕ\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : "
        "!Cartesian(k=(k_lo, k_hi, n_k))\n",
    )
    for lower, upper, knots in (
        (0.1, 0.2, [0.1, 0.15000000000000002, 0.2]),
        (0.0, 1.0, [0.0, 0.5, 1.0]),
    ):
        version = copy_native(spaced)
        version.configure({"settings": {"k_lo": lower, "k_hi": upper, "n_k": 3}})
        version.calibrate(
            {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "K": knots, "Y": [1.0, 2.0, 4.0]}}
        )
        try:
            prepared[upper] = check.prepare_table(version, "dcsn_to_arvl.table.evaluate", "K", "Y")
        except ValueError as error:
            prepared[upper] = str(error)
    assert (
        "the node 10808639105689191/72057594037927936 (nearest floating-point number "
        "0.15000000000000002) of the grid and the knot 0.15000000000000002 of the table"
    ) in prepared[0.2]
    assert prepared[1.0].evaluator([0.0, 0.25, 1.0]).tolist() == [1.0, 1.5, 4.0]

    # the selected pairs of the endogenous grid method, and the closed form
    held = solves.comparisons[50]
    pairs = check.prepare_pairs(held.gridded, "policy.evaluate", held.route)
    assert (pairs.word, pairs.source) == ("!Linear", "pairs")
    assert np.array_equal(pairs.nodes, held.route.knots)
    difference = pairs.evaluator(solves.resources) - exact.consumption(solves.resources)
    assert np.max(np.abs(difference)) < 1e-9
    expression = check.prepare_expression(closed, "policy.evaluate")
    assert (expression.word, expression.source, expression.nodes) == (
        "!closed_form",
        "expression",
        None,
    )
    assert expression.evaluator(np.array([1.0])).tolist() == pytest.approx([2.0])

    # own nodes: the closed-form decision value sampled on the realized grid
    own = methodized(check.elaborated(), check.source(check.METHODS), OWN_NODES)
    own.calibrate(check.CALIBRATION)
    own.configure({"settings": {"n_m": 9, "m_lo": -30.0, "m_hi": 50.0}})
    sampled = check.prepare_own_nodes(own, "cntn_to_dcsn.evaluate", check.closed_form(own).value)
    assert (sampled.word, sampled.source) == ("!pchip", "own nodes")
    assert sampled.nodes.tolist() == [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    assert np.array_equal(sampled.values, exact.value(sampled.nodes))
    assert np.array_equal(sampled.evaluator(sampled.nodes), sampled.values)

    # the same preparation on three nodes from 1 to 1.0000000000000002, the
    # first two of which have the nearest floating-point number 1.0, refuses
    # the conversion that merges them
    own.configure({"settings": {"n_m": 3, "m_lo": 1.0, "m_hi": 1.0000000000000002}})
    with pytest.raises(ValueError) as merged:
        check.prepare_own_nodes(own, "cntn_to_dcsn.evaluate", check.closed_form(own).value)
    assert (
        "the grid of 'cntn_to_dcsn.evaluate' holds the distinct exact nodes m = 1 and "
        "m = 9007199254740993/9007199254740992, whose nearest floating-point number is the "
        "same, 1.0; numerical preparation converts the exact nodes of a grid to "
        "floating-point numbers and refuses a conversion that merges distinct nodes"
    ) == str(merged.value)

    # a family that accepts only its own nodes, under !egm, prepared from
    # the reconstruction of the selected pairs on its grid
    if nodal.word not in families():
        register(nodal)
    written = "\n    | policy.evaluate.method : !Linear]"
    text = check.GRIDDED_METHODS.read_text(encoding="utf-8")
    assert text.count(written) == 1
    text = text.replace(
        written,
        "\n    | policy.evaluate.method : !nodal"
        "\n    | policy.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m))]",
    )
    version = check.elaborated()
    version.methodize({"text": text + "n_m : ℕ\nm_lo : Xm\nm_hi : Xm\n", "origin": "nodal.bl"})
    version.calibrate(check.CALIBRATION)
    version.configure(
        {
            "settings": {
                "n_a": 50,
                "a_min": -40.0,
                "a_max": 60.0,
                "n_m": 11,
                "m_lo": -30.0,
                "m_hi": 50.0,
            }
        }
    )
    assert version.methods["policy.evaluate"].source == "own nodes"
    assert "pair-reconstruction" in [item.condition for item in version.obligations()]
    route = check.gridded_route(version)
    reconstructed = check.prepare_own_nodes(
        version, "policy.evaluate", lambda nodes: check.reconstruct(route, nodes)
    )
    assert (reconstructed.word, reconstructed.source, reconstructed.evaluator) == (
        "!nodal",
        "own nodes",
        None,
    )
    assert reconstructed.nodes.tolist() == [-30.0 + 8.0 * n for n in range(11)]
    assert np.max(np.abs(reconstructed.values - exact.consumption(reconstructed.nodes))) < 1e-9


# --- item 2: the test, unit B ---


def test_item_2_representations_read_the_data_their_place_supplies_in_the_order_of_the_sources(
    request,
):
    """Item 2: the registry, the four data sources selected from the combined
    declarations, the refusals of an unaccepted source, the sites of a node,
    opaque incoming functions, combined and successive selections with the
    removal of `!egm`, a family registered again, the exact comparison of a
    table with its grid, the authored closed form bound with no setting and
    refused with a grid, and the obligations on the domain; then
    the preparation of each of the four sources and of a registered family
    that accepts only its own nodes."""
    _selection_checks(request)
    _preparation_checks(request)


# --- item 3: the explicit checks, unit B ---


def _explicit_checks(request):
    """The explicit half of item 3 (build contract §5): the row of
    `!explicit`; the operative rows of an explicit policy builder beside its
    declared maximization; its compiled kernel executed; the closed form
    generated at its Evaluation with its provenance, overridden by an
    authored representation and removed with `!explicit`; an explicit value
    builder; every exclusion; and the formula-only block refused under
    `!egm` and `!time_iteration` while the blocks of those methods that read
    the continuation value bind."""
    perfect_foresight = request.getfixturevalue("perfect_foresight")
    explicit = request.getfixturevalue("perfect_foresight_explicit")
    cons_savings_iid = request.getfixturevalue("cons_savings_iid")

    row = method_types["!explicit"]
    assert (row.kind, row.takes_block, row.admits, dict(row.keywords), row.grid) == (
        "solution",
        True,
        ("builder",),
        {},
        None,
    )
    # the block's one line stands in place of the maximization at the
    # operative level, and the declared level keeps the maximization
    assert [piece.key for piece in explicit.builder.policy.kernels().pieces] == [
        "consumption:Aggregation",
        "Evaluation",
    ]
    assert "policy.optimality:Argmax" in explicit.declared.policy.list().names
    # the compiled kernel executes and reads the derived parameter h through
    # its definition, with the declared parameters alone as its arguments: at
    # the calibration, consumption is κ*(m - 1 + h) with κ = 0.04/1.04 and
    # h = 52, compared exactly in item 4
    calibrated = copy_native(explicit).calibrate({"calibration": PERFECT_FORESIGHT_CALIBRATION})
    consumption = calibrated.builder.policy.primitives["consumption:Aggregation"]
    kernel = consumption.kernel()
    resources = np.array([0.0, 1.0, 10.0])
    assert kernel.parameters == ("β", "ρ", "R", "Γ")
    assert "    h = 1/(1 - Γ/R)\n" in kernel.python and "(m - 1 + h)" in kernel.python
    assert np.allclose(
        consumption.compile_kernel()(resources, *kernel.parameter_values),
        0.04 / 1.04 * (resources - 1 + 52),
    )
    # the closed form generated at the Evaluation, shown as generated by the
    # methods and the signature
    held = explicit.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == (
        "!closed_form",
        "expression",
        "policy.method",
    )
    assert "policy.evaluate   !closed_form   generated from policy.method" in str(explicit.methods)
    assert "method     !closed_form  generated from policy.method" in str(
        explicit.builder.policy.primitives["policy:Evaluation"].signature()
    )
    # an authored representation overrides it, and removing !explicit
    # removes it
    tabulated = methodized(
        perfect_foresight,
        EXPLICIT_GRID_SETTINGS
        + _explicit_policy(
            "policy.evaluate.method : !Linear | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
        ),
    )
    held = tabulated.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!Linear", "own nodes", None)
    assert dict(methodized(explicit, "").methods) == {}
    # an explicit backward value builder, its Evaluation generated likewise
    value = methodized(
        perfect_foresight,
        "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {\n"
        "    V = (1 - (R*β)^(1/ρ)/R)^(-ρ)*(m - 1 + h)^(1-ρ)/(1-ρ)    :: [id=closed_value]\n}\n",
    )
    assert value.methods["cntn_to_dcsn.evaluate"].generated_from == "cntn_to_dcsn.method"

    # the exclusions, each refused naming its cause and the method under
    # which such a line is written, at the line at fault in the addition, the
    # block's third line, or at the typing entry, its second, where no line
    # is at fault
    policy = "[id=policy, policy.method : {word}] {{\n{line}}}\n"
    solving = "!egm or !time_iteration, whose block reads the continuation value"
    cases = (
        (
            "!explicit",
            "    c^(-ρ) = β*R*D_{a}V[>]    :: [id=euler]\n",
            3,
            ("states a relation", solving),
        ),
        (
            "!explicit",
            "    c = (β*D_{a}V[>])^(-1/ρ)    :: [id=inverse]\n",
            3,
            ("reads V[>], a value input", solving),
        ),
        (
            "!explicit",
            "    c[>] = (1 - (R*β)^(1/ρ)/R)*(a + 1)    :: [id=candidate]\n"
            "    c = c[>]    :: [id=identification]\n",
            3,
            ("defines c[>], a field at another perch", "write the line under !egm"),
        ),
        (
            "!explicit",
            "    c = solve_{c}(c - (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R)))    :: [id=solved]\n",
            3,
            ("applies solve, an operator", solving),
        ),
        (
            "!explicit",
            "    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n"
            "    c = argmax_{cp : Γ_c(m)}(κ*𝑢(cp))    :: [id=chosen]\n",
            4,
            ("applies argmax, an operator", solving),
        ),
        (
            "!explicit",
            "    c = D_{m}(m^2)    :: [id=slope]\n",
            3,
            ("applies D, an operator", solving),
        ),
        (
            "!explicit",
            "    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n",
            2,
            (
                "no line the addition appends writes c",
                "write a line `c = <expression>` in the block",
            ),
        ),
        ("!egm", EXPLICIT_POLICY.split("\n")[2] + "\n", 2, ("type !explicit",)),
        ("!time_iteration", EXPLICIT_POLICY.split("\n")[2] + "\n", 2, ("type !explicit",)),
    )
    for word, line, at, words in cases:
        refused = _refusal(
            lambda: methodized(perfect_foresight, policy.format(word=word, line=line))
        )
        assert (refused.rule, refused.file, refused.line) == (
            "explicit-solution",
            "addition-1.bl",
            at,
        ), (word, line)
        assert all(each in refused.message for each in words), (words, refused.message)
    # a value builder's line that reads the control at which its declared
    # lines are read, refused at the line
    refused = _refusal(
        lambda: methodized(
            perfect_foresight,
            "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {\n"
            "    V = 𝑢(c)/(1-β)    :: [id=stationary]\n}\n",
        )
    )
    assert (refused.rule, refused.address, refused.line) == (
        "explicit-solution",
        "cntn_to_dcsn",
        3,
    )
    assert "reads c, a control input of the builder's header" in refused.message
    # an expectation integrates over a shock, so it writes no explicit
    # function: on the buffer-stock stage, which has two shocks, the line is
    # refused at its own position
    refused = _refusal(
        lambda: methodized(
            request.getfixturevalue("buffer_stock"),
            "[id=dcsn_to_arvl, dcsn_to_arvl.method : !explicit] {\n"
            "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * 𝑢(R*k/(Γ*ψ) + ξ))    :: [id=closed]\n}\n",
        )
    )
    assert (refused.rule, refused.address, refused.line) == (
        "explicit-solution",
        "dcsn_to_arvl",
        3,
    )
    assert "applies E, an operator" in refused.message and solving in refused.message
    # an entry with no block of the builder's id, typed in an addition or in
    # the stage file beside the stage file's own explicit line, is refused at
    # the entry with the block to write; a forward builder is refused first
    for text, words in (
        ("policy.method : !explicit\n", "no addition appends a line"),
        ("arvl_to_dcsn.method : !explicit\n", "is a forward builder"),
    ):
        refused = _refusal(lambda: methodized(perfect_foresight, text))
        assert (refused.rule, refused.line) == ("explicit-solution", 2), text
        assert words in refused.message, text
    own = perfect_foresight_text(
        ("[id=policy, (V[>]", "policy.method : !explicit\n[id=policy, (V[>]"),
        ("c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])", "c = 0.5*(m - 1 + h)"),
    )
    refused = _refusal(lambda: stage_from_text(own, PERFECT_FORESIGHT_ORIGIN))
    assert (refused.rule, refused.address) == ("explicit-solution", "policy")
    assert "a block `[id=policy, policy.method : !explicit]`" in refused.message
    assert refused.write.startswith("Write in the methods file the block")
    # the blocks of !egm that read the continuation value's derivative bind
    path = ROOT / CORPUS["cons_savings_iid"]
    bound = copy_native(cons_savings_iid).methodize(path.parent / "methods.bl")
    assert bound.methods["policy"].word == "!egm"


# --- item 3: the derived checks, unit C ---


def _derived_checks(request):
    """The derived half of item 3 (build contract §5), through public
    calibration. On the perfect-foresight fixture, h and R_n construct and
    `stage.par` lists them after the declared parameters with their
    definitions; a calibration that names h, and one at which h divides by
    zero, are refused at h's definition; a cycle, a name that is no parameter
    and a call other than log and exp are refused at elaboration. Calibrated,
    h is 52, the stored calibration holds the declared parameters alone, the
    compiled law of motion writes R_n through its definition with the
    declared parameters as its arguments, and h's definition card shows its
    definition and value. κ, which a methods addition defines, is listed
    after `methodize` and not before, is 0.04/1.04 at the calibration and
    leaves with its addition, and an addition whose definition has no value
    at the kept calibration is refused. On the buffer-stock stage with μ_ξ
    derived, the derived value reaches the distribution check: at σ_ξ = 0 the
    positive atom of the transitory draw is 1/(1 − p_zero), and the variant
    whose derived log scale is negative is refused."""
    fixtures = request.getfixturevalue("derived_parameters")
    lines = enumerate(fixtures.text.split("\n"), 1)
    line = next(n for n, text in lines if text.startswith("h :="))
    at_h = ("derived-parameter", f"{fixtures.origin}:{line}")

    stage = fixtures.stage()
    assert list(stage.par) == ["β", "ρ", "R", "Γ", "h", "R_n"]
    assert str(stage.par["h"]) == "h := 1/(1 - Γ/R), unbound"
    for values in ({**fixtures.calibration, "h": 52.0}, {**fixtures.calibration, "Γ": 1.04}):
        with pytest.raises(ConstructionError) as refused:
            stage.calibrate({"calibration": values})
        assert (refused.value.rule, refused.value.address) == at_h
    assert stage.bindings.calibration is None
    for changed, rule in (
        ("h := 1/(1 - Γ/R) + q\nq := h/2", "definition-order"),
        ("h := 1/(1 - Γ/m)", "derived-parameter"),
        ("h := 1/sqrt(1 - Γ/R)", "derived-parameter"),
    ):
        with pytest.raises(ConstructionError) as refused:
            fixtures.stage(("h := 1/(1 - Γ/R)", changed))
        assert refused.value.rule == rule, changed

    stage.calibrate({"calibration": fixtures.calibration})
    assert stage.par["h"].value == pytest.approx(52.0)
    assert dict(stage.bindings.calibration) == fixtures.calibration
    law = stage.builder["arvl", "dcsn"]["Pushforward"]
    kernel = law.kernel()
    assert kernel.parameters == ("R", "Γ") and "    R_n = R/Γ\n" in kernel.python
    assert law.compile_kernel()(np.array([1.0]), *kernel.parameter_values) == pytest.approx(
        [1.04 / 1.02 + 1]
    )
    h = next(identity for identity in stage.definitions if str(identity).endswith(":derived:h"))
    card = str(stage.definitions.denote(h))
    assert "h  := 1/(1 − Γ/R)" in card and f"= {stage.par['h'].value!r}" in card

    assert "κ" not in stage.par
    stage.methodize(fixtures.addition)
    assert list(stage.par)[-1] == "κ" and stage.par["κ"].value == pytest.approx(0.04 / 1.04)
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(
            {"text": "@methods: perfect_foresight\nκ := 1/(R - 1.04)\n", "origin": "m.bl"}
        )
    assert (refused.value.rule, refused.value.address) == ("derived-parameter", "m.bl:2")
    stage.methodize([])
    assert "κ" not in stage.par and dict(stage.bindings.calibration) == fixtures.calibration

    p_zero = fixtures.buffer_stock_calibration["p_zero"]
    atom = fixtures.buffer_stock()
    atom.calibrate({"calibration": {**fixtures.buffer_stock_calibration, "σ_ξ": 0.0}})
    assert math.exp(atom.par["μ_ξ"].value) == pytest.approx(1 / (1 - p_zero))
    assert "μ_ξ" not in atom.bindings.calibration
    variant = fixtures.buffer_stock("μ_ξ")
    with pytest.raises(ConstructionError) as refused:
        variant.calibrate({"calibration": {**fixtures.buffer_stock_calibration, "σ_ξ": 0.2}})
    assert refused.value.rule == "distribution-domain"
    assert "μ_ξ = -0.0149874581" in refused.value.message and "σ ≥ 0" in refused.value.message


# --- item 3: the one test, which calls both helpers ---


def test_item_3_explicit_outputs_compile_and_derived_parameters_reach_every_check(request):
    """Item 3: the compiled outputs of an explicit block and every
    exclusion, the formula-only block refused under `!egm` and
    `!time_iteration`, through `_explicit_checks`; and the derived
    definitions, their order, arithmetic and override refusals and their
    values at every calibration check, through `_derived_checks`."""
    _explicit_checks(request)
    _derived_checks(request)


# --- item 4, unit D ---


# the calibration at which the normalized discount factor βΓ^(1-ρ) is 1.8,
# above one, and the closed form still holds (implementation §2)
NORMALIZED_DISCOUNT_ABOVE_ONE = {"β": 0.9, "ρ": 2.0, "R": 1.04, "Γ": 0.5}


def test_item_4_the_perfect_foresight_routes_meet_every_identity_bound_and_refusal(request):
    """Item 4 (implementation §§2, 3): both methods through `elaborate →
    methodize → calibrate → configure`; the derived parameters q, h, L and κ
    and the book's example; the compiled consumption, decision value and
    arrival value against independent formulas at CDC's two calibrations and
    at a valid calibration whose normalized discount exceeds one, with the
    normalization Γ^(1-ρ) and the arrival marginal factor RΓ^(-ρ); the
    Bellman, arrival, Euler and present-value budget identities and
    feasibility; the refusals of Γ ≥ R, q ≥ 1, ρ = 1, nonfinite parameters
    and nonpositive total wealth, each naming its condition; the policy error
    of the gridded route below 10⁻⁹ and the Bellman residual below 10⁻¹² on
    the baseline intervals; Linear and PCHIP value evaluators on 5, 50 and
    500 nodes; the near-limit relative and scaled bounds; and the failures of
    an exhausted iteration, a nonfinite value and an infeasible
    extrapolation. Each evaluation states whether it interpolates or
    extrapolates."""
    solves = request.getfixturevalue("perfect_foresight_solves")
    check, closed = solves.check, solves.closed

    # both methods through the four steps: the closed form on the three
    # explicit builders with no setting, and the endogenous grid method with
    # the Linear policy read from its pairs and the three settings of its grid
    gridded = solves.comparisons[50].gridded
    assert [line.split() for line in str(closed.methods).splitlines()] == [
        ["cntn_to_dcsn", "!explicit"],
        ["cntn_to_dcsn.evaluate", "!closed_form", "generated", "from", "cntn_to_dcsn.method"],
        ["dcsn_to_arvl", "!explicit"],
        ["dcsn_to_arvl.evaluate", "!closed_form", "generated", "from", "dcsn_to_arvl.method"],
        ["policy", "!explicit"],
        ["policy.evaluate", "!closed_form", "generated", "from", "policy.method"],
    ]
    assert list(closed.settings.list()) == [] and not (check.DECLARATION / "settings").exists()
    assert (
        gridded.methods["policy"].word,
        gridded.methods["policy.evaluate"].word,
        gridded.methods["policy.evaluate"].source,
    ) == ("!egm", "!Linear", "pairs")
    assert {(row["name"], row["by"]) for row in gridded.settings.list()} == {
        (name, "!egm") for name in ("n_a", "a_min", "a_max")
    }

    # the derived parameters and the book's example: κ = 0.04/1.04, h = 52,
    # L = -51, and the compiled consumption at m = 1 is κh = 2 (claims 2b and
    # 4f of the second imported file)
    form = check.closed_form(closed)
    assert list(closed.par)[4:] == ["q", "h", "L", "κ"]
    assert (
        form.return_patience < 1 and check.parameters(closed)["Γ"] < check.parameters(closed)["R"]
    )
    assert (form.κ, form.h, form.limit) == (
        pytest.approx(0.04 / 1.04),
        pytest.approx(52.0),
        pytest.approx(-51.0),
    )
    assert form.consumption(1.0) == pytest.approx(form.κ * form.h) == pytest.approx(2.0)
    assert np.allclose(
        form.consumption(solves.resources),
        form.κ * (solves.resources - 1 + form.h),
        rtol=1e-14,
        atol=0,
    )

    # the compiled closed form against the independent formulas, at the three
    # calibrations, on total wealth from 10⁻³ to 100 at the decision and the
    # arrival perch, the two marginals included: κ^(-ρ)w^(-ρ) at w = m - L,
    # and RΓ^(-ρ)v′(Rk/Γ + 1) with v′ that formula; and the identities of the
    # closed form
    impatient = check.closed_form_stage({"calibration": NORMALIZED_DISCOUNT_ABOVE_ONE})
    assert NORMALIZED_DISCOUNT_ABOVE_ONE["β"] * 0.5 ** (1 - 2.0) == pytest.approx(1.8)
    wealth = np.geomspace(1e-3, 100.0, 201)
    for stage, interval in (
        (closed, solves.resources),
        (solves.alternative, solves.resources),
        (impatient, np.linspace(0.0, 50.0, 401)),
    ):
        p, held = check.parameters(stage), check.closed_form(stage)
        reference = check.reference_coefficients(p)
        points = held.limit + wealth
        assert (held.return_patience, held.κ, held.h, held.limit) == pytest.approx(
            (reference.q, reference.κ, reference.h, reference.L), rel=1e-14
        )
        assert np.allclose(
            held.consumption(points), check.reference_consumption(p, points), rtol=1e-12, atol=0
        )
        assert np.allclose(
            held.value(points), check.reference_value(p, points), rtol=1e-12, atol=0
        )
        assert np.allclose(
            held.arrival_value(points),
            check.reference_arrival_value(p, points),
            rtol=1e-12,
            atol=0,
        )
        assert np.allclose(
            held.marginal(points),
            reference.κ ** (-p["ρ"]) * (points - reference.L) ** (-p["ρ"]),
            rtol=1e-12,
            atol=0,
        )
        following = p["R"] * points / p["Γ"] + 1
        assert np.allclose(
            held.arrival_marginal(points),
            p["R"]
            * p["Γ"] ** (-p["ρ"])
            * reference.κ ** (-p["ρ"])
            * (following - reference.L) ** (-p["ρ"]),
            rtol=1e-12,
            atol=0,
        )
        assert np.max(np.abs(check.bellman_residual(stage, interval))) < 1e-12
        assert np.max(np.abs(check.arrival_residual(stage, interval))) < 1e-12
        assert np.max(check.euler_residual(stage, interval)) < 1e-12
        assert check.feasibility(stage, interval).all()
        periods = math.ceil(math.log(1e-12) / math.log(reference.q))
        budget = check.present_value_budget(stage, interval, periods)
        assert (
            np.max(
                np.abs(budget.present_value + budget.remainder - budget.total_wealth)
                / budget.total_wealth
            )
            < 1e-12
        )
        assert np.allclose(
            budget.remainder / budget.total_wealth, reference.q**periods, rtol=0, atol=1e-15
        )
    # the arrival marginal of the gridded variant: its compiled kernel is
    # RΓ^(-ρ) times the decision marginal it reads, and at the compiled
    # envelope condition and the closed-form policy it is RΓ^(-ρ) v′(Rk/Γ + 1)
    p = check.parameters(gridded)
    kernels = gridded.builder["dcsn", "arvl"].kernels()
    marginal = check.kernel_function(kernels, "marginal:Derivative:1")
    envelope = check.kernel_function(
        gridded.builder["cntn", "dcsn"].kernels(), "marginal:Derivative:1"
    )
    k = form.limit + wealth
    following = check.kernel_function(kernels, "Pullback")(k=k)
    decision_marginal = envelope(m=following, c=form.consumption(following))
    assert np.allclose(
        marginal(k=k, **{"D_{m}(V)": decision_marginal}),
        p["R"] * p["Γ"] ** (-p["ρ"]) * decision_marginal,
        rtol=1e-14,
        atol=0,
    )
    assert np.allclose(
        marginal(k=k, **{"D_{m}(V)": decision_marginal}),
        check.reference_arrival_marginal(p, k),
        rtol=1e-12,
        atol=0,
    )

    # the refusals, each naming its condition: Γ ≥ R by the declared set
    # (0, R), the finite human wealth condition; q ≥ 1 by the declared set
    # of β, whose upper bound R^(ρ-1) is the return impatience condition;
    # ρ = 1 by the set (1, inf); nonfinite parameters by their sets; and
    # nonpositive total wealth by each function of the closed form
    for changes, words in (
        ({"Γ": 1.04}, "(0, R)"),
        ({"Γ": 1.06}, "(0, R)"),
        ({"β": 0.99, "ρ": 2.0, "R": 0.9, "Γ": 0.85}, "the condition β < R^(ρ - 1)"),
        ({"ρ": 1.0}, "(1, inf)"),
        ({"β": math.nan}, "(0, 1)"),
        ({"R": math.inf}, "ℝ₊₊"),
        ({"Γ": math.nan}, "(0, R)"),
    ):
        with pytest.raises(ValueError) as refused:
            check.closed_form_stage({"calibration": {**PERFECT_FORESIGHT_CALIBRATION, **changes}})
        assert words in str(refused.value), changes
    with pytest.raises(ValueError, match=r"the condition β < R\^\(ρ - 1\)"):
        check.gridded_stage(
            5, -10.0, 60.0, {"calibration": {"β": 0.99, "ρ": 2.0, "R": 0.9, "Γ": 0.85}}
        )
    # one rounding step below the bound R^(ρ-1) the discount factor binds and
    # q computes to one: the route's own check refuses it, and the closed
    # form refuses it by κ > 0
    rounding = {"calibration": {"β": 0.8999999999999999, "ρ": 2.0, "R": 0.9, "Γ": 0.81}}
    with pytest.raises(ValueError, match=r"return impatience condition q < 1"):
        check.gridded_route(check.gridded_stage(5, -10.0, 60.0, rounding))
    with pytest.raises(ValueError, match=r"κ > 0"):
        check.closed_form_stage(rounding)
    # a grid of savings from -40 starts below the natural borrowing limit of
    # the second calibration, L = 1 - 1/(1 - 1.01/1.04), about -33.7
    with pytest.raises(ValueError, match="at or below the natural borrowing limit"):
        check.gridded_route(
            check.gridded_stage(
                50, -40.0, 60.0, {"calibration": {"β": 0.90, "ρ": 2.0, "R": 1.04, "Γ": 1.01}}
            )
        )
    for function, point in (
        (form.consumption, form.limit),
        (form.value, form.limit - 1.0),
        (form.marginal, form.limit),
        (form.arrival_value, form.limit),
        (form.arrival_marginal, form.limit - 1.0),
    ):
        with pytest.raises(ValueError, match="total wealth"):
            function(np.array([0.0, point]))

    # the gridded route at the baseline: policy error below 10⁻⁹ at 5, 50
    # and 500 savings and at the second calibration, every comparison point
    # interpolated, each route converged, and the extension reported at each
    # iteration of each route
    for found in (*solves.comparisons.values(), solves.alternative_comparison):
        assert found.difference < 1e-9
        assert (found.interpolated, found.extrapolated) == (401, 0)
        assert found.route.change < 1e-12 and len(found.route.extended) == found.iterations
    # the comparison's record and the fixed point's `evaluate`: the linear
    # interpolant between the pairs; outside them a refusal unless
    # extrapolation is asked for, and then the checked endpoint-secant
    # extension, whose use is reported
    found = solves.comparisons[50]
    assert {"n_a", "iterations", "difference", "route"} <= set(vars(found))
    route, inside = found.route, solves.resources
    assert np.array_equal(route.evaluate(inside), route.policy(inside))
    beyond = np.array([route.knots[-1] + 10.0])
    with pytest.raises(ValueError, match="outside the pairs"):
        route.evaluate(beyond)
    with pytest.warns(UserWarning, match="endpoint-secant extension gives 1 of the 1 points"):
        extended = route.evaluate(beyond, extrapolate=True)
    assert np.array_equal(
        extended, route.policy.extend(beyond, check.EndpointSecant(route.limit)).values
    )
    with pytest.raises(ValueError, match="restricted to the economic domain"):
        route.evaluate(np.array([route.limit]), extrapolate=True)

    # the Linear and PCHIP value evaluators on [-30, 50]: off-node errors on
    # the fixed sample fall at each refinement, every sample point
    # interpolates, and Linear stays within Δ² max|v″|/8 and the rounding
    # allowance; PCHIP's slopes follow the published rules, here at the
    # nodes 0 to 5 with the values 0, 1, 0.5, 0.5, 2, -1, where every
    # interior slope is zero and the end slopes are the three-point
    # estimates 1.75 and -5.25
    for word in ("Linear", "pchip"):
        found = [check.value_interpolation(closed, word, count) for count in (5, 50, 500)]
        for name in ("decision", "arrival"):
            rows = [getattr(item, name) for item in found]
            assert all(
                fine.error < coarse.error or coarse.error <= coarse.allowance
                for coarse, fine in zip(rows, rows[1:])
            ), (word, name)
            assert all((row.interpolated, row.extrapolated) == (1000, 0) for row in rows)
            if word == "Linear":
                assert all(row.error <= row.bound + row.allowance for row in rows), name
    assert check.Pchip(range(6), [0.0, 1.0, 0.5, 0.5, 2.0, -1.0]).slopes.tolist() == [
        1.75,
        0.0,
        0.0,
        0.0,
        0.0,
        -5.25,
    ]
    assert check.Pchip([0.0, 3.0, 3.2, 4.0], [0.0, 0.3, -2.0, 1.0]).slopes[0] == pytest.approx(0.3)
    # at unequally spaced nodes an interior slope is the harmonic mean of
    # the two secants, weighted by the widths, and an end slope is the
    # three-point estimate, zero where its sign differs from the end
    # secant's; the first row is derived by hand from those rules, and both
    # rows are the slopes SciPy 1.14.1's PchipInterpolator gives
    assert check.Pchip(
        [0.0, 1.0, 3.0, 3.5], [0.0, 1.0, 2.0, 4.0]
    ).slopes.tolist() == pytest.approx([7 / 6, 9 / 13, 20 / 19, 4.7], rel=1e-12)
    assert check.Pchip(
        [0.0, 0.1, 3.0, 4.0], [0.0, 0.01, 30.0, 31.0]
    ).slopes.tolist() == pytest.approx(
        [0.0, 0.15177125506072875, 1.6085073025827212, 0.0], rel=1e-12, abs=1e-15
    )
    # the derivatives each evaluator offers are the orders the registry
    # records, each with its coordinate, shape and region, and they are the
    # representation's own: Linear's slopes differ on the two sides of the
    # node -10, PCHIP's first derivative is continuous there and its second
    # derivative jumps, and on 500 nodes PCHIP's first derivative stays
    # within 10⁻⁴ of the authored envelope condition D_{m}V = c^(-ρ)
    nodes, side = np.linspace(-30.0, 50.0, 5), [-10.0 - 1e-9, -10.0]
    linear = check.Linear(nodes, form.value(nodes), "m")
    pchip = check.Pchip(nodes, form.value(nodes), "m")
    for evaluator, word in ((linear, "Linear"), (pchip, "pchip")):
        assert [(d.coordinate, d.order, d.shape) for d in evaluator.derivatives] == [
            ("m", order, ()) for order in families()[word].derivatives
        ]
    left, right = linear.derivative(side, 1)
    assert left > right
    assert np.ptp(pchip.derivative(side, 1)) < 1e-6 < np.ptp(pchip.derivative(side, 2))
    fine, sample = np.linspace(-30.0, 50.0, 500), check.evaluation_sample(-30.0, 50.0)
    authored = envelope(m=sample, c=form.consumption(sample))
    assert (
        np.max(
            np.abs(check.Pchip(fine, form.value(fine)).derivative(sample) - authored) / authored
        )
        < 1e-4
    )

    # near the borrowing limit, on total wealth from 10⁻³ to 1: the converged
    # policy interpolated between the pairs of the near-limit route, with the
    # exact compiled values; a point below the first pair is refused
    near = check.near_limit(closed, solves.near_route, np.geomspace(1e-3, 1.0, 61))
    assert near.policy_error < 1e-8 and near.euler < 1e-8 and near.bellman < 1e-10
    assert (near.interpolated, near.extrapolated) == (61, 0)
    with pytest.raises(ValueError, match="outside the closed node interval"):
        solves.near_route.policy(form.limit + 1e-5)

    # the failures of the iteration: an exhausted iteration limit, a value
    # that is not finite, at ρ = 400 where the marginal value underflows, and
    # an infeasible extrapolation from the first iterate of CDC's narrow grid
    with pytest.raises(ValueError, match="limit of iterations"):
        check.gridded_route(solves.comparisons[5].gridded, iterations=3)
    with pytest.raises(ValueError, match="not finite"):
        check.gridded_route(
            check.gridded_stage(
                5, -40.0, 60.0, {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "ρ": 400.0}}
            )
        )
    narrow = np.linspace(-40.0, -39.9, 5)
    with pytest.raises(ValueError, match="leaves the feasible set"):
        check.gridded_route(
            check.gridded_stage(
                5, -40.0, -39.9, {"calibration": {**PERFECT_FORESIGHT_CALIBRATION, "ρ": 2.5}}
            ),
            initial=(narrow + 1.0, np.linspace(1.0, 2.0, 5)),
        )


# --- item 5: the entry-point checks, unit D ---


def _entry_point_checks():
    """The public surface of the perfect-foresight application's module as
    CDC's version wrote it, which other programs import (implementation §2):
    its twelve functions with the arguments each takes, its six path
    constants, and the fields of the records of the closed form and of the
    gridded route. Three functions take a further optional argument: the
    Bellman and Euler residuals a `policy`, so that the near-limit check
    reads the converged policy, and the gridded route its `initial` pairs,
    so that the failure of an infeasible extrapolation can be provoked."""
    check = closed_form_check()
    assert {
        name: tuple(inspect.signature(getattr(check, name)).parameters)
        for name in (
            "closed_form_stage",
            "gridded_stage",
            "parameters",
            "piece",
            "kernel_text",
            "closed_form",
            "value_kernels",
            "bellman_residual",
            "euler_residual",
            "interpolate",
            "gridded_route",
            "comparison",
        )
    } == {
        "closed_form_stage": ("calibration",),
        "gridded_stage": ("n_a", "a_min", "a_max", "calibration"),
        "parameters": ("stage",),
        "piece": ("record", "key", "values"),
        "kernel_text": ("record", "key"),
        "closed_form": ("stage",),
        "value_kernels": ("stage",),
        "bellman_residual": ("stage", "m", "policy"),
        "euler_residual": ("stage", "m", "policy"),
        "interpolate": ("m", "knots", "values"),
        "gridded_route": ("stage", "tolerance", "iterations", "initial"),
        "comparison": ("n_a", "a_min", "a_max", "m", "tolerance", "calibration"),
    }
    # the six path constants: the application's folder, its declaration, the
    # stage file, the two methods files beside it and the calibration
    folder = check.DECLARATION / "stages" / "perfect_foresight"
    assert (
        check.DECLARATION,
        check.STAGE,
        check.METHODS,
        check.GRIDDED_METHODS,
        check.CALIBRATION,
    ) == (
        check.FOLDER / "declaration",
        folder / "perfect_foresight.bl",
        folder / "methods.bl",
        folder / "methods.egm.bl",
        check.DECLARATION / "calibration" / "perfect_foresight.yml",
    )
    assert all(
        path.is_file()
        for path in (check.STAGE, check.METHODS, check.GRIDDED_METHODS, check.CALIBRATION)
    )
    # the fields of the two records, the closed form's exactly and the
    # gridded route's at least CDC's, with the arguments of `evaluate`
    form = check.closed_form(check.closed_form_stage())
    assert set(vars(form)) == {
        "return_patience",
        "κ",
        "h",
        "limit",
        "consumption",
        "value",
        "marginal",
        "arrival_value",
        "arrival_marginal",
    }
    route = check.gridded_route(check.gridded_stage(5, -40.0, 60.0))
    assert {"knots", "consumption", "iterations", "evaluate"} <= set(vars(route))
    assert tuple(inspect.signature(route.evaluate).parameters) == ("m", "extrapolate")
    assert inspect.signature(route.evaluate).parameters["extrapolate"].default is False


# --- item 5: the buffer-stock checks, unit D2 ---


def _declared_value(expression, values):
    """The value of `expression`, an expression as the stage prints it, at
    `values`, a mapping from names to numbers or functions: the printed text
    read as a Python expression with the power `^` as `**`, and log and exp
    those of mpmath, so that values given at fifty digits are evaluated at
    fifty digits."""
    names = {"log": mpmath.log, "exp": mpmath.exp, **values}
    return eval(expression.replace("^", "**"), {"__builtins__": {}}, names)


def _transitory_law(stage, values=None):
    """The law of the transitory draw ξ as the Expectation of the arrival
    value builder's `kernels()` record prints it, a mixture of an atom and a
    lognormal draw, with its arguments evaluated at `values`, by default the
    values `stage.par` answers: the pair of the atom's weight and point, and
    the pair of the draw's weight and the location and scale of its
    LogNormal. A law of another form does not unpack into these pairs."""
    record = stage.builder["dcsn", "arvl"].kernels()
    (expectation,) = [piece for piece in record.pieces if piece.kind == "Expectation"]
    law = expectation.kernel.split("\n", 1)[0].partition("ξ ~ ")[2]
    if values is None:
        values = {name: stage.par[name].value for name in stage.par}
    families = {"Mixture": lambda *parts: parts, "LogNormal": lambda *arguments: arguments}
    (atom_weight, atom), (weight, (location, scale)) = _declared_value(law, {**values, **families})
    return (atom_weight, atom), (weight, (location, scale))


def _transitory_mean(law):
    """The exact mean of `law`, a law as `_transitory_law` gives it: the
    atom's weight times its point, plus the draw's weight times the mean
    exp(μ + σ²/2) of its LogNormal(μ, σ)."""
    (atom_weight, atom), (weight, (location, scale)) = law
    return atom_weight * atom + weight * mpmath.exp(location + scale**2 / 2)


def _transitory_quadrature(law, nodes):
    """The points and the probabilities that Gauss–Hermite quadrature with
    `nodes` nodes gives `law`, a law as `_transitory_law` gives it: the
    atom's point with the atom's weight, and the points exp(μ + σ·z) at the
    standard normal nodes z with the draw's weight times the weights of the
    rule, divided by √(2π). At σ = 0 every point of the draw is exp(μ)."""
    (atom_weight, atom), (weight, (location, scale)) = law
    standard, weights = np.polynomial.hermite_e.hermegauss(nodes)
    points = np.concatenate(([atom], np.exp(location + scale * standard)))
    drawn = weight * weights / math.sqrt(2 * math.pi)
    return points, np.concatenate(([atom_weight], drawn))


def _buffer_stock_checks(request):
    """The buffer-stock half of item 5 (implementation §§2, 3), through the
    application's files and public calibration, read from the fixture
    `buffer_stock_application`. The stage file defines
    μ_ξ := -log(1 - p_zero) - σ_ξ^2/2, which `stage.par` lists after the
    declared parameters and the stored calibration does not hold. The law
    of ξ is read as the arrival value builder's `kernels()` record prints
    it, and its weights and the arguments of its LogNormal are evaluated at
    the values the stage gives. The exact mean of that law is one: at fifty
    digits from the primitive parameters, with μ_ξ evaluated by the
    definition `stage.par` prints, and to rounding at the value of μ_ξ the
    stage computes. Separately, Gauss–Hermite quadrature of the same law at
    the application's seven nodes and at fourteen keeps its mass and its
    mean at one to rounding; this is evidence about a quadrature rule, not
    about a Bellman integration handler. At σ_ξ = 0 every positive point of
    the rule is the atom 1/(1 − p_zero), and the mean is one. A calibration
    at p_zero = 0 or 1 is refused by the declared set (0, 1), and one that
    supplies μ_ξ, even at the value of its definition, is refused at the
    definition; the derived parameter owns one condition of the model, that
    its value is a real number, established at calibration. The printed law
    names μ_ξ and holds neither its value nor its definition, so that a
    handler reads the value in `stage.par`. The methods file binds its four
    components as it writes them, the settings file configures them, and
    the example page quotes the three files as they stand. The negative
    derived scale is refused in item 3, by `_derived_checks`, on this stage
    file."""
    application = request.getfixturevalue("buffer_stock_application")
    calibration = application.calibration
    eps = np.finfo(float).eps

    stage = application.stage(calibration)
    assert repr(stage) == "ElaboratedStage('buffer_stock', specified)"
    assert list(stage.par)[-1] == "μ_ξ" and stage.par["μ_ξ"].derived
    assert str(stage.par["μ_ξ"]).endswith(":= -log(1 - p_zero) - σ_ξ^2/2")
    assert "μ_ξ" not in stage.bindings.calibration
    p_zero, scale, location = (stage.par[name].value for name in ("p_zero", "σ_ξ", "μ_ξ"))

    # the exact mean of the declared law, at fifty digits from the primitive
    # parameters and to rounding at the value of μ_ξ the stage computes
    definition = str(stage.par["μ_ξ"]).partition(":= ")[2]
    with mpmath.workdps(50):
        primitive = {
            name: mpmath.mpf(stage.par[name].value)
            for name in stage.par
            if not stage.par[name].derived
        }
        exact = _declared_value(definition, primitive)
        law = _transitory_law(stage, {**primitive, "μ_ξ": exact})
        assert abs(_transitory_mean(law) - 1) < mpmath.mpf(10) ** -45
        p, s = primitive["p_zero"], primitive["σ_ξ"]
        assert abs(location - exact) <= 4 * eps * (abs(mpmath.log(1 - p)) + s**2 / 2)
    law = _transitory_law(stage)
    assert abs(_transitory_mean(law) - 1) <= 2 * eps

    # the separate evidence of numerical quadrature of the same law, and the
    # zero-scale atom
    nodes = stage.settings["n_ξ_nodes"].value
    assert nodes == 7
    for count in (nodes, 2 * nodes):
        points, probabilities = _transitory_quadrature(law, count)
        assert abs(probabilities.sum() - 1) <= 4 * eps
        assert abs(probabilities @ points - 1) <= 4 * eps
    atom = application.stage({**calibration, "σ_ξ": 0.0})
    points, probabilities = _transitory_quadrature(_transitory_law(atom), nodes)
    positive = np.unique(points[1:])
    assert positive.size == 1 and positive[0] == pytest.approx(1 / (1 - p_zero), rel=4 * eps)
    assert abs(probabilities @ points - 1) <= 4 * eps

    # the bounds of p_zero, and a calibration that supplies μ_ξ
    for value in (0.0, 1.0):
        with pytest.raises(ValueError, match=r"lies outside the declared set \(0, 1\)"):
            application.stage({**calibration, "p_zero": value})
    lines = (ROOT / DERIVED_BUFFER_STOCK).read_text(encoding="utf-8").split("\n")
    line = next(n for n, written in enumerate(lines, 1) if written.startswith("μ_ξ :="))
    with pytest.raises(ConstructionError) as refused:
        application.stage({**calibration, "μ_ξ": location})
    assert (refused.value.rule, refused.value.address) == (
        "derived-parameter",
        f"{DERIVED_BUFFER_STOCK}:{line}",
    )
    assert "which the stage defines as `-log(1 - p_zero) - σ_ξ^2/2`" in refused.value.message
    owned = [
        item
        for item in stage.obligations()
        if item.entries and str(item.entries[0]) == "buffer_stock:derived:μ_ξ"
    ]
    assert [(item.condition, item.status) for item in owned] == [
        ("arithmetic-definedness", "established")
    ]

    # what a handler reads from the kernels of the arrival value builder
    record = stage.builder["dcsn", "arvl"].kernels()
    (expectation,) = [piece for piece in record.pieces if piece.kind == "Expectation"]
    assert "LogNormal(μ_ξ, σ_ξ)" in expectation.kernel and expectation.parameters == ()
    assert "μ_ξ" not in record.parameters and "log(1 - p_zero)" not in str(record)

    # the entry points, the methods file's syntax and the example page
    assert [(str(place), str(method)) for place, method in stage.methods.items()] == [
        ("dcsn_to_arvl.E_ψ_ξ", "!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)"),
        ("dcsn_to_arvl.evaluate", "!Linear   !Cartesian(k=(k_min, k_max, n_k))"),
        ("policy", "!egm   !Cartesian(a=(a_min, a_max, n_a))"),
        ("policy.evaluate", "!Linear"),
    ]
    page = (ROOT / application.page).read_text(encoding="utf-8")
    for quoted in (DERIVED_BUFFER_STOCK, application.methods, application.settings):
        assert (ROOT / quoted).read_text(encoding="utf-8") in page, quoted


# --- item 5: the one test, which calls both helpers ---


def test_item_5_buffer_stock_derives_its_log_mean_and_the_applications_keep_their_entry_points(
    request,
):
    """Item 5: the buffer-stock half, `_buffer_stock_checks`, and the
    comparison functions of the perfect-foresight module, unit D's
    `_entry_point_checks`."""
    _buffer_stock_checks(request)
    _entry_point_checks()


# --- item 6: the reference checks, unit E1 ---


# the methods page, which `docs/_hooks/reference_pages.py` prints from the
# records validation reads (build contract §7)
METHODS_PAGE = "docs/Bellman-Sym/reference/methods.md"
# the fragments of the methods page that the documentation links
LINKED_FRAGMENTS = ("egm", "vfi", "3-the-grid")


def _reference_checks(request):
    """The generated method and grid references (build contract §7): the
    page holds what the generator prints from the current records, so a
    second generation changes nothing; it holds one entry for each method of
    `method_types`, registered families included, and one for each grid
    constructor, in the records' order; an empty argument record prints the
    one sentence of the unlisted-keyword policy; the linked fragments stand;
    and no entry links a public source that no exported revision holds. The
    coverage of arguments and compatibility, registration and removal, the
    links and the executed examples are checked in
    `tests/cat/test_docs_shape.py`."""
    import sys

    from bellman.native.records import NO_REGISTERED_ARGUMENTS
    from bellman.stage.grids import GRID_CONSTRUCTORS

    hooks = str(ROOT / "docs/_hooks")
    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    from reference_pages import MARKERS, methods_table

    page = (ROOT / METHODS_PAGE).read_text(encoding="utf-8")
    generated = methods_table(METHODS_PAGE)
    held = page.split(MARKERS[0], 1)[1].split(MARKERS[1], 1)[0]
    assert held.strip() == generated.strip() == methods_table(METHODS_PAGE).strip()
    words = [*method_types, *(f"!{word}" for word in GRID_CONSTRUCTORS)]
    headings = [line.split("`")[1] for line in generated.splitlines() if line.startswith("### ")]
    assert headings == words
    empty = [word for word in method_types if not method_types[word]["keywords"]]
    assert generated.count(f"**Arguments.** {NO_REGISTERED_ARGUMENTS}") == len(empty)
    from markdown.extensions.toc import slugify

    fragments = {line.split('"')[1] for line in page.splitlines() if line.startswith("<a id=")}
    fragments |= {
        slugify(line.lstrip("#").strip(), "-")
        for line in page.splitlines()
        if line.startswith("## ")
    }
    assert set(LINKED_FRAGMENTS) <= fragments
    assert "github.com" not in generated


# --- item 6: the notebook checks, unit D ---


# the notebook of the perfect-foresight application, committed with the
# outputs of its execution
PERFECT_FORESIGHT_NOTEBOOK = (
    ROOT
    / "applications"
    / "consumption-perfect-foresight-crra"
    / "code"
    / "closed-form-and-grid.ipynb"
)
# the intended refusal of each cell tagged `raises-exception`, by the cell's
# id: the class of the exception and the condition its message names
INTENDED_REFUSALS = {
    "7297042b": ("ValueError", "does not satisfy the condition β < R^(ρ - 1)"),
    "3c9d3030": ("ValueError", "lies outside the declared set (0, R)"),
    "66c54820": ("ValueError", "total wealth m - L = 0.0 is not positive"),
}


def _notebook_checks():
    """The committed notebook of the perfect-foresight application, read as
    JSON: every code cell holds an execution count, and the counts run in
    order from 1, so the cells were executed once from a fresh kernel; an
    error output stands only in the three cells tagged `raises-exception`,
    one in each, and each is the refusal that the markdown cell before it
    states: the declared set of the discount factor, whose upper bound is
    the return impatience condition, the declared set (0, R) of the growth
    factor, and the evaluation of the
    consumption function at the natural borrowing limit."""
    cells = json.loads(PERFECT_FORESIGHT_NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    code = [cell for cell in cells if cell["cell_type"] == "code"]
    assert [cell["execution_count"] for cell in code] == list(range(1, len(code) + 1))
    tagged = {
        cell["id"] for cell in code if "raises-exception" in cell["metadata"].get("tags", [])
    }
    assert tagged == set(INTENDED_REFUSALS)
    errors = {
        cell["id"]: [output for output in cell["outputs"] if output["output_type"] == "error"]
        for cell in code
    }
    assert {identifier for identifier, found in errors.items() if found} == tagged
    for identifier, (name, condition) in INTENDED_REFUSALS.items():
        (error,) = errors[identifier]
        assert error["ename"] == name, (identifier, error["ename"])
        assert condition in error["evalue"], (identifier, error["evalue"])


# --- item 6: the one test, which calls both helpers ---


def test_item_6_the_generated_method_and_grid_references_cover_every_record_reproducibly(request):
    """Item 6: the generated method and grid references, unit E1's part,
    through `_reference_checks`, and the executed notebook of the
    perfect-foresight application, unit D's part, through
    `_notebook_checks`; the public views are compared once by the snapshot
    guard, `test_snapshot.py`."""
    _reference_checks(request)
    _notebook_checks()
