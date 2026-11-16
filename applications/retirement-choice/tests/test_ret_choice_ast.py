"""Hand-derived AST expectations for the three retirement-choice stages.

Every expected node below is derived from the surface text of `ret_choice.bl`,
`worker_cons.bl` and `retiree_cons.bl` under `declaration/stages/`, of the
methods file beside each, `declaration/stages/<stage>/methods.bl`, an addition
to the stage file that holds its derivative lines, its method entries and, for
the two consumption stages, its inverse Euler lines, and from the generated
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
statement, in the block `policy` of the methods file, is an inequality (D20).
The claim that the maximization is marked `!doc` is deleted: the mark stood
while the inverse Euler lines shared the policy block, and with those lines in
the methods file the maximization is the block's one line (decision MB-S15).
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "applications"))

import pytest

import stage_ast
from stage_ast import (VLU, at_var, block, check, dom, extended_real, parsed,
                       run_checks, sym)
from bellman.syntax.terms import (
    Add, Annotation, Arrival, Assignment, At, Block, Call, Cartesian, Closed,
    Constant, Continuation, Control, Coordinate, CorrDef, Declaration, Declare,
    Decision, Div, Domain, Equation, FiniteSet, FuncDef, Grid, Handler,
    Inequality, Infoset, Interval, Key, Keyword, KeyValue, Le, Metadata,
    Method, Mul, Name, Named, Number, Open, Operator, Path, Range, Role,
    Segment, Select, Signature, Space, Spaced, Statement, Sub, Subject, Tag,
    Tuple, Typer, Var, In, Word,
)

STAGES = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
CHOICE = parsed(STAGES / "ret_choice" / "ret_choice.bl")
WORKER = parsed(STAGES / "worker_cons" / "worker_cons.bl")
RETIREE = parsed(STAGES / "retiree_cons" / "retiree_cons.bl")
# the methods file beside each stage file, an addition to it: its blocks name
# the stage's blocks by their ids, and the `policy` blocks of the two
# consumption stages hold the lines of the endogenous grid method
CHOICE_ADDITION = parsed(STAGES / "ret_choice" / "methods.bl")
WORKER_ADDITION = parsed(STAGES / "worker_cons" / "methods.bl")
RETIREE_ADDITION = parsed(STAGES / "retiree_cons" / "methods.bl")


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
    # stands in the block `cntn_to_dcsn` of the methods file.
    check(block(CHOICE_ADDITION.items, "cntn_to_dcsn").body[0],
          Statement(Equation(Operator("D", [Var("a_d")], [sym("V")]),
                             Select(Tuple([Operator("D", [Var("a_w")],
                                                    [at_var("V_w", Continuation)]),
                                           Operator("D", [Var("a_r")],
                                                    [at_var("V_r", Continuation)])]),
                                    Key("d"))),
                    Annotation([KeyValue("id", "marginal")])),
          "ret_choice.cntn_to_dcsn.marginal")


def test_choice_addition_types_the_policy_with_the_maximum():
    # The methods file of the choice stage: `policy.method : !max` and
    # `policy.handler : "fues-retirement:dcsn_mover"`, two file-level entries
    # routed by their paths to the block `policy`, which gains no line, and
    # then the block `cntn_to_dcsn` with the derivative line, named by the
    # builder's id and carrying no signature.
    items = CHOICE_ADDITION.items
    assert [type(i).__name__ for i in items] == ["Metadata", "Declare", "Declare", "Block"]
    check(items[0], Metadata("methods", "ret_choice"), "methods.items[0]")
    check(items[1],
          Declare(Declaration(Path([Segment("policy"), Segment("method")]),
                              [Method(Word("max"))]), None),
          "methods.items[1]")
    check(items[2],
          Declare(Handler(Path([Segment("policy"), Segment("handler")]),
                          "fues-retirement:dcsn_mover"), None),
          "methods.items[2]")
    check(items[3].tag, Annotation([KeyValue("id", "cntn_to_dcsn")]), "methods.items[3].tag")


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
    # blocks of the methods file that name the two value builders.
    check(block(WORKER.items, "cntn_to_dcsn").body,
          [Statement(Equation(sym("V"), Add(Call("𝑢", [sym("c")]),
                                            Mul(sym("β"), at_var("V", Continuation)))),
                     Annotation([KeyValue("id", "value")]))],
          "worker_cons.cntn_to_dcsn.body")
    check(block(WORKER_ADDITION.items, "cntn_to_dcsn").body,
          [Statement(Equation(Operator("D", [Var("w")], [sym("V")]),
                              Call("𝑑𝑢", [sym("c")])),
                     Annotation([KeyValue("id", "marginal")]))],
          "methods.cntn_to_dcsn.body")
    # The gross return is the chain-rule factor of the arrival transition, so
    # it stands in the arrival derivative line and not in the inverse Euler.
    check(block(WORKER.items, "dcsn_to_arvl").body,
          [Statement(Equation(at_var("V", Arrival), sym("V")),
                     Annotation([KeyValue("id", "value")]))],
          "worker_cons.dcsn_to_arvl.body")
    check(block(WORKER_ADDITION.items, "dcsn_to_arvl").body,
          [Statement(Equation(Operator("D", [Var("a_w")], [at_var("V", Arrival)]),
                              Mul(sym("R"), Operator("D", [Var("w")], [sym("V")]))),
                     Annotation([KeyValue("id", "marginal")]))],
          "methods.dcsn_to_arvl.body")


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
    # The stage file's policy block holds the maximization, and the block
    # `policy` of the methods file holds the four lines of the method. That
    # block's bracket types the builder with the endogenous grid method, its
    # grid on the savings b and its handler, and the operator `upper_env` of
    # its last line with the fast upper envelope scan and its threshold, a
    # keyword argument whose value is the setting's name.
    added = block(WORKER_ADDITION.items, "policy")
    check(added.tag, Annotation([
        KeyValue("id", "policy"),
        Typer(Declaration(Path([Segment("method")]), [Method(Word("egm"))])),
        Typer(Declaration(Path([Segment("grid")]), [Grid(Cartesian([
            Spaced("b", Name("a_min"), Name("a_max"), Name("n_a"))]))])),
        Typer(Handler(Path([Segment("handler")]), "asva:make_egm_1d")),
        Typer(Declaration(Path([Segment("upper_env"), Segment("method")]),
                          [Method(Word("FUES", [Keyword("m_bar", Name("m_bar"))]))])),
        Typer(Handler(Path([Segment("upper_env"), Segment("handler")]), "dcsmm:EGM_UE")),
    ]), "worker_cons.methods.policy.tag")
    body = policy.body + added.body
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
    egm = block(RETIREE_ADDITION.items, "policy")
    # The bracket of the methods file's block carries its typing entries by
    # the absolute path: the endogenous grid method, its grid on the savings
    # b_ret and its handler. A string in a statement annotation keeps its
    # quotation marks, and the note on the inverse Euler line is kept with it.
    check(egm.tag, Annotation([
        KeyValue("id", "policy"),
        Typer(Declaration(Path([Segment("policy"), Segment("method")]), [Method(Word("egm"))])),
        Typer(Declaration(Path([Segment("policy"), Segment("grid")]), [Grid(Cartesian([
            Spaced("b_ret", Name("a_ret_min"), Name("a_ret_max"), Name("n_a_ret"))]))])),
        Typer(Handler(Path([Segment("policy"), Segment("handler")]), "asva:make_egm_1d")),
    ]), "retiree_cons.methods.policy.tag")
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
