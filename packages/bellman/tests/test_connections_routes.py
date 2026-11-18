"""Routes between periods and within a period: the certification of a route,
the diagnostics of the routes beside the diagnostic of a connector, and the
transport of points, derivatives, Hessians and atoms along a route.

A trellis whose period holds an authored cycle is still elaborated, and a
transport along a route on the cycle is refused.
"""

from fractions import Fraction

import numpy
import pytest
from application_files import ROOT
from stage_builders import stage_from_text
from stage_texts import (
    BUFFER_STOCK_READING_THE_SECOND_FIELD,
    BUFFER_STOCK_WRITING_THE_SECOND_FIELD,
    UNADMITTED_FAMILY_AFTER_DECISION,
    buffer_stock_text,
)
from trellises import (
    candidate_groups,
    connection_between,
    one_route,
    period_record,
    printed_pairs,
    selection_of_periods,
)

from bellman.refusal_examples import CORPUS as REFUSAL_EXAMPLES
from bellman.stage import load_stage
from bellman.trellis import (
    connection_report,
    elaborate_trellis,
    pull_back,
    transport_atoms,
    transport_hessian,
    transport_point,
    transport_vector,
)

# a stage that carries `a`, `b` and `c` unchanged from its arrival perch to
# its continuation perch, so that the pairs of a connector between two of its
# occurrences may take the three fields in any order
THREE_FIELDS = """@stage: three_fields
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ, b : ℝ, c : ℝ) : !arvl -> (a_d : ℝ, b_d : ℝ, c_d : ℝ) : !dcsn] {
    a_d = a
    b_d = b
    c_d = c
}
[id=dcsn_to_cntn, (a_d, b_d, c_d) : !dcsn -> (a : ℝ, b : ℝ, c : ℝ) : !cntn] {
    a = a_d
    b = b_d
    c = c_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# a branching stage whose two branches continue to `(x_up, y_up)` and
# `(x_dn, y_dn)` and whose decision value states its derivatives in the
# coordinates of the decision perch, so that a connector may join both
# branches of one occurrence to the arrival fields `(x, y)` of another
MERGE = """@stage: merge
β : (0,1)
[id=arvl_to_dcsn, (x : ℝ₊, y : ℝ₊) : !arvl -> (x_d : ℝ₊, y_d : ℝ₊) : !dcsn] {
    x_d = x
    y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d, d : !ctrl @ {up, down}) : !dcsn -> ()] {
    [label=up,   () -> (x_up : ℝ₊, y_up : ℝ₊) : !cntn] {
        x_up = x_d
        y_up = y_d
    }
    [label=down, () -> (x_dn : ℝ₊, y_dn : ℝ₊) : !cntn] {
        x_dn = x_d
        y_dn = y_d
    }
}
[id=cntn_to_dcsn, (V_up[>] : ℝ @ !vlu, V_dn[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V          = (V_up[>], V_dn[>])[d]
    D_{x_d}V   = (D_{x_up}V_up[>], D_{x_dn}V_dn[>])[d]
    D_{y_d}V   = (D_{y_up}V_up[>], D_{y_dn}V_dn[>])[d]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V_up[>], V_dn[>]) : !cntn -> (d : {up, down} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_up[>], V_dn[>])
}
"""


def route_line(report):
    """The one line of the printed connection report `report` that prints a
    route."""
    (line,) = [line for line in str(report).splitlines() if line.startswith("route ")]
    return line


@pytest.fixture(scope="module")
def three_field_stage():
    return stage_from_text(THREE_FIELDS, "three_fields.bl")


@pytest.fixture(scope="module")
def merge_stage():
    return stage_from_text(MERGE, "merge.bl")


@pytest.fixture(scope="module")
def durables_selection(durables_trellis):
    """The selection of the connections of the durables trellis of 51
    periods."""
    return connection_report(durables_trellis).selection


@pytest.fixture(scope="module")
def rotating_routes(three_field_stage):
    """The routes S → T and T → U of one period of three occurrences of the
    three-field stage: the first connector takes `a` into `b`, `b` into `c`
    and `c` into `a`, and the second swaps `b` and `c`."""
    selection = selection_of_periods(
        [
            period_record(
                {"S": three_field_stage, "T": three_field_stage, "U": three_field_stage},
                [
                    {"S.a": "T.b", "S.b": "T.c", "S.c": "T.a"},
                    {"T.a": "U.a", "T.b": "U.c", "T.c": "U.b"},
                ],
            )
        ]
    )
    # the source, the branch and the destination of a route, each occurrence
    # at its position (h, key): the index of its period and its stage key
    return (
        one_route(selection, (0, "S"), None, (0, "T")),
        one_route(selection, (0, "T"), None, (0, "U")),
    )


@pytest.fixture(scope="module")
def swap_route(two_state_identity_stage):
    """The route S → T of two occurrences of the two-field stage, whose
    connector takes `a` into `b` and `b` into `a`."""
    selection = selection_of_periods(
        [
            period_record(
                {"S": two_state_identity_stage, "T": two_state_identity_stage},
                [{"S.a": "T.b", "S.b": "T.a"}],
            )
        ]
    )
    return one_route(selection, (0, "S"), None, (0, "T"))


@pytest.fixture(scope="module")
def pension_stages(pension_trellis_with_arrival_builders):
    """The stage occurrences of the terminal period, `periods[0]`, of the
    pension trellis, whose retirement choice continues on the branches
    `work` and `retire` into the terminal stage's arrival fields `y_f_T` and
    `y_p_T`."""
    return pension_trellis_with_arrival_builders["periods"][0]["stages"]


@pytest.fixture(scope="module")
def one_field_selection(pension_stages):
    """The selection of the terminal period, `periods[0]`, of the pension
    trellis under one connector, from `y_f_wk` of the work branch into
    `y_f_T`."""
    return selection_of_periods([period_record(pension_stages, [{"y_f_wk": "y_f_T"}])])


@pytest.fixture(scope="module")
def incomplete_route(one_field_selection):
    """The route of the work branch into the terminal stage, whose connector
    supplies `y_f_T` alone."""
    return one_route(one_field_selection, (0, "retire_choice"), "work", (0, "terminal"))


@pytest.fixture(scope="module")
def two_branch_selection(pension_stages):
    """The selection of the terminal period, `periods[0]`, of the pension
    trellis under one connector that supplies `y_f_T` from the work branch
    and `y_p_T` from the retire branch."""
    return selection_of_periods(
        [period_record(pension_stages, [{"y_f_wk": "y_f_T", "y_p_rt": "y_p_T"}])]
    )


@pytest.fixture(scope="module")
def merge_selection(merge_stage):
    """The selection of two occurrences S and T of the merge stage, whose
    connector joins both branches of S, `(x_up, y_up)` and `(x_dn, y_dn)`,
    to the arrival fields `(x, y)` of T."""
    return selection_of_periods(
        [
            period_record(
                {"S": merge_stage, "T": merge_stage},
                [{"S.x_up": "T.x", "S.y_up": "T.y", "S.x_dn": "T.x", "S.y_dn": "T.y"}],
            )
        ]
    )


@pytest.fixture(scope="module")
def cycle_report(merge_stage):
    """The connection report of one period of three occurrences A, B and C of
    the merge stage, whose up branches join A to B, B to C and C to A, an
    authored cycle, and whose down branch joins A to C."""
    connectors = [
        {f"A.{source}": f"B.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"B.{source}": f"C.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"C.{source}": f"A.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"A.{source}": f"C.{target}" for source, target in (("x_dn", "x"), ("y_dn", "y"))},
    ]
    trellis = elaborate_trellis(
        {
            "periods": [
                period_record({"A": merge_stage, "B": merge_stage, "C": merge_stage}, connectors)
            ],
            "inter_connectors": [],
        }
    )
    return connection_report(trellis)


@pytest.fixture(scope="module")
def cycle_route(cycle_report):
    """The route of the down branch from A into C, which lies on a cycle with
    the route of the up branch from C into A."""
    return one_route(cycle_report.selection, (0, "A"), "down", (0, "C"))


@pytest.fixture(scope="module")
def no_law_selection(identity_stage):
    """The selection of one period of an occurrence S of the stage
    `UNADMITTED_FAMILY_AFTER_DECISION`, whose law of motion draws a shock of a
    family that the package does not construct, and an occurrence T of the
    unchanged stage, which carries `a` unchanged from its arrival perch to its
    continuation perch, joined by `{S.a: T.a}`."""
    unadmitted_family_after_decision_stage = stage_from_text(
        UNADMITTED_FAMILY_AFTER_DECISION, "no_law.bl"
    )
    return selection_of_periods(
        [
            period_record(
                {"S": unadmitted_family_after_decision_stage, "T": identity_stage},
                [{"S.a": "T.a"}],
            )
        ]
    )


@pytest.fixture(scope="module")
def no_law_route(no_law_selection):
    (route,) = no_law_selection.routes
    return route


def test_a_route_into_a_period_without_a_field_that_the_earlier_reads_is_uncertified_naming_it():
    """The connection report prints the route into the buffer-stock stage
    file, which writes `V[<]` and `L[<]` and not `Θ[<]`, as uncertified,
    naming `Θ` as the component that the later period does not supply."""
    report = connection_between(BUFFER_STOCK_READING_THE_SECOND_FIELD, buffer_stock_text())
    (route,) = report.routes
    assert route.status == "uncertified"
    assert route_line(report) == (
        "route periods[1].bs → periods[0].bs: uncertified, (a) → (k); the backward component "
        "buffer_stock:function:cntn:Θ is incompatible: every value periods[0].bs supplies "
        "answers another requirement of periods[1].bs, and none is left for "
        "buffer_stock:function:cntn:Θ"
    )


def test_a_route_into_a_period_that_writes_the_field_is_certified_with_each_field_paired_by_name():
    """The connection report prints the route into a later period that writes
    `Θ[<]` beside `V[<]` and `L[<]` as certified, the route pairing each of
    the three fields that the earlier period requires, in the order in which
    its headers list them, with the field of its name."""
    report = connection_between(
        BUFFER_STOCK_READING_THE_SECOND_FIELD, BUFFER_STOCK_WRITING_THE_SECOND_FIELD
    )
    (route,) = report.routes
    assert route_line(report) == "route periods[1].bs → periods[0].bs: certified, (a) → (k)"
    assert [(part.required, part.supplied, part.rule) for part in route.components] == [
        ("buffer_stock:function:cntn:V", "buffer_stock:function:arvl:V", "equal name"),
        ("buffer_stock:function:cntn:L", "buffer_stock:function:arvl:L", "equal name"),
        ("buffer_stock:function:cntn:Θ", "buffer_stock:function:arvl:Θ", "equal name"),
    ]


def test_both_consumption_stages_of_the_terminal_durables_period_continue_to_the_bequest(
    durables_selection,
):
    """The first connector of the terminal period of the durables trellis
    joins the three continuation fields of each of the two consumption
    stages to the three arrival fields of the bequest stage."""
    terminal = [
        (writing, reading)
        for writing, reading, address in printed_pairs(durables_selection)
        if address == "periods[0].connectors[0]"
    ]
    assert sorted(terminal) == sorted(
        [
            ("periods[0].keeper_cons.a_nxt_kp", "periods[0].bequest.a_bq"),
            ("periods[0].keeper_cons.h_nxt_kp", "periods[0].bequest.h_bq"),
            ("periods[0].keeper_cons.z_nxt_kp", "periods[0].bequest.z_bq"),
            ("periods[0].adjuster_cons.a_nxt_adj", "periods[0].bequest.a_bq"),
            ("periods[0].adjuster_cons.h_nxt_adj", "periods[0].bequest.h_bq"),
            ("periods[0].adjuster_cons.z_nxt_adj", "periods[0].bequest.z_bq"),
        ]
    )


def test_each_continuation_field_of_the_tenure_stage_is_paired_under_the_branch_that_writes_it(
    durables_selection,
):
    """In the second connector of the terminal period, each pair from a
    continuation field of the tenure stage carries the label of the branch
    whose block writes the field, and reads a field of the consumption stage
    of that branch."""
    branches = sorted(
        (pair.writing.field, pair.reading.field, pair.writing.branch, pair.reading.key)
        for pair in durables_selection.pairs
        if pair.address == "periods[0].connectors[1]"
    )
    assert branches == [
        ("h_kp", "h_d", "keep", "keeper_cons"),
        ("w_adj", "m", "adjust", "adjuster_cons"),
        ("w_kp", "w_d", "keep", "keeper_cons"),
        ("z_adj", "z_d", "adjust", "adjuster_cons"),
        ("z_kp", "z_d", "keep", "keeper_cons"),
    ]


def test_the_selection_of_the_durables_trellis_infers_rejects_and_diagnoses_nothing(
    durables_selection,
):
    """Every pair of the durables trellis is authored, since no continuation
    field of a period shares its name with an arrival field of that period:
    its selection infers no pair and holds no group of candidates, no
    rejected candidate and no diagnostic."""
    assert {pair.origin for pair in durables_selection.pairs} == {"authored"}
    assert candidate_groups(durables_selection) == {}
    assert durables_selection.diagnostics == () and durables_selection.rejected == ()
    assert durables_selection.counts["inferred"] == 0


def test_the_inter_period_mappings_of_the_durables_trellis_resolve_300_pairs(
    durables_selection,
):
    """The mappings between the periods of the durables trellis resolve 300
    pairs."""
    # 50 mappings join the 51 periods, and each writes six fields
    inter_period = [
        pair for pair in durables_selection.pairs if pair.address.startswith("inter_connectors")
    ]
    assert len(inter_period) == 300


def test_every_route_of_the_durables_trellis_is_certified(durables_selection):
    """Each of the 204 routes of the durables trellis is certified."""
    assert durables_selection.counts["routes"] == durables_selection.counts["certified"] == 204


# the permutation of a route: entry i is the position, among the continuation
# fields of the source, of the field that arrival field i of the destination
# takes; the inverse gives, for each continuation field, the position of the
# arrival field that takes it
@pytest.mark.parametrize(
    ("branch", "destination", "fields", "permutation", "law", "ages", "values"),
    [
        pytest.param(
            "keep",
            "keeper_cons",
            (("w_kp", "h_kp", "z_kp"), ("w_d", "h_d", "z_d")),
            (0, 1, 2),
            "tenure:measure:cntn:keep",
            ("tenure:function:cntn:age_kp", "keeper_cons:function:dcsn:age"),
            ("tenure:function:cntn:V_kp", "keeper_cons:function:dcsn:V"),
            id="keep",
        ),
        pytest.param(
            "adjust",
            "adjuster_cons",
            (("w_adj", "z_adj"), ("m", "z_d")),
            (0, 1),
            "tenure:measure:cntn:adjust",
            ("tenure:function:cntn:age_adj", "adjuster_cons:function:dcsn:age"),
            ("tenure:function:cntn:V_adj", "adjuster_cons:function:dcsn:V"),
            id="adjust",
        ),
    ],
)
def test_the_route_of_each_branch_of_the_tenure_stage_carries_its_fields_under_its_own_law(
    durables_selection, branch, destination, fields, permutation, law, ages, values
):
    """The route of each branch of the tenure stage takes the continuation
    fields that the branch writes, in their order and each through an
    authored pair, to the decision fields of the consumption stage of the
    branch, under the joint law of the branch; it pairs the age of the
    branch with the age of that stage by the pair that the connector writes,
    and then the continuation value of the branch with the value of that
    stage, one value for the one role."""
    route = one_route(durables_selection, (0, "tenure"), branch, (0, destination))
    assert (route.source_fields, route.destination_fields) == fields
    assert route.permutation == permutation
    assert route.law == law
    assert [pair.origin for pair in route.pairs] == ["authored"] * len(permutation)
    assert [(part.required, part.supplied, part.rule) for part in route.components] == [
        (*ages, "explicit connector"),
        (*values, "one wire per role"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("keeper_cons", id="the keeper's consumption stage"),
        pytest.param("adjuster_cons", id="the adjuster's consumption stage"),
    ],
)
def test_the_route_of_each_consumption_stage_into_the_bequest_is_certified_by_authored_pairs(
    durables_selection, source
):
    """The route of each consumption stage of the terminal period into the
    bequest stage is certified, its three arrival fields each reached by an
    authored pair."""
    route = one_route(durables_selection, (0, source), None, (0, "bequest"))
    assert route.status == "certified" and route.destination_fields == ("a_bq", "h_bq", "z_bq")
    assert [pair.origin for pair in route.pairs] == ["authored"] * 3


def test_the_keep_route_whose_permutation_is_the_identity_transports_an_atom_to_itself(
    durables_selection,
):
    """An atom transported along the route of the keep branch, whose fields
    keep their order, keeps its point and its mass."""
    keep = one_route(durables_selection, (0, "tenure"), "keep", (0, "keeper_cons"))
    # one atom, written (point, mass)
    assert transport_atoms(keep, (((1, 2, 3), 0.3),)) == (((1, 2, 3), 0.3),)


def test_a_connector_that_rotates_three_fields_gives_its_route_the_permutation_and_its_inverse(
    rotating_routes,
):
    """The route of the connector that takes `a` into `b`, `b` into `c` and
    `c` into `a` is certified with the permutation (2, 0, 1) and the inverse
    (1, 2, 0)."""
    first, _ = rotating_routes
    assert first.status == "certified"
    assert first.permutation == (2, 0, 1) and first.inverse == (1, 2, 0)


def test_a_point_is_transported_into_the_order_of_the_arrival_fields_of_the_destination(
    rotating_routes,
):
    """The point (1, 2, 3) at `(a, b, c)` of S is (3, 1, 2) at `(a, b, c)` of
    T."""
    first, _ = rotating_routes
    assert transport_point(first, (1, 2, 3)) == (3, 1, 2)


def test_the_components_of_a_derivative_are_transported_into_the_order_of_the_source(
    rotating_routes,
):
    """The components of a derivative in the order of the arrival fields of T
    are given in the order of the continuation fields of S, by the
    inverse."""
    first, _ = rotating_routes
    assert transport_vector(first, ("ga", "gb", "gc")) == ("gb", "gc", "ga")


def test_both_indices_of_a_hessian_are_transported_into_the_order_of_the_source(
    rotating_routes,
):
    """The rows and the columns of a Hessian in the order of the arrival
    fields of T are given in the order of the continuation fields of S."""
    first, _ = rotating_routes
    # the entry of row i and column j is 10 * (i + 1) + (j + 1)
    hessian = ((11, 12, 13), (21, 22, 23), (31, 32, 33))
    assert transport_hessian(first, hessian) == ((22, 23, 21), (32, 33, 31), (12, 13, 11))


def test_a_transport_refuses_a_point_with_the_wrong_number_of_coordinates(swap_route):
    """A transport along the route of two coordinates refuses a point of
    one."""
    with pytest.raises(ValueError, match="has 2 entries; 1 given"):
        transport_point(swap_route, (1,))


def test_the_pullback_along_two_routes_is_the_composition_of_their_pullbacks_in_reverse_order(
    rotating_routes,
):
    """A function of the arrival fields of U, pulled back along T → U and then
    along S → T, answers at a point of S its value at the point transported
    along S → T and then along T → U."""
    first, second = rotating_routes
    assert second.status == "certified"
    pulled = pull_back(first, pull_back(second, lambda a, b, c: (a, b, c)))
    assert (
        pulled(1, 2, 3) == transport_point(second, transport_point(first, (1, 2, 3))) == (3, 2, 1)
    )


# the masses of the atoms of each row, all at the point (1, 2, 3)
@pytest.mark.parametrize(
    "masses",
    [
        pytest.param((-0.5,), id="a negative mass"),
        pytest.param((float("nan"),), id="a mass that is not a number"),
        pytest.param((float("inf"),), id="an infinite mass"),
        pytest.param((-float("inf"),), id="a negative infinite mass"),
        pytest.param(
            (1.0, -0.5),
            id="a negative mass after a positive mass at the same point, a sum of 0.5 that the "
            "check of the accumulated mass admits",
        ),
    ],
)
def test_an_atom_whose_mass_is_negative_or_not_finite_is_refused(rotating_routes, masses):
    """The transport of atoms refuses an atom whose mass is not a finite
    nonnegative number."""
    first, _ = rotating_routes
    with pytest.raises(ValueError, match="nonnegative number"):
        transport_atoms(first, tuple(((1, 2, 3), mass) for mass in masses))


# 10**400 lies far beyond the largest double, about 1.8 * 10**308, and
# 2**64 - 1 is the largest unsigned 64-bit integer
@pytest.mark.parametrize(
    ("masses", "total"),
    [
        pytest.param((10**400, 10**400), 2 * 10**400, id="two integers beyond the largest double"),
        pytest.param(
            (Fraction(10**400, 3), 10**400),
            Fraction(10**400, 3) + 10**400,
            id="a fraction and an integer beyond the largest double",
        ),
        pytest.param(
            (numpy.uint64(2**64 - 1), numpy.uint64(2**64 - 1)),
            2 * (2**64 - 1),
            id="two unsigned 64-bit integers of NumPy whose sum needs 65 bits",
        ),
    ],
)
def test_the_masses_of_two_atoms_with_one_image_are_summed_exactly(swap_route, masses, total):
    """The atoms at (1, 2) are transported to (2, 1), their integer or
    fractional masses summed exactly."""
    atoms = tuple(((1, 2), mass) for mass in masses)
    assert transport_atoms(swap_route, atoms) == (((2, 1), total),)


@pytest.mark.parametrize(
    "masses",
    [
        pytest.param((1e308, 1e308), id="two doubles whose sum is beyond the largest double"),
        pytest.param((10**400, 0.5), id="an integer beyond the largest double and a double"),
    ],
)
def test_an_accumulated_mass_that_is_not_a_finite_number_is_refused(swap_route, masses):
    """The transport of two atoms with one image refuses a sum of their masses
    that is not a finite number."""
    with pytest.raises(ValueError, match="accumulated mass.*finite"):
        transport_atoms(swap_route, tuple(((1, 2), mass) for mass in masses))


def test_a_route_that_supplies_one_of_two_arrival_fields_is_incomplete_and_names_the_other(
    incomplete_route,
):
    """The route of the work branch into the terminal stage, whose connector
    supplies `y_f_T` alone, is incomplete and uncertified, with no
    permutation, and its obligation names `y_p_T`."""
    assert (
        incomplete_route.state,
        incomplete_route.status,
        incomplete_route.permutation,
    ) == ("incomplete", "uncertified", ())
    assert any(
        "no selected pair supplies the arrival coordinate y_p_T" in said
        for said in incomplete_route.obligations
    )


def test_an_incomplete_route_is_diagnosed_under_route_incomplete_at_its_connector(
    one_field_selection,
):
    """The connector that supplies one of the two arrival fields of the
    terminal stage carries one diagnostic, under `route-incomplete`."""
    assert [
        diagnostic.rule
        for diagnostic in one_field_selection.diagnostics
        if diagnostic.address == "periods[0].connectors[0]"
    ] == ["route-incomplete"]


# each row: the route, the transport, its argument, a point or atoms written
# (point, mass), and a phrase of the refusal
@pytest.mark.parametrize(
    ("route_fixture", "transport", "argument", "phrase"),
    [
        pytest.param(
            "incomplete_route",
            transport_point,
            (1.0, 2.0),
            "not certified",
            id="a point along an incomplete route",
        ),
        pytest.param(
            "incomplete_route",
            transport_atoms,
            (((1.0, 2.0), 1.0),),
            "not certified",
            id="an atom along an incomplete route",
        ),
        pytest.param(
            "cycle_route",
            transport_point,
            (1, 2),
            "not certified",
            id="a point along a complete route on an authored cycle, uncertified for the cycle",
        ),
        pytest.param(
            "no_law_route",
            transport_atoms,
            (((1.0,), 1.0),),
            "no joint law",
            id="an atom along a route without a joint law, the refusal naming the law",
        ),
    ],
)
def test_a_route_that_is_not_certified_transports_nothing(
    request, route_fixture, transport, argument, phrase
):
    """A transport along a route that is not certified is refused."""
    route = request.getfixturevalue(route_fixture)
    assert route.status == "uncertified"
    with pytest.raises(ValueError, match=phrase):
        transport(route, argument)


@pytest.mark.parametrize(
    ("branch", "phrase"),
    [
        pytest.param("work", "mutually exclusive branches work and retire", id="work"),
        pytest.param("retire", "mutually exclusive branches retire and work", id="retire"),
    ],
)
def test_compatible_pairs_from_two_exclusive_branches_leave_each_route_incomplete_naming_both(
    two_branch_selection, branch, phrase
):
    """Where the work branch supplies one arrival field of the terminal stage
    and the retire branch the other, the route of each branch is incomplete,
    although its one pair is compatible, its obligation naming the two
    branches."""
    route = one_route(two_branch_selection, (0, "retire_choice"), branch, (0, "terminal"))
    assert [pair.compatibility for pair in route.pairs] == ["compatible"]
    assert route.state == "incomplete"
    assert any(phrase in said for said in route.obligations)


@pytest.mark.parametrize(
    ("branch", "law"),
    [
        pytest.param("up", "merge:measure:cntn:up", id="up"),
        pytest.param("down", "merge:measure:cntn:down", id="down"),
    ],
)
def test_each_branch_joined_into_one_destination_has_a_certified_route_under_its_own_law(
    merge_selection, branch, law
):
    """Each branch of S, joined with the other to the arrival fields of T, has
    a certified route under the joint law of the branch, with no diagnostic
    in the selection."""
    route = one_route(merge_selection, (0, "S"), branch, (0, "T"))
    assert route.status == "certified" and merge_selection.diagnostics == ()
    assert route.law == law


def test_the_up_route_pairs_the_continuation_value_of_the_branch_with_the_destination_value(
    merge_selection,
):
    """The route of the up branch of S pairs the continuation value `V_up` of
    S with the value `V` of T."""
    up = one_route(merge_selection, (0, "S"), "up", (0, "T"))
    assert [
        (part.required.rsplit(":", 1)[1], part.supplied.rsplit(":", 1)[1])
        for part in up.components
    ] == [("V_up", "V")]


def test_atoms_along_the_two_branches_keep_their_points_and_masses_which_sum_to_one(
    merge_selection,
):
    """The atoms of each branch, whose fields keep their order, keep their
    points and their masses, which sum to one over the two branches."""
    up = one_route(merge_selection, (0, "S"), "up", (0, "T"))
    down = one_route(merge_selection, (0, "S"), "down", (0, "T"))
    # atoms written (point, mass), of total mass 0.4 on the up branch and 0.6
    # on the down branch
    of_up = transport_atoms(up, (((1.0, 2.0), 0.3), ((3.0, 4.0), 0.1)))
    of_down = transport_atoms(down, (((1.0, 2.0), 0.6),))
    assert of_up == (((1.0, 2.0), 0.3), ((3.0, 4.0), 0.1)) and of_down == (((1.0, 2.0), 0.6),)
    assert sum(mass for _, mass in of_up) + sum(mass for _, mass in of_down) == 1.0


def test_a_complete_compatible_route_on_an_authored_cycle_is_uncertified_for_the_cycle(
    cycle_route,
):
    """The route of the down branch from A into C, which the cycle that runs
    through the up branches alone leaves out, is complete, compatible and
    has its joint law, and it is uncertified with an obligation that names
    the authored cycle."""
    assert cycle_route.state == "complete" and cycle_route.compatibility == "compatible"
    assert cycle_route.law == "merge:measure:cntn:down"
    assert cycle_route.status == "uncertified"
    assert any("authored cycle" in obligation for obligation in cycle_route.obligations)


def test_every_route_of_a_period_with_an_authored_cycle_is_uncertified(cycle_report):
    """Each of the four routes of the period whose up branches form an
    authored cycle is uncertified, with an obligation that names the cycle."""
    assert [route.status for route in cycle_report.routes] == ["uncertified"] * 4
    assert [
        any("authored cycle" in obligation for obligation in route.obligations)
        for route in cycle_report.routes
    ] == [True] * 4


def test_a_complete_route_from_a_stage_that_writes_no_joint_law_is_uncertified_for_the_law(
    no_law_selection, no_law_route
):
    """The route of the compatible authored pair from the stage that writes no
    joint law on its continuation state is complete and uncertified, its
    obligation naming the law that is not written."""
    (pair,) = [pair for pair in no_law_selection.pairs if pair.origin == "authored"]
    assert pair.compatibility == "compatible"
    assert (no_law_route.state, no_law_route.law, no_law_route.status) == (
        "complete",
        None,
        "uncertified",
    )
    assert any(
        "is not constructed, so no joint law on (a) is written" in said
        for said in no_law_route.obligations
    )


def test_a_route_without_a_joint_law_is_diagnosed_under_route_no_law(no_law_selection):
    """The selection of the period whose stage writes no joint law holds one
    diagnostic, under `route-no-law`."""
    assert [diagnostic.rule for diagnostic in no_law_selection.diagnostics] == ["route-no-law"]


# the example stages are two stage files of the portfolio-choice application:
# `disc`, the discounting stage, which arrives at `a` and continues to `a`,
# and `port`, the portfolio stage, which arrives at `k` and continues to
# `m_next`; each row: the example stage file of each stage key, the
# connectors of the period, the rule and the address of the connector's
# diagnostic, and the number of routes whose diagnostic depends on it
@pytest.mark.parametrize(
    ("examples", "connectors", "rule", "address", "diagnosed_routes"),
    [
        pytest.param(
            {"disc": "disc", "port": "port"},
            [{"disc.a": "port.k"}, {"port.m_next": "disc.a"}],
            "authored-cycle",
            "periods[0].connectors[0]",
            2,
            id="an authored cycle",
        ),
        pytest.param(
            {"S": "disc", "T": "port", "U": "port"},
            [{"S.a": "T.k"}, {"S.a": "U.k"}],
            "use-claimed-twice",
            "periods[0].connectors[1]",
            1,
            id="a use that two connectors claim",
        ),
    ],
)
def test_the_diagnostic_of_each_route_depends_on_the_diagnostic_of_the_connector(
    examples, connectors, rule, address, diagnosed_routes
):
    """Beside a diagnostic of a connector, the diagnostic of each route of the
    period depends on it, and it depends on no other diagnostic."""
    stages = {key: load_stage(ROOT / REFUSAL_EXAMPLES[name]) for key, name in examples.items()}
    trellis = elaborate_trellis(
        {"periods": [period_record(stages, connectors)], "inter_connectors": []}
    )
    diagnostics = connection_report(trellis).diagnostics
    (found,) = [diagnostic for diagnostic in diagnostics if diagnostic.rule == rule]
    assert (found.address, found.depends_on) == (address, None)
    assert [
        diagnostic.depends_on for diagnostic in diagnostics if diagnostic.rule.startswith("route-")
    ] == [address] * diagnosed_routes
