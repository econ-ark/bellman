"""Hand-derived AST expectations for the three retirement-choice stages.

Every expected node below is derived from the surface text of `ret_choice.bl`,
`worker_cons.bl` and `retiree_cons.bl` under `declaration/stages/`, of the block
files that hold their derivative lines and their inverse Euler lines under
`declaration/methods/` (`marginals_<stage>.bl`, `worker_cons_egm.bl`,
`retiree_cons_egm.bl`), and from the generated
term constructors (`bellman.sym.terms`, generated from `dynspec_full.asdl`), not
copied from their recorded encodings `*.ast.json` under
`packages/bellman/tests/snapshot/corpus/retirement-choice/`. Each file is parsed
fresh through the Lark route (`stage.lark`, then the `ToAst` lowering) and the
items under test are compared with their expectations. Runnable under pytest or
directly:

    venv/bin/python applications/retirement-choice/tests/test_ret_choice_ast.py

Three spellings of this corpus are asserted here because they carry rulings:
the nested branch blocks of the discrete choice (D02), the tuple selection of a
branch value and of the derivatives of the branch values (D02, D03), and the policy,
whose declarative maximization the stage file states (D19) and whose inverse Euler
statement, in the method block of the policy builder, is an inequality (D20).
The claim that the maximization is marked `!doc` is deleted: the mark stood
while the inverse Euler lines shared the policy block, and with those lines in
the method block the maximization is the block's one line (decision MB-S15).
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "packages" / "bellman" / "tests" / "tools"))

import pytest

import stage_ast
from stage_ast import (VLU, at_var, block, check, dom, extended_real, parsed,
                       run_checks, sym)
from stage_types import (
    Add, Annotation, Arrival, Assignment, At, Block, Call, Closed, Constant,
    Continuation, Control, Coordinate, CorrDef, Declaration, Declare, Decision,
    Div, Domain, Equation, FiniteSet, FuncDef, Inequality, Infoset, Interval,
    Key, KeyValue, Le, Metadata, Mul, Named, Number, Open, Operator, Range,
    Role, Select, Signature, Space, Statement, Sub, Subject, Tag, Tuple,
    Typer, Var, In,
)

STAGES = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
METHODS = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "methods"
CHOICE = parsed(STAGES / "ret_choice" / "ret_choice.bl")
WORKER = parsed(STAGES / "worker_cons" / "worker_cons.bl")
RETIREE = parsed(STAGES / "retiree_cons" / "retiree_cons.bl")
# the block files: the marginal blocks of each stage and the method blocks of
# the two consumption stages' policy builders
CHOICE_MARGINALS = parsed(METHODS / "marginals_ret_choice.bl")
WORKER_MARGINALS = parsed(METHODS / "marginals_worker_cons.bl")
WORKER_EGM = parsed(METHODS / "worker_cons_egm.bl")
RETIREE_EGM = parsed(METHODS / "retiree_cons_egm.bl")


# --- ret_choice.bl ----------------------------------------------------------


def test_choice_file_shape():
    # One metadata line, the work-cost declaration, and the five blocks.
    kinds = [type(i).__name__ for i in CHOICE.items]
    assert kinds == ["Metadata", "Declare"] + ["Block"] * 5, kinds
    assert stage_ast.unlowered_parse_nodes(CHOICE) == []


def test_choice_metadata_and_parameter():
    check(CHOICE.items[0], Metadata("stage", "ret_choice"), "items[0]")
    # `δ : ℝ₊₊ :: [...]`: the colon types the single coordinate, the Domain
    # sits on the Declaration, and the written description is kept on the
    # Declare item's annotation slot (AMD-SG-014 §3).
    check(CHOICE.items[1],
          Declare(Declaration(Subject([Coordinate("δ", None, [])]),
                              [dom("ℝ₊₊")], None),
                  Annotation([Tag('"utility cost of working, charged in the'
                                  ' period whose wage it earns"')])),
          "items[1]")


def test_choice_arrival_transition():
    want = Block(
        Annotation([
            KeyValue("id", "arvl_to_dcsn"),
            Typer(Signature(
                Subject([Coordinate("a", None, [dom("ℝ₊")])]),
                [Infoset(Arrival())],
                Subject([Coordinate("a_d", None, [dom("ℝ₊")])]),
                [Infoset(Decision())])),
        ]),
        [Statement(Equation(sym("a_d"), sym("a")),
                   Annotation([KeyValue("id", "assets")]))])
    check(block(CHOICE.items, "arvl_to_dcsn"), want, "ret_choice.arvl_to_dcsn")


def test_choice_branch_signature_has_an_empty_output_side():
    # `(a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()`: the control carries its
    # role before its finite set, in the order written; the output side is an
    # empty subject with no side type, the branches supplying the continuation
    # fields (D02).
    want = Annotation([
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([
                Coordinate("a_d", None, []),
                Coordinate("d", None, [Role(Control()),
                                       Domain(FiniteSet(["work", "retire"]))]),
            ]),
            [Infoset(Decision())],
            Subject([]),
            [])),
    ])
    check(block(CHOICE.items, "dcsn_to_cntn").tag, want, "ret_choice.dcsn_to_cntn.tag")


def test_choice_nested_branch_blocks():
    body = block(CHOICE.items, "dcsn_to_cntn").body
    assert len(body) == 2
    for nested, label, stem in [(body[0], "work", "a_w"),
                                (body[1], "retire", "a_r")]:
        want = Block(
            Annotation([
                KeyValue("label", label),
                Typer(Signature(
                    Subject([]),
                    [],
                    Subject([Coordinate(stem, None, [dom("ℝ₊")])]),
                    [Infoset(Continuation())])),
            ]),
            [Statement(Equation(sym(stem), sym("a_d")), None)])
        check(nested, want, f"ret_choice.dcsn_to_cntn.{label}")


def test_choice_value_and_marginal_are_tuple_selections():
    body = block(CHOICE.items, "cntn_to_dcsn").body
    assert len(body) == 1
    # V = (V_w[>] - δ, V_r[>])[d]: a two-item tuple in label order, selected by
    # the control's name; the work entry carries the subtraction of the cost.
    check(body[0],
          Statement(Equation(sym("V"),
                             Select(Tuple([Sub(at_var("V_w", Continuation), sym("δ")),
                                           at_var("V_r", Continuation)]),
                                    Key("d"))),
                    Annotation([KeyValue("id", "choice_value")])),
          "ret_choice.cntn_to_dcsn.choice_value")
    # D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]: the same selection on the
    # derivatives of the branch values, which carry no cost (D03); the line
    # stands in the marginal block of the decision value builder.
    check(block(CHOICE_MARGINALS.items, "dcsn_marginal").body[0],
          Statement(Equation(Operator("D", [Var("a_d")], [sym("V")]),
                             Select(Tuple([Operator("D", [Var("a_w")],
                                                    [at_var("V_w", Continuation)]),
                                           Operator("D", [Var("a_r")],
                                                    [at_var("V_r", Continuation)])]),
                                    Key("d"))),
                    Annotation([KeyValue("id", "marginal")])),
          "ret_choice.cntn_to_dcsn.marginal")


def test_choice_policy_selects_the_larger_branch_value():
    policy = block(CHOICE.items, "policy")
    # The inputs are the two branch values, already declared, so they carry no
    # classifier here; the output is the control on its finite set.
    sig = policy.tag.entries[1].typing
    check(sig.source,
          Subject([Coordinate("V_w", At(Continuation()), []),
                   Coordinate("V_r", At(Continuation()), [])]),
          "ret_choice.policy.source")
    check(sig.target,
          Subject([Coordinate("d", None, [Domain(FiniteSet(["work", "retire"])),
                                          Role(Control())])]),
          "ret_choice.policy.target")
    # argmax_{d}(V_w[>] - δ, V_r[>]): the binder is the control, the two
    # comma-separated arguments stay two arguments in the same order as the
    # tuple of the value equation.
    check(policy.body[0],
          Statement(Equation(sym("d"),
                             Operator("argmax", [Var("d")],
                                      [Sub(at_var("V_w", Continuation), sym("δ")),
                                       at_var("V_r", Continuation)])),
                    Annotation([KeyValue("id", "choice")])),
          "ret_choice.policy.choice")


# --- worker_cons.bl ---------------------------------------------------------


def test_worker_file_shape():
    # Metadata, the set definition, three parameters, three function
    # definitions, the feasible correspondence, and the five blocks.
    kinds = [type(i).__name__ for i in WORKER.items]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 3
                     + ["Statement"] * 4 + ["Block"] * 5), kinds
    assert stage_ast.unlowered_parse_nodes(WORKER) == []
    check(WORKER.items[0], Metadata("stage", "worker_cons"), "items[0]")
    check(WORKER.items[1],
          Statement(Assignment(Constant("Xa"), Space(Named("ℝ₊"))), None),
          "items[1]")


def test_worker_definitions():
    # Log utility with its closed-form derivative and inverse derivative: the
    # three are ordinary function definitions with typed arguments, and Γ is a
    # correspondence definition whose body is a set (D19).
    check(WORKER.items[5],
          Statement(FuncDef("𝑢", [Coordinate("c", None, [dom("ℝ₊₊")])],
                            Call("log", [sym("c")])),
                    Annotation([KeyValue("id", "util")])),
          "worker_cons.util")
    check(WORKER.items[6],
          Statement(FuncDef("𝑑𝑢", [Coordinate("c", None, [dom("ℝ₊₊")])],
                            Div(Number(1), sym("c"))),
                    Annotation([KeyValue("id", "marg_util")])),
          "worker_cons.marg_util")
    check(WORKER.items[7],
          Statement(FuncDef("𝑑𝑢𝑖𝑛𝑣", [Coordinate("x", None, [dom("ℝ₊₊")])],
                            Div(Number(1), sym("x"))),
                    Annotation([KeyValue("id", "inv_marg_util")])),
          "worker_cons.inv_marg_util")
    check(WORKER.items[8],
          Statement(CorrDef("Γ", [Coordinate("x", None, [dom("ℝ₊₊")])],
                            Interval(Range(Open(), Number(0), sym("x"), Closed()))),
                    Annotation([KeyValue("id", "feasible")])),
          "worker_cons.feasible")


def test_worker_transitions():
    want = Block(
        Annotation([
            KeyValue("id", "arvl_to_dcsn"),
            Typer(Signature(
                Subject([Coordinate("a_w", None, [Domain(Named("Xa"))])]),
                [Infoset(Arrival())],
                Subject([Coordinate("w", None, [dom("ℝ₊₊")])]),
                [Infoset(Decision())])),
        ]),
        [Statement(Equation(sym("w"), Add(Mul(sym("R"), sym("a_w")), sym("y"))),
                   Annotation([KeyValue("id", "cash_on_hand")]))])
    check(block(WORKER.items, "arvl_to_dcsn"), want, "worker_cons.arvl_to_dcsn")
    want = Block(
        Annotation([
            KeyValue("id", "dcsn_to_cntn"),
            Typer(Signature(
                Subject([Coordinate("w", None, []),
                         Coordinate("c", None, [dom("ℝ₊₊"), Role(Control())])]),
                [Infoset(Decision())],
                Subject([Coordinate("b", None, [Domain(Named("Xa"))])]),
                [Infoset(Continuation())])),
        ]),
        [Statement(Equation(sym("b"), Sub(sym("w"), sym("c"))),
                   Annotation([KeyValue("id", "savings")]))])
    check(block(WORKER.items, "dcsn_to_cntn"), want, "worker_cons.dcsn_to_cntn")


def test_worker_backward_blocks():
    # The value lines stand in the stage file and the derivative lines in the
    # marginal blocks of the two value builders.
    check(block(WORKER.items, "cntn_to_dcsn").body,
          [Statement(Equation(sym("V"), Add(Call("𝑢", [sym("c")]),
                                            Mul(sym("β"), at_var("V", Continuation)))),
                     Annotation([KeyValue("id", "value")]))],
          "worker_cons.cntn_to_dcsn.body")
    check(block(WORKER_MARGINALS.items, "dcsn_marginal").body,
          [Statement(Equation(Operator("D", [Var("w")], [sym("V")]),
                              Call("𝑑𝑢", [sym("c")])),
                     Annotation([KeyValue("id", "marginal")]))],
          "marginals_worker_cons.dcsn_marginal.body")
    # The gross return is the chain-rule factor of the arrival transition, so
    # it stands in the arrival derivative line and not in the inverse Euler.
    check(block(WORKER.items, "dcsn_to_arvl").body,
          [Statement(Equation(at_var("V", Arrival), sym("V")),
                     Annotation([KeyValue("id", "value")]))],
          "worker_cons.dcsn_to_arvl.body")
    check(block(WORKER_MARGINALS.items, "arvl_marginal").body,
          [Statement(Equation(Operator("D", [Var("a_w")], [at_var("V", Arrival)]),
                              Mul(sym("R"), Operator("D", [Var("w")], [sym("V")]))),
                     Annotation([KeyValue("id", "marginal")]))],
          "marginals_worker_cons.arvl_marginal.body")


def test_worker_policy_block():
    policy = block(WORKER.items, "policy")
    sig = policy.tag.entries[1].typing
    # The input is the continuation value and no continuation state (D22);
    # the output is the control.
    check(sig.source,
          Subject([Coordinate("V", At(Continuation()), [extended_real(), VLU])]),
          "worker_cons.policy.source")
    check(sig.target,
          Subject([Coordinate("c", None, [dom("ℝ₊₊"), Role(Control())])]),
          "worker_cons.policy.target")
    # The stage file's policy block holds the maximization, and the method
    # block of the policy builder holds the four lines of the method.
    body = policy.body + block(WORKER_EGM.items, "egm").body
    assert [e.value for st in body for e in st.annot.entries
            if isinstance(e, KeyValue)] == [
        "optimality", "InvEuler", "endoggrid", "cand_value", "envelope"]
    assert len(policy.body) == 1
    # The declarative maximization binds the control's own name to its feasible
    # set (D19).
    check(body[0],
          Statement(Equation(sym("c"),
                             Operator("argmax", [In("c", Call("Γ", [sym("w")]))],
                                      [Add(Call("𝑢", [sym("c")]),
                                           Mul(sym("β"), at_var("V", Continuation)))])),
                    Annotation([KeyValue("id", "optimality")])),
          "worker_cons.policy.optimality")
    # The inverse Euler statement is an inequality, whose candidate is a
    # segment where the borrowing constraint binds (D20).
    check(body[1],
          Statement(Inequality(at_var("c", Continuation), Le(),
                               Call("𝑑𝑢𝑖𝑛𝑣", [Mul(sym("β"),
                                                  Operator("D", [Var("b")],
                                                           [at_var("V", Continuation)]))])),
                    Annotation([KeyValue("id", "InvEuler")])),
          "worker_cons.policy.InvEuler")
    check(body[2],
          Statement(Equation(at_var("w", Continuation),
                             Add(sym("b"), at_var("c", Continuation))),
                    Annotation([KeyValue("id", "endoggrid")])),
          "worker_cons.policy.endoggrid")
    check(body[3],
          Statement(Equation(at_var("v", Continuation),
                             Add(Call("𝑢", [at_var("c", Continuation)]),
                                 Mul(sym("β"), at_var("V", Continuation)))),
                    Annotation([KeyValue("id", "cand_value")])),
          "worker_cons.policy.cand_value")
    # The envelope selects among the candidates by value and defines the
    # control; `upper_env` is written as an ordinary call.
    check(body[4],
          Statement(Equation(sym("c"),
                             Call("upper_env", [at_var("w", Continuation),
                                                at_var("c", Continuation),
                                                at_var("v", Continuation)])),
                    Annotation([KeyValue("id", "envelope")])),
          "worker_cons.policy.envelope")


# --- retiree_cons.bl --------------------------------------------------------


def test_retiree_file_shape_and_arrival_transition():
    kinds = [type(i).__name__ for i in RETIREE.items]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 2
                     + ["Statement"] * 4 + ["Block"] * 5), kinds
    assert stage_ast.unlowered_parse_nodes(RETIREE) == []
    check(RETIREE.items[0], Metadata("stage", "retiree_cons"), "items[0]")
    # The retiree earns no wage: cash on hand is the return on assets alone.
    check(block(RETIREE.items, "arvl_to_dcsn"),
          Block(
              Annotation([
                  KeyValue("id", "arvl_to_dcsn"),
                  Typer(Signature(
                      Subject([Coordinate("a_ret", None, [Domain(Named("Xa"))])]),
                      [Infoset(Arrival())],
                      Subject([Coordinate("w_ret", None, [Domain(Named("Xa"))])]),
                      [Infoset(Decision())])),
              ]),
              [Statement(Equation(sym("w_ret"), Mul(sym("R"), sym("a_ret"))),
                         Annotation([KeyValue("id", "cash_on_hand")]))]),
          "retiree_cons.arvl_to_dcsn")


def test_retiree_policy_block_and_its_retained_notes():
    policy = block(RETIREE.items, "policy")
    egm = block(RETIREE_EGM.items, "egm")
    # A quoted string in a block header is a tag, and the lowering keeps its
    # text without the quotation marks; a string in a statement annotation
    # keeps them. The note stands on the header of the method block, which
    # holds the method it describes (decision MB-S11).
    assert egm.tag.entries[2] == Tag(
        "method = egm! will look for policy[>] and x[>] grid and invert it. "
        "Important here that the grids contain all constrained sections")
    body = policy.body + egm.body
    assert [e.value for st in body for e in st.annot.entries
            if isinstance(e, KeyValue)] == [
        "optimality", "InvEuler", "endoggrid", "cons_choice"]
    assert len(policy.body) == 1
    check(body[0],
          Statement(Equation(sym("c"),
                             Operator("argmax", [In("c", Call("Γ", [sym("w_ret")]))],
                                      [Add(Call("𝑢", [sym("c")]),
                                           Mul(sym("β"), at_var("V", Continuation)))])),
                    Annotation([KeyValue("id", "optimality")])),
          "retiree_cons.policy.optimality")
    check(body[1],
          Statement(Inequality(at_var("c", Continuation), Le(),
                               Call("𝑑𝑢𝑖𝑛𝑣", [Mul(sym("β"),
                                                  Operator("D", [Var("b_ret")],
                                                           [at_var("V", Continuation)]))])),
                    Annotation([
                        KeyValue("id", "InvEuler"),
                        Tag('"Implies a correspondence: where equality holds, '
                            'c[>] takes on a single value, where inequality '
                            'holds, it is multiple values"')])),
          "retiree_cons.policy.InvEuler")
    check(body[2],
          Statement(Equation(at_var("w_ret", Continuation),
                             Add(sym("b_ret"), at_var("c", Continuation))),
                    Annotation([KeyValue("id", "endoggrid")])),
          "retiree_cons.policy.endoggrid")
    # The retiree's continuation value is concave, so the implicit statement
    # identifies the control with its candidate and no envelope is needed.
    check(body[3],
          Statement(Equation(sym("c"), at_var("c", Continuation)),
                    Annotation([KeyValue("id", "cons_choice")])),
          "retiree_cons.policy.cons_choice")


if __name__ == "__main__":
    sys.exit(run_checks(globals(), "on the three retirement-choice stages"))
