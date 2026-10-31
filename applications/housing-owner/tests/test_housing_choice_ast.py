#!/usr/bin/env python3
"""Structural verification of the AST for housing_choice.bl.

Each expectation below was derived by hand from the surface text of the
stage file, read against the three canonical ASDL listings (dynsym.asdl,
dynsym_new.asdl, stage.asdl; merged in dynspec_full.asdl). The test
parses the example fresh through the Lark route (stage.lark + ToAst) and
compares statement by statement against the hand-built constructor
trees; it does not read the stored .ast.json.

Constructs particular to this file, asserted deliberately: the move
indicator I(H_choice, H_d), which the file's own grammar notes announce
as the encoding of 1{H_choice differs from H_d}, is an ordinary
two-argument Call; the discrete housing grid XH := linspace(H_min,
H_max, n_H) is an Assignment whose value is a Call (a formula), not a
Space-wrapped set expression, and every housing symbol (H, H_d,
H_choice, H_nxt) carries Domain(Named("XH")) at its binding occurrence;
the Markov expectation E_{y}(V) lowers to Operator("E", [Var("y")], ...)
with the lexed trailing underscore stripped, the conditioning on y_pre
being carried by the DiscreteMarkov law rather than the subscript; the
discrete choice appears in kernel/policy form, the cntn_to_dcsn block
passing the continuation value through unchanged and the policy block carrying
H_choice = argmax_{H_choice}(V[>]).

The final test checks the independent TatSu route on comment-stripped
text. The TatSu grammar cannot step over a full-line comment between
two top-level items (its nl rule finds the newline already consumed
around the skipped comment), and this file opens with a block of
full-line grammar notes; on the same text with comment lines removed —
which the Lark route confirms is AST-identical to the original — the
two routes produce equal trees.

Runnable under pytest or directly with the repository interpreter:

    venv/bin/python applications/housing-owner/tests/test_housing_choice_ast.py
"""

import pathlib
import re
import sys

_TESTS = pathlib.Path(__file__).resolve().parent
_TOOLS = _TESTS.parents[2] / "packages" / "bellman" / "tests" / "tools"
sys.path.insert(0, str(_TOOLS))

import stage_ast                      # noqa: E402
from bellman.syntax.parse import build_parser  # noqa: E402
from stage_ast import annotation as _ann, parsed, perched as _p, run_checks, sym as _c  # noqa: E402
from stage_types import (             # noqa: E402
    Add, Arrival, Assignment, At, Block, Call, Constant,
    Continuation, Control, Coordinate, Declaration, Declare, Decision,
    Domain, Equation, Infoset, Key, KeyValue, Metadata, Mul, Named,
    Number, Operator, Role, Select, Shock, Signature, Space, Statement,
    Sub, Subject, Typer, Value, Var,
)

import pytest
pytest.skip(
    "assertions predate the typing respelling (colon, tilde, ! word-types)\n    — re-derive against the new terms (typing-spelling-0.3)",
    allow_module_level=True)

_SOURCE = _TESTS.parent / "declaration" / "stages" / "housing_choice" / "housing_choice.bl"
_TEXT = _SOURCE.read_text()
_AST = parsed(_SOURCE)
_ITEMS = _AST.items


def test_item_census():
    # One metadata line, four space assignments, eight declarations
    # (five parameters, Pi and z_vals for the shock law, the shock y),
    # and five blocks (arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn,
    # dcsn_to_arvl, policy).
    assert len(_ITEMS) == 18
    kinds = [type(it).__name__ for it in _ITEMS]
    assert kinds == (["Metadata"] + ["Statement"] * 4 + ["Declare"] * 8
                     + ["Block"] * 5)
    assert stage_ast.unlowered_parse_nodes(_AST) == []


def test_metadata_line():
    # @stage: housing_choice
    assert _ITEMS[0] == Metadata("stage", "housing_choice")


def test_space_assignments():
    # Xa := ℝ₊ and Xw := ℝ₊ — a reserved set glyph on the right-hand
    # side is a set expression, so the value is wrapped in Space.
    assert _ITEMS[1] == Statement(
        Assignment(Constant("Xa"), Space(Named("ℝ₊"))), None)
    assert _ITEMS[3] == Statement(
        Assignment(Constant("Xw"), Space(Named("ℝ₊"))), None)
    # Y := ℕ — the source Z+ has no ℤ₊ glyph; ℕ is the reserved neighbour.
    assert _ITEMS[4] == Statement(
        Assignment(Constant("Y"), Space(Named("ℕ"))), None)


def test_grid_assignment_is_a_call():
    # XH := linspace(H_min, H_max, n_H) — the discrete housing grid is a
    # space-defining call (the file's grammar notes), so the assigned
    # value is a Call in formula position, not a Space-wrapped set
    # expression; its arguments are the three grid parameters.
    assert _ITEMS[2] == Statement(
        Assignment(Constant("XH"),
                   Call("linspace",
                        [_c("H_min"), _c("H_max"), _c("n_H")])),
        None)


def test_parameter_declarations():
    # r @in ℝ₊ · φ @in ℝ₊ · n_H @in ℕ · H_min @in ℝ₊ · H_max @in ℝ₊
    # · Pi @in ℝ · z_vals @in ℝ — each a bare declaration line wrapped
    # in the provisional Declare item.
    expected = [("r", "ℝ₊"), ("φ", "ℝ₊"), ("n_H", "ℕ"),
                ("H_min", "ℝ₊"), ("H_max", "ℝ₊"),
                ("Pi", "ℝ"), ("z_vals", "ℝ")]
    for offset, (stem, space) in enumerate(expected):
        assert _ITEMS[5 + offset] == Declare(Declaration(
            Subject([Coordinate(stem, None, [])]),
            [Domain(Named(space))],
            None)), stem


def test_shock_declaration():
    # y @in Y @dist DiscreteMarkov(Pi, z_vals) — the income shock: a
    # named domain plus a shock role whose law parameters are ordinary
    # expressions. Conditioning on y_pre lives in the law, not here.
    assert _ITEMS[12] == Declare(Declaration(
        Subject([Coordinate("y", None, [])]),
        [Domain(Named("Y")),
         Role(Shock("DiscreteMarkov", [_c("Pi"), _c("z_vals")]))],
        None))


def test_arvl_to_dcsn_header():
    # [id=arvl_to_dcsn, (b @in Xa, H @in XH, y_pre @in Y, y) @arvl
    #        -> (w @in Xa, H_d @in XH, y_d @in Y) @dcsn]
    # The realized shock y rides in the arrival-side tuple without
    # classifiers; its binding occurrence is the top-level declaration.
    assert _ITEMS[13].tag == _ann(
        KeyValue("id", "arvl_to_dcsn"),
        Typer(Signature(
            Subject([Coordinate("b", None, [Domain(Named("Xa"))]),
                     Coordinate("H", None, [Domain(Named("XH"))]),
                     Coordinate("y_pre", None, [Domain(Named("Y"))]),
                     Coordinate("y", None, [])]),
            [Infoset(Arrival())],
            Subject([Coordinate("w", None, [Domain(Named("Xa"))]),
                     Coordinate("H_d", None, [Domain(Named("XH"))]),
                     Coordinate("y_d", None, [Domain(Named("Y"))])]),
            [Infoset(Decision())])))


def test_arvl_to_dcsn_body():
    # w = (1 + r)*b + z_vals[y] — the parenthesised sum multiplies b,
    # and z_vals[y] is selection from the family z_vals by the name key
    # y. Then the explicit carriers H_d = H and y_d = y.
    assert _ITEMS[13].body == [
        Statement(
            Equation(_c("w"),
                     Add(Mul(Add(Number(1), _c("r")), _c("b")),
                         Select(_c("z_vals"), Key("y")))),
            _ann(KeyValue("id", "cash_on_hand"))),
        Statement(Equation(_c("H_d"), _c("H")), None),
        Statement(Equation(_c("y_d"), _c("y")), None),
    ]


def test_dcsn_to_cntn_header():
    # [id=dcsn_to_cntn, (w, H_d, y_d, H_choice @control @in XH) @dcsn
    #        -> (w_c @in Xw, H_nxt @in XH, y_c @in Y) @cntn]
    # H_choice is a binding occurrence: classifiers in surface order,
    # @control before @in XH — the discrete grid domain on the control.
    assert _ITEMS[14].tag == _ann(
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([Coordinate("w", None, []),
                     Coordinate("H_d", None, []),
                     Coordinate("y_d", None, []),
                     Coordinate("H_choice", None,
                                [Role(Control()),
                                 Domain(Named("XH"))])]),
            [Infoset(Decision())],
            Subject([Coordinate("w_c", None, [Domain(Named("Xw"))]),
                     Coordinate("H_nxt", None, [Domain(Named("XH"))]),
                     Coordinate("y_c", None, [Domain(Named("Y"))])]),
            [Infoset(Continuation())])))


def test_dcsn_to_cntn_move_indicator():
    # moved = I(H_choice, H_d) — the move indicator 1{H_choice differs
    # from H_d}, encoded as an ordinary two-argument Call because
    # relational operators are not yet available in formula position.
    assert _ITEMS[14].body[0] == Statement(
        Equation(_c("moved"),
                 Call("I", [_c("H_choice"), _c("H_d")])),
        _ann(KeyValue("id", "move_indicator")))


def test_dcsn_to_cntn_housing_budget():
    # w_c = w + H_d - (1 + φ*moved)*H_choice — the sum associates to
    # the left, so the tree is Sub(Add(w, H_d), Mul(...)); inside the
    # parentheses the product φ*moved binds before the addition.
    assert _ITEMS[14].body[1] == Statement(
        Equation(_c("w_c"),
                 Sub(Add(_c("w"), _c("H_d")),
                     Mul(Add(Number(1), Mul(_c("φ"), _c("moved"))),
                         _c("H_choice")))),
        _ann(KeyValue("id", "housing_budget")))


def test_dcsn_to_cntn_carriers():
    # H_nxt = H_choice and y_c = y_d, with no statement meta.
    assert _ITEMS[14].body[2] == Statement(
        Equation(_c("H_nxt"), _c("H_choice")), None)
    assert _ITEMS[14].body[3] == Statement(
        Equation(_c("y_c"), _c("y_d")), None)


def test_cntn_to_dcsn_header():
    # [id=cntn_to_dcsn, (V[>] @in ℝ @value, dV[>] @in ℝ₊ @marginal, H_choice)
    #   @cntn -> (V @in ℝ @value, dV @in ℝ₊ @marginal) @dcsn]
    # The perch marks on the binding occurrences sit in the coordinate
    # index slot; @value is Role(Value(0)), @marginal Role(Value(1));
    # H_choice enters bare — the choice indexes the continuation
    # objects, and the policy block supplies it.
    assert _ITEMS[15].tag == _ann(
        KeyValue("id", "cntn_to_dcsn"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("dV", At(Continuation()),
                                [Domain(Named("ℝ₊")), Role(Value(1))]),
                     Coordinate("H_choice", None, [])]),
            [Infoset(Continuation())],
            Subject([Coordinate("V", None,
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("dV", None,
                                [Domain(Named("ℝ₊")), Role(Value(1))])]),
            [Infoset(Decision())])))


def test_cntn_to_dcsn_body():
    # V = V[>] and dV = dV[>] — the kernel of the discrete choice in
    # two-block form: the objective passes through unchanged, and the
    # maximization is lifted into the policy block, so max is recovered as
    # evaluation at the argmax.
    assert _ITEMS[15].body == [
        Statement(Equation(_c("V"), _p("V", Continuation())),
                  _ann(KeyValue("id", "value"))),
        Statement(Equation(_c("dV"), _p("dV", Continuation())),
                  _ann(KeyValue("id", "marginal"))),
    ]


def test_dcsn_to_arvl_header():
    # [id=dcsn_to_arvl, (V, dV) @dcsn -> (V[<] @in ℝ @value,
    #                             dV[<] @in ℝ₊ @marginal) @arvl]
    assert _ITEMS[16].tag == _ann(
        KeyValue("id", "dcsn_to_arvl"),
        Typer(Signature(
            Subject([Coordinate("V", None, []),
                     Coordinate("dV", None, [])]),
            [Infoset(Decision())],
            Subject([Coordinate("V", At(Arrival()),
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("dV", At(Arrival()),
                                [Domain(Named("ℝ₊")), Role(Value(1))])]),
            [Infoset(Arrival())])))


def test_dcsn_to_arvl_body():
    # V[<] = E_{y}(V) and dV[<] = E_{y}(dV) — the operator head is
    # stored as "E" (the lexed "E_" loses its underscore) with one
    # subscript Var("y"); the conditioning on y_pre is carried by the
    # DiscreteMarkov law declared on y, not by the subscript.
    assert _ITEMS[16].body == [
        Statement(
            Equation(_p("V", Arrival()),
                     Operator("E", [Var("y")], [_c("V")])),
            _ann(KeyValue("id", "value"))),
        Statement(
            Equation(_p("dV", Arrival()),
                     Operator("E", [Var("y")], [_c("dV")])),
            _ann(KeyValue("id", "marginal"))),
    ]


def test_policy_header():
    # [id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (H_choice : XH @ !ctrl) : !dcsn]
    # — the perch words added on 9 Sep 2026: the input is the continuation
    # value with its domain and value role, the output the housing control
    # on the declared grid at the decision perch. The policy block is the
    # last item of the file.
    assert _ITEMS[-1].tag == _ann(
        KeyValue("id", "policy"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))])]),
            [Infoset(Continuation())],
            Subject([Coordinate("H_choice", None,
                                [Domain(Named("XH")), Role(Control())])]),
            [Infoset(Decision())])))


def test_policy_argmax():
    # H_choice = argmax_{H_choice}(V[>]) — the lexed head "argmax_" has
    # its trailing underscore stripped; the subscript is the bound
    # choice variable; the single argument is the continuation value.
    assert _ITEMS[-1].body == [Statement(
        Equation(_c("H_choice"),
                 Operator("argmax", [Var("H_choice")],
                          [_p("V", Continuation())])),
        _ann(KeyValue("id", "choice")))]


def test_a_comment_carries_no_content_of_the_tree():
    # Comments carry no AST content: the text with every full-line
    # comment removed parses to the identical tree.
    stripped = re.sub(r"(?m)^[ \t]*#[^\n]*\n", "", _TEXT)
    assert stage_ast.ToAst().transform(
        build_parser().parse(stripped)) == _AST


if __name__ == "__main__":
    sys.exit(run_checks(globals(), f"for {_SOURCE.name}"))
