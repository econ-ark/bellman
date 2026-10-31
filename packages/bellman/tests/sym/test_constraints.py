"""Constraint syntax: CorrDef, feasible-set binders, slack lines.

Γ(x : ℝ₊) := (0, x] defines a correspondence (a set-expression body
on a typed binder). An operator binder carries its feasible set by the
typing colon, argmax_{cp : Γ(w)}, lowering to the In binder. A
statement may carry a complementary-slackness clause, `… ⟂ b >= 0`,
on residual or assertion lines. The glyph ⟂ has that one meaning: in
binder position it is rejected (one meaning per symbol, AAS, 9 Sep
2026). A signature side may be a bare single coordinate
(V : !dcsn -> …). R_{+} and R_{++} are ASCII-brace spellings of ℝ₊
and ℝ₊₊.
"""

import json

import pytest
from lark.exceptions import UnexpectedInput

from bellman.syntax.lower import parse_with_spans, to_json

STAGE = """@stage: t

b : ℝ₊
Γ(x : {rp}) := (0, x]

[id=pol, (b) -> (c : ℝ₊₊)] {{
    c = argmax_{{cp {sep} Γ(b)}}(u(cp)) ⟂ b >= 0    :: [id=optimality, !doc]
}}

[id=g, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {{
    V[<] = V
}}
"""


@pytest.mark.parametrize("rp", ["ℝ₊", "R_{+}", "R+"])
def test_constraint_constructs_parse_and_encode(rp):
    term, _ = parse_with_spans(STAGE.format(rp=rp, sep=":"))
    j = json.dumps(to_json(term), ensure_ascii=False)
    for node in ["CorrDef", "In", "Slack"]:
        assert node in j, f"missing {node}"


def test_a_perp_in_binder_position_is_a_syntax_error():
    # ⟂ means complementarity and nothing else; membership is the colon.
    with pytest.raises(UnexpectedInput):
        parse_with_spans(STAGE.format(rp="ℝ₊", sep="⟂"))


INEQUALITY_STAGE = """@stage: t

b : ℝ₊

[id=pol, (V[>] : ℝ @ !vlu, b) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= duinv(D_{b}V[>]) ⟂ b >= 0 :: [id=InvEuler]
    c    = c[>]                       :: [id=cons_choice]
}
"""


def test_an_inequality_statement_parses_lowers_and_prints():
    # `c[>] <= duinv(D_{b}V[>])` is a valid spelling of an occasionally binding
    # constraint (ruling D20, 9 Sep 2026): it lowers to Inequality(lhs, Le, rhs),
    # may carry the complementary-slackness clause, and prints back as written.
    from bellman.syntax import terms
    from bellman.syntax.lower import parse_with_spans
    from bellman.syntax.source import to_source
    ast, _ = parse_with_spans(INEQUALITY_STAGE)
    block = [it for it in ast.items if isinstance(it, terms.Block)][0]
    core = block.body[0].core
    assert isinstance(core, terms.Slack) and isinstance(core.core, terms.Inequality)
    assert isinstance(core.core.op, terms.Le)
    assert to_source(core) == "c[>] <= duinv(D_{b}V[>]) ⟂ b >= 0"
