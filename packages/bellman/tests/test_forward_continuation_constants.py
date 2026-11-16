"""Continuation constants read by a forward branch."""

from bellman.stage import elaborate_text
from bellman.trellis import connection_report, elaborate_trellis
from test_modular_fields import KEPT_BOUND, RETIREMENT, period


def test_a_constant_read_by_a_forward_branch_has_a_connected_supplier():
    text = RETIREMENT.replace("a_r = a", "a_r = a + L_r[>]").replace(
        "(a : ℝ, d : !ctrl", "(a : ℝ, L_r[>], d : !ctrl"
    ).replace("min(L_w[>], L_r[>])", "L_w[>]")
    recipe = {
        "periods": [period(
            {"choice": text, "work": KEPT_BOUND, "retire": KEPT_BOUND},
            [{"a_w": "work.k", "a_r": "retire.k", "L_w": "work.L", "L_r": "retire.L"}],
        )],
        "inter_connectors": [],
    }
    trellis = elaborate_trellis(recipe)
    choice = trellis["periods"][0]["stages"]["choice"]
    assert "L_r" in {port.identity.field for port in choice.builder.bwd.signature().inputs}
    routes = connection_report(trellis).routes
    assert all(route.status == "certified" for route in routes)
    retire, = (route for route in routes if route.branch == "retire")
    assert any(component.required.endswith(":L_r") for component in retire.components)

    unread = elaborate_text(text.replace("a_r = a + L_r[>]", "a_r = a"), "choice.bl")
    assert "L_r" not in {port.identity.field for port in unread.builder.bwd.signature().inputs}
