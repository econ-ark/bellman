"""The acceptance file of unit C of the build of specification 0.6 for the
trellis demand: one test for each of the brief's acceptance items 1 and 2, on
the two recipes of `applications/cons-port`, consumption first
and portfolio first, whose methods files bind `!egm` with its block on the
consumption stage, `!time-iteration` with its block on the portfolio stage
and `!marginals` on the value builders of both. The connection tests of
`test_amd_comp_001.py` are run unchanged beside this file. The rulings the
build took are the rows SC of the development repository's decisions file
`SC-the-trellis-and-the-cards.md`.
"""

from __future__ import annotations

import pytest
from conftest import ROOT

from bellman.factory.connections import connection_report
from bellman.factory.elaboration import bind_stage, elaborate_stage
from bellman.factory.joins import derivative_missing
from bellman.factory.recipe import load_recipe
from bellman.factory.trellis import elaborate_trellis, methodize_trellis
from bellman.stage import load_stage

DEMONSTRATION = ROOT / "applications/cons-port/declaration"
RECIPES = ("spec.cons-port.yml", "spec.port-cons.yml")


def _methodized(recipe, without_marginals=(), without_representation=()):
    """The demonstration's trellis of `recipe`, elaborated and methodized
    from its recipe, with the `!marginals` lines of the stages
    `without_marginals` names, and the `!Linear` lines of the stages
    `without_representation` names, taken out of their methods mappings."""
    syntactic = load_recipe(DEMONSTRATION, recipe)
    removed = {key: {"marginals"} for key in without_marginals}
    for key in without_representation:
        removed.setdefault(key, set()).add("Linear")
    for period in syntactic["periods"]:
        for key, tags in removed.items():
            methods = period["stages"][key]["methods"]
            methods["methods"] = [
                entry
                for entry in methods["methods"]
                if entry["method"].get("__yaml_tag__") not in tags
            ]
    return methodize_trellis(elaborate_trellis(syntactic), syntactic)


@pytest.mark.parametrize("recipe", RECIPES)
def test_item_1_both_orders_pass_the_route_certification_under_the_bindings(recipe):
    """In both orders every route of the six periods is certified once the
    methods are bound, on the values alone, and no derivative reading is
    unmet: the consumption stage's block reads `D_{a}V[>]`, and the value
    the stage after it exports carries the derivative by its stated line
    (AMD-MB-001 R5)."""
    trellis = _methodized(recipe)
    for period in trellis["periods"]:
        assert "block cons_egm.bl" in str(period["stages"]["cons"].methods)
        assert "block port_foc.bl" in str(period["stages"]["port"].methods)
    routes = connection_report(trellis).routes
    assert len(routes) == 17
    assert [route for route in routes if route.status != "certified"] == []
    assert derivative_missing(trellis) == ()


@pytest.mark.parametrize(("recipe", "uncertified"), [(RECIPES[0], 6), (RECIPES[1], 5)])
def test_item_2_without_the_portfolio_marginals_the_route_is_reported_and_nothing_refuses(
    recipe, uncertified
):
    """With the portfolio stage's `!marginals` line taken out, the methods
    bind and nothing refuses, every route is certified on the values alone,
    and nothing is reported, since the stage's `!Linear` representation of
    its value evaluates the first derivative, as its row of the method table
    says (D6). With that representation taken out as well, the trellis
    reports one `derivative-missing` per route into the portfolio stage, at
    the portfolio stage: the consumption stage's block reads `D_{a}V[>]`, the
    discounting stage passes the value through by `V[<] = V` and `V = β*V[>]`
    under its identity laws (D3), and the portfolio stage's exported value
    carries no derivative in `k`; the diagnostic names that stage, its value
    and the coordinate (AMD-MB-001 R5, D3, D5, D6)."""
    trellis = _methodized(recipe, without_marginals=("port",))
    routes = connection_report(trellis).routes
    assert [route for route in routes if route.status != "certified"] == []
    assert derivative_missing(trellis) == ()
    trellis = _methodized(recipe, without_marginals=("port",), without_representation=("port",))
    routes = connection_report(trellis).routes
    assert [route for route in routes if route.status != "certified"] == []
    into_port = [
        route for route in routes if (route.source[1], route.destination[1]) == ("disc", "port")
    ]
    assert len(into_port) == uncertified
    found = derivative_missing(trellis)
    assert [diagnostic.rule for diagnostic in found] == ["derivative-missing"] * uncertified
    assert all(diagnostic.candidates == ("port:function:dcsn:V", "k") for diagnostic in found)
    first = found[0]
    assert first.address == f"periods[{into_port[0].destination[0]}].stages['port']"
    assert "stage 'port'" in first.message
    assert "`D_{a}V[>]`" in first.message and "pass-through of disc" in first.message
    assert "!marginals" in first.message


def test_the_recipe_route_reads_the_block_file_beside_the_methods_file(tmp_path, monkeypatch):
    """The consumption stage's record in the recipe `spec.cons-port.yml`
    supplies its methods as a mapping, whose `block: cons_egm.bl` is read
    beside `declaration/methods/cons.yml`, the file the record's
    `source_lists` names, whatever the working directory: `bind_stage`, the
    route by which Bellman Workbench binds the occurrence a page shows,
    `elaborate_stage` of the record and the trellis route each bind the
    block (decisions SC-5 and SC-16)."""
    monkeypatch.chdir(tmp_path)
    syntactic = load_recipe(DEMONSTRATION, RECIPES[0])
    record = syntactic["periods"][0]["stages"]["cons"]
    symbolic = elaborate_stage(load_stage(DEMONSTRATION / "stages/cons/cons.bl"), bind=False)
    bound = bind_stage(symbolic, record)
    assert bound.failed == {}
    assert "policy                    !egm   block cons_egm.bl" in str(bound.stage.methods)
    assert "block cons_egm.bl" in str(elaborate_stage(record).methods)
    trellis = methodize_trellis(elaborate_trellis(syntactic), syntactic)
    assert "block cons_egm.bl" in str(trellis["periods"][0]["stages"]["cons"].methods)
