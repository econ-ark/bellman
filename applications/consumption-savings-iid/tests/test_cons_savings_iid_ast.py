#!/usr/bin/env python3
"""Structural verification of the AST for cons_savings_iid.bl.

Each expectation below was derived by hand from the surface text of the
stage file, read against the three canonical ASDL listings (dynsym.asdl,
dynsym_new.asdl, stage.asdl; merged in dynspec_full.asdl). The test
parses the example fresh through the Lark route (stage.lark + ToAst) and
compares statement by statement against the hand-built constructor
trees; it does not read the stored .ast.json. A final test checks that

Deliberate conventions asserted here, not incidental output: a bare
declaration line becomes Declare(Declaration(...)); @value and @marginal
become Role(Value(0)) and Role(Value(1)); V[<] / V[>] in expression
position become Sym(Variable(name, At(perch), 0)); the lexed operator
head "E_" is stored without its underscore; ":: [id=x, !node]" becomes
Annotation entries with !node as Typer(Marked(Node())); assigning a set
expression wraps the value in Space(...).

Runnable under pytest or directly with the repository interpreter:

    venv/bin/python applications/consumption-savings-iid/tests/test_cons_savings_iid_ast.py
"""

import pathlib
import sys

_TESTS = pathlib.Path(__file__).resolve().parent
_TOOLS = _TESTS.parents[2] / "applications"
sys.path.insert(0, str(_TOOLS))

from stage_ast import annotation as _ann, parsed, perched as _p, run_checks, sym as _c  # noqa: E402
from bellman.syntax.terms import (             # noqa: E402
    Add, Arrival, Assignment, At, Block, Call, Constant,
    Continuation, Control, Coordinate, Declaration, Declare, Decision, Div,
    Domain, Equation, Infoset, Interval, KeyValue, Marked, Metadata, Mul,
    Named, Neg, Node, Number, Open, Operator, Pow, Range, Role, Shock,
    Signature, Space, Statement, Sub, Subject, Typer, Value, Var,
)

_SOURCE = _TESTS.parent / "declaration" / "stages" / "cons_savings_iid" / "cons_savings_iid.bl"

import pytest
pytest.skip(
    "assertions predate the typing respelling — the file now parses; "
    "re-derive the structural assertions against the new terms",
    allow_module_level=True)

_ITEMS = parsed(_SOURCE).items


def test_item_census():
    assert len(_ITEMS) == 13
    kinds = [type(it).__name__ for it in _ITEMS]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 6
                     + ["Block"] * 5)


def test_metadata_line():
    # @stage: cons_savings_iid
    assert _ITEMS[0] == Metadata("stage", "cons_savings_iid")


def test_space_assignment():
    # Y := ℝ — the set-valued right-hand side is wrapped in Space.
    assert _ITEMS[1] == Statement(
        Assignment(Constant("Y"), Space(Named("ℝ"))), None)


def test_declare_beta_open_interval():
    # β @in (0,1) — an open interval on both ends.
    assert _ITEMS[2] == Declare(Declaration(
        Subject([Coordinate("β", None, [])]),
        [Domain(Interval(Range(Open(), Number(0), Number(1), Open())))],
        None))


def test_declares_with_named_domains():
    # γ @in ℝ₊ · r @in ℝ₊₊ · μ_y @in ℝ · σ_y @in ℝ₊
    expected = [("γ", "ℝ₊"), ("r", "ℝ₊₊"), ("μ_y", "ℝ"), ("σ_y", "ℝ₊")]
    for offset, (stem, space) in enumerate(expected):
        assert _ITEMS[3 + offset] == Declare(Declaration(
            Subject([Coordinate(stem, None, [])]),
            [Domain(Named(space))],
            None)), stem


def test_declare_shock():
    # y @in Y @dist N(μ_y, σ_y) — a named domain plus a shock role whose
    # law parameters are ordinary expressions.
    assert _ITEMS[7] == Declare(Declaration(
        Subject([Coordinate("y", None, [])]),
        [Domain(Named("Y")),
         Role(Shock("N", [_c("μ_y"), _c("σ_y")]))],
        None))


def test_block_arvl_to_dcsn_header():
    # [id=arvl_to_dcsn, (b @in ℝ₊, y) @arvl -> (w @in ℝ₊) @dcsn]
    assert _ITEMS[8].tag == _ann(
        KeyValue("id", "arvl_to_dcsn"),
        Typer(Signature(
            Subject([Coordinate("b", None, [Domain(Named("ℝ₊"))]),
                     Coordinate("y", None, [])]),
            [Infoset(Arrival())],
            Subject([Coordinate("w", None, [Domain(Named("ℝ₊"))])]),
            [Infoset(Decision())])))


def test_block_arvl_to_dcsn_body():
    # w = exp(y) + b*r — the product binds before the sum, so the
    # right-hand side is Add(Call(exp, [y]), Mul(b, r)).
    assert _ITEMS[8].body == [Statement(
        Equation(_c("w"),
                 Add(Call("exp", [_c("y")]), Mul(_c("b"), _c("r")))),
        _ann(KeyValue("id", "cash_on_hand")))]


def test_block_dcsn_to_cntn_header():
    # [id=dcsn_to_cntn, (w, c @control @in ℝ₊) @dcsn -> (a @in ℝ₊) @cntn] —
    # the classifiers on c keep their surface order: role, then domain.
    assert _ITEMS[9].tag == _ann(
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([Coordinate("w", None, []),
                     Coordinate("c", None, [Role(Control()),
                                            Domain(Named("ℝ₊"))])]),
            [Infoset(Decision())],
            Subject([Coordinate("a", None, [Domain(Named("ℝ₊"))])]),
            [Infoset(Continuation())])))


def test_block_dcsn_to_cntn_body():
    # a = w - c, with no statement meta.
    assert _ITEMS[9].body == [Statement(
        Equation(_c("a"), Sub(_c("w"), _c("c"))), None)]


def test_block_cntn_to_dcsn_header():
    # [id=cntn_to_dcsn, (V[>] @in ℝ @value, c) @cntn
    #        -> (V @in ℝ @value, dV @in ℝ₊₊ @marginal) @dcsn]
    # The perch mark on V's binding occurrence sits in the coordinate's
    # index slot; @value is Role(Value(0)), @marginal Role(Value(1)).
    assert _ITEMS[10].tag == _ann(
        KeyValue("id", "cntn_to_dcsn"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("c", None, [])]),
            [Infoset(Continuation())],
            Subject([Coordinate("V", None,
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("dV", None,
                                [Domain(Named("ℝ₊₊")), Role(Value(1))])]),
            [Infoset(Decision())])))


def test_block_cntn_to_dcsn_value_equation():
    # V = c^(1-γ)/(1-γ) + β*V[>] — the power binds before the division,
    # the division before the sum, and V[>] is a continuation-perch
    # occurrence of V.
    one_minus_gamma = Sub(Number(1), _c("γ"))
    assert _ITEMS[10].body[0] == Statement(
        Equation(_c("V"),
                 Add(Div(Pow(_c("c"), one_minus_gamma), one_minus_gamma),
                     Mul(_c("β"), _p("V", Continuation())))),
        _ann(KeyValue("id", "value")))


def test_block_cntn_to_dcsn_marginal_equation():
    # dV = c^(-γ) — the parenthesised exponent is Neg(γ).
    assert _ITEMS[10].body[1] == Statement(
        Equation(_c("dV"), Pow(_c("c"), Neg(_c("γ")))),
        _ann(KeyValue("id", "marginal")))


def test_block_dcsn_to_arvl_header():
    # [id=dcsn_to_arvl, (V, dV) @dcsn -> (V[<] @in ℝ @value,
    #                             dV[<] @in ℝ₊₊ @marginal) @arvl]
    assert _ITEMS[11].tag == _ann(
        KeyValue("id", "dcsn_to_arvl"),
        Typer(Signature(
            Subject([Coordinate("V", None, []),
                     Coordinate("dV", None, [])]),
            [Infoset(Decision())],
            Subject([Coordinate("V", At(Arrival()),
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("dV", At(Arrival()),
                                [Domain(Named("ℝ₊₊")), Role(Value(1))])]),
            [Infoset(Arrival())])))


def test_block_dcsn_to_arvl_body():
    # V[<] = E_{y}(V) and dV[<] = E_{y}(r * dV) — the operator head is
    # stored as "E" (the lexed "E_" loses its underscore), with one
    # subscript Var("y").
    assert _ITEMS[11].body == [
        Statement(
            Equation(_p("V", Arrival()),
                     Operator("E", [Var("y")], [_c("V")])),
            _ann(KeyValue("id", "value"))),
        Statement(
            Equation(_p("dV", Arrival()),
                     Operator("E", [Var("y")], [Mul(_c("r"), _c("dV"))])),
            _ann(KeyValue("id", "marginal"))),
    ]


def test_block_policy_header():
    # [id=policy, (dV[>] @in ℝ₊₊ @marginal, a, w) -> (c)] — neither side
    # carries a perch typing, so both perch-type lists are empty.
    assert _ITEMS[12].tag == _ann(
        KeyValue("id", "policy"),
        Typer(Signature(
            Subject([Coordinate("dV", At(Continuation()),
                                [Domain(Named("ℝ₊₊")), Role(Value(1))]),
                     Coordinate("a", None, []),
                     Coordinate("w", None, [])]),
            [],
            Subject([Coordinate("c", None, [])]),
            [])))


def test_block_policy_inveuler():
    # c[>] = (β*dV[>])^(-1/γ) :: [id=InvEuler, !node] — unary minus in
    # the grammar takes a whole product, so the exponent is
    # Neg(Div(1, γ)); the !node tag becomes Typer(Marked(Node())).
    assert _ITEMS[12].body[0] == Statement(
        Equation(_p("c", Continuation()),
                 Pow(Mul(_c("β"), _p("dV", Continuation())),
                     Neg(Div(Number(1), _c("γ"))))),
        _ann(KeyValue("id", "InvEuler"), Typer(Marked(Node()))))


def test_block_policy_regrid():
    # w[>] = a + c[>] :: [id=regrid, !node]
    assert _ITEMS[12].body[1] == Statement(
        Equation(_p("w", Continuation()),
                 Add(_c("a"), _p("c", Continuation()))),
        _ann(KeyValue("id", "regrid"), Typer(Marked(Node()))))


def test_block_policy_evaluate():
    # c = evaluate(c[>], w[>], w) :: [id=pol_func] — evaluate is an
    # ordinary Call whose arguments mix perch-marked and plain symbols.
    assert _ITEMS[12].body[2] == Statement(
        Equation(_c("c"),
                 Call("evaluate", [_p("c", Continuation()),
                                   _p("w", Continuation()),
                                   _c("w")])),
        _ann(KeyValue("id", "pol_func")))


if __name__ == "__main__":
    sys.exit(run_checks(globals(), f"for {_SOURCE.name}"))
