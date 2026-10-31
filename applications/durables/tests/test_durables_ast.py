"""Hand-derived AST expectations for three of the four stages of the durables
model and for the block files that hold their derivative lines and their
endogenous grid lines; the terminal stage `bequest.bl` is compared by the
corpus test alone.

Every expectation below is derived from the surface text of
`declaration/stages/tenure/tenure.bl`, `declaration/stages/keeper_cons/keeper_cons.bl`
and `declaration/stages/adjuster_cons/adjuster_cons.bl`, of the marginal blocks
of `declaration/methods/marginals_tenure.bl`, `marginals_keeper_cons.bl` and
`marginals_adjuster_cons.bl`, and of the method blocks of
`declaration/methods/keeper_cons_egm.bl` and `adjuster_cons_egm.bl`, and from
the generated term constructors (bellman.sym.terms, generated from
dynspec_full.asdl), not copied from their recordings `*.ast.json` under
`packages/bellman/tests/snapshot/corpus/durables/`. Each file is parsed fresh
through the Lark route (stage.lark, then the ToAst lowering) and compared item
by item.

Constructs particular to this model, asserted deliberately: the branching
transition of `tenure.bl`, whose output side is empty and whose body is two
labeled blocks with no shared field name; the selection of a branch value,
and of the derivatives of the branch values, by the control, `(…, …)[d]`,
which lowers to a Select of a Tuple by a name key; the inequality statement of
both consumption stages' method blocks, which writes the borrowing constraint
as a correspondence; the joint maximization of `adjuster_cons.bl`, whose left
side is a tuple and whose two binders carry feasible sets, the second reading
the first binder; and the joint solution statement of the adjuster's method
block, with two unknowns and two residuals. The tuple left side constructs as
a joint choice. All the files parse, which is what this test checks.

Runnable under pytest or directly:

    venv/bin/python applications/durables/tests/test_durables_ast.py
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "packages" / "bellman" / "tests" / "tools"))

import pytest

import stage_ast
from stage_ast import arvl, check, cntn, dom, one_minus, parsed, run_checks, sym
from stage_types import (
    Add, Annotation, Arrival, At, Block, Call, Closed, Constant, Continuation,
    Control, Coordinate, CorrDef, Declaration, Declare, Decision, Div, Domain,
    Equation, FiniteSet, FuncDef, In, Inequality, Infoset, Interval, Key,
    KeyValue, Law, Le, Metadata, Mul, Named, Neg, Number, Open, Operator, Pow,
    Range, Role, Select, Signature, Statement, Sub, Subject, Sym, Tag, Tuple,
    Typer, Value, Var,
)

STAGES = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
METHODS = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "methods"
TENURE = parsed(STAGES / "tenure" / "tenure.bl")
KEEPER = parsed(STAGES / "keeper_cons" / "keeper_cons.bl")
ADJUSTER = parsed(STAGES / "adjuster_cons" / "adjuster_cons.bl")
# the block files that hold the derivative lines of the value builders and the
# endogenous grid lines of the two policy builders, each a metadata line and
# its blocks (decisions MB-U2 and MB-U5)
TENURE_MARGINALS = parsed(METHODS / "marginals_tenure.bl")
KEEPER_MARGINALS = parsed(METHODS / "marginals_keeper_cons.bl")
KEEPER_EGM = parsed(METHODS / "keeper_cons_egm.bl")
ADJUSTER_MARGINALS = parsed(METHODS / "marginals_adjuster_cons.bl")
ADJUSTER_EGM = parsed(METHODS / "adjuster_cons_egm.bl")


def block_file(items, stage):
    """The first item of a block file, the metadata line `@methods: <stage>`,
    and the blocks after it, each a Block."""
    check(items[0], Metadata("methods", stage), "items[0]")
    assert all(type(item).__name__ == "Block" for item in items[1:]), items
    return items[1:]


# --- spellings shared by the three files -------------------------------------

def ident(name):
    return Annotation([KeyValue("id", name)])


def coord(stem, at=None, classifiers=()):
    return Coordinate(stem, at, list(classifiers))


def value(space="ℝ"):
    """The classifiers of a value field, domain then role as written."""
    return [dom(space), Role(Value(0))]


def derivative(coordinate, field):
    """The derivative term `D_{coordinate}` of the value field `field`, an
    operator term whose one argument is the field as the line writes it."""
    return Operator("D", [Var(coordinate)], [field])


def sig(source, source_types, target, target_types):
    return Typer(Signature(Subject(source), source_types,
                           Subject(target), target_types))


def header(block_id, signature):
    return Annotation([KeyValue("id", block_id), signature])


def scalar_declarations(items, offset, expected):
    """`name : <set>` lines: the domain sits on the Declaration and the
    coordinate carries none; a written `:: ["…"]` description is kept on
    the Declare item's annotation slot (AMD-SG-014 §3)."""
    for index, (stem, space, described) in enumerate(expected, start=offset):
        annot = None if described is None else Annotation([Tag(f'"{described}"')])
        want = Declare(Declaration(
            Subject([coord(stem)]), [Domain(space)], None), annot)
        check(items[index], want, f"items[{index}]")


# --- tenure.bl ---------------------------------------------------------------

def test_tenure_file_shape():
    # One metadata line, seven parameters, the innovation, its law, the income
    # function, and the five blocks.
    kinds = [type(item).__name__ for item in TENURE.items]
    assert kinds == (["Metadata"] + ["Declare"] * 8 + ["Statement"] * 2
                     + ["Block"] * 5), kinds
    assert stage_ast.unlowered_parse_nodes(TENURE) == []


def test_tenure_declarations():
    check(TENURE.items[0], Metadata("stage", "tenure"), "items[0]")
    # `δ : [0,1)` is closed at zero and open at one; `ρ_z : (0,1)` is open at
    # both ends. Each trailing `:: [...]` explanation is a Tag on the
    # declaration's annotation; the innovation `ε : ℝ` is written without one.
    scalar_declarations(TENURE.items, 1, [
        ("R", Named("ℝ₊₊"), "gross return on financial assets"),
        ("R_H", Named("ℝ₊₊"),
         "gross return on housing, received when the house is sold"),
        ("δ", Interval(Range(Closed(), Number(0), Number(1), Open())),
         "depreciation rate of housing"),
        ("ρ_z", Interval(Range(Open(), Number(0), Number(1), Open())),
         "persistence of log income"),
        ("σ_z", Named("ℝ₊"),
         "standard deviation of the innovation to log income"),
        ("Y", Named("ℝ₊"),
         "earnings per unit of the income state at the age of the period"),
        ("y_R", Named("ℝ₊"),
         "income that does not depend on the income state at the age of"
         " the period"),
        ("ε", Named("ℝ"), None),
    ])


def test_tenure_law_and_income_function():
    # `ε ~ N(0, 1)`: a Statement whose core is Law(subjects, law), the law an
    # ordinary call. `𝑦(z : ℝ₊₊) := Y*z + y_R`: a function of the income state
    # whose two parameters the occurrence supplies.
    check(TENURE.items[9],
          Statement(Law(["ε"], Call("N", [Number(0), Number(1)])), None),
          "items[9]")
    check(TENURE.items[10],
          Statement(FuncDef("𝑦", [coord("z", None, [dom("ℝ₊₊")])],
                            Add(Mul(sym("Y"), sym("z")), sym("y_R"))),
                    ident("income")),
          "items[10]")


def test_tenure_arrival_transition():
    # The innovation rides on the arrival side as an argument of the
    # transition; `z^ρ_z*exp(σ_z*ε)` is the autoregression in levels, with the
    # power binding before the multiplication.
    want = Block(
        header("arvl_to_dcsn", sig(
            [coord("a", None, [dom("ℝ₊")]),
             coord("h", None, [dom("ℝ₊₊")]),
             coord("z", None, [dom("ℝ₊₊")]),
             coord("ε")],
            [Infoset(Arrival())],
            [coord("a_d", None, [dom("ℝ₊")]),
             coord("h_d", None, [dom("ℝ₊₊")]),
             coord("z_d", None, [dom("ℝ₊₊")])],
            [Infoset(Decision())])),
        [Statement(Equation(sym("a_d"), sym("a")), None),
         Statement(Equation(sym("h_d"), sym("h")), None),
         Statement(Equation(sym("z_d"),
                            Mul(Pow(sym("z"), sym("ρ_z")),
                                Call("exp", [Mul(sym("σ_z"), sym("ε"))]))),
                   ident("income_state"))])
    check(TENURE.items[11], want, "items[11]")


def test_tenure_branching_transition():
    # The branch control is typed by the ordered set of labels, the output side
    # is empty, and the body is one labelled block per branch, each defining
    # its own fields. No field name is shared between the branches.
    keep = Block(
        Annotation([KeyValue("label", "keep"),
                    sig([], [],
                        [coord("w_kp", None, [dom("ℝ₊₊")]),
                         coord("h_kp", None, [dom("ℝ₊₊")]),
                         coord("z_kp", None, [dom("ℝ₊₊")])],
                        [Infoset(Continuation())])]),
        [Statement(Equation(sym("w_kp"),
                            Add(Mul(sym("R"), sym("a_d")),
                                Call("𝑦", [sym("z_d")]))),
                   ident("cash_on_hand")),
         Statement(Equation(sym("h_kp"), Mul(one_minus("δ"), sym("h_d"))),
                   ident("housing_kept")),
         Statement(Equation(sym("z_kp"), sym("z_d")), None)])
    adjust = Block(
        Annotation([KeyValue("label", "adjust"),
                    sig([], [],
                        [coord("w_adj", None, [dom("ℝ₊₊")]),
                         coord("z_adj", None, [dom("ℝ₊₊")])],
                        [Infoset(Continuation())])]),
        [Statement(Equation(sym("w_adj"),
                            Add(Add(Mul(sym("R"), sym("a_d")),
                                    Mul(Mul(sym("R_H"), one_minus("δ")),
                                        sym("h_d"))),
                                Call("𝑦", [sym("z_d")]))),
                   ident("total_wealth")),
         Statement(Equation(sym("z_adj"), sym("z_d")), None)])
    want = Block(
        header("dcsn_to_cntn", sig(
            [coord("a_d"), coord("h_d"), coord("z_d"),
             coord("d", None, [Role(Control()),
                               Domain(FiniteSet(["keep", "adjust"]))])],
            [Infoset(Decision())], [], [])),
        [keep, adjust])
    check(TENURE.items[12], want, "items[12]")


def test_tenure_branch_selection():
    # Each backward line selects from a tuple by the control: the value, in
    # the stage file, and the derivatives of the decision value in a_d and
    # h_d, in the marginal block of marginals_tenure.bl, each a selection of
    # derivatives of the branch values with the derivative of the branch
    # transition as the factor. Tuple positions are in label order, keep
    # first.
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V_kp", At(Continuation()), value()),
             coord("V_adj", At(Continuation()), value()),
             coord("d")],
            [Infoset(Continuation())],
            [coord("V", None, value())],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Select(Tuple([cntn("V_kp"), cntn("V_adj")]),
                                   Key("d"))),
                   ident("choice_value"))])
    check(TENURE.items[13], want, "items[13]")
    # The marginal block's header is the value builder's restricted to what
    # its lines read: the two branch values and the control, and the value.
    (marginal,) = block_file(TENURE_MARGINALS.items, "tenure")
    want = Block(
        header("dcsn_marginal", sig(
            [coord("V_kp", At(Continuation())), coord("V_adj", At(Continuation())),
             coord("d")],
            [Infoset(Continuation())],
            [coord("V")],
            [Infoset(Decision())])),
        [Statement(Equation(derivative("a_d", sym("V")),
                            Select(Tuple([Mul(sym("R"), derivative("w_kp", cntn("V_kp"))),
                                          Mul(sym("R"), derivative("w_adj", cntn("V_adj")))]),
                                   Key("d"))),
                   ident("marginal_assets")),
         Statement(Equation(derivative("h_d", sym("V")),
                            Select(Tuple([Mul(one_minus("δ"), derivative("h_kp", cntn("V_kp"))),
                                          Mul(Mul(sym("R_H"), one_minus("δ")),
                                              derivative("w_adj", cntn("V_adj")))]),
                                   Key("d"))),
                   ident("marginal_housing"))])
    check(marginal, want, "marginals_tenure.bl items[1]")


def test_tenure_arrival_expectation():
    # The value is integrated over the innovation: one Operator, its head "E"
    # with the lexed underscore stripped. The laws `a_d = a` and `h_d = h`
    # are the identity in the two coordinates of the derivatives, so the
    # file writes no derivative line here.
    want = Block(
        header("dcsn_to_arvl", sig(
            [coord("V")],
            [Infoset(Decision())],
            [coord("V", At(Arrival()), value())],
            [Infoset(Arrival())])),
        [Statement(Equation(arvl("V"), Operator("E", [Var("ε")], [sym("V")])),
                   ident("value"))])
    check(TENURE.items[14], want, "items[14]")


def test_tenure_policy():
    # The policy block compares the same two alternatives as the value line and
    # returns the label; its inputs are the two continuation values alone.
    want = Block(
        header("policy", sig(
            [coord("V_kp", At(Continuation()), value()),
             coord("V_adj", At(Continuation()), value())],
            [Infoset(Continuation())],
            [coord("d", None, [Domain(FiniteSet(["keep", "adjust"])),
                               Role(Control())])],
            [Infoset(Decision())])),
        [Statement(Equation(sym("d"),
                            Operator("argmax", [Var("d")],
                                     [cntn("V_kp"), cntn("V_adj")])),
                   ident("choice"))])
    check(TENURE.items[15], want, "items[15]")


# --- keeper_cons.bl ----------------------------------------------------------

UTILITY = Add(
    Div(Mul(sym("α"), Pow(sym("c"), one_minus("γ_c"))), one_minus("γ_c")),
    Div(Mul(one_minus("α"), Pow(Mul(sym("κ"), sym("h")), one_minus("γ_h"))),
        one_minus("γ_h")))

MARGINAL_CONSUMPTION = Mul(sym("α"), Pow(sym("c"), Neg(sym("γ_c"))))

MARGINAL_HOUSING = Mul(Mul(one_minus("α"), Pow(sym("κ"), one_minus("γ_h"))),
                       Pow(sym("h"), Neg(sym("γ_h"))))

INVERSE_MARGINAL = Pow(Div(sym("α"), sym("x")), Div(Number(1), sym("γ_c")))

CONSUMPTION_PARAMS = [coord("c", None, [dom("ℝ₊₊")])]
HOUSING_PARAMS = [coord("h", None, [dom("ℝ₊₊")])]
UTILITY_PARAMS = CONSUMPTION_PARAMS + HOUSING_PARAMS


def preference_functions(items, offset):
    """The four closed forms both consumption stages write, in source order."""
    check(items[offset],
          Statement(FuncDef("𝑢", UTILITY_PARAMS, UTILITY), ident("util")),
          f"items[{offset}]")
    check(items[offset + 1],
          Statement(FuncDef("𝑢_c", CONSUMPTION_PARAMS, MARGINAL_CONSUMPTION),
                    ident("marg_util_cons")),
          f"items[{offset + 1}]")
    check(items[offset + 2],
          Statement(FuncDef("𝑢_h", HOUSING_PARAMS, MARGINAL_HOUSING),
                    ident("marg_util_housing")),
          f"items[{offset + 2}]")
    check(items[offset + 3],
          Statement(FuncDef("𝑢_c_inv", [coord("x", None, [dom("ℝ₊₊")])],
                            INVERSE_MARGINAL),
                    ident("inv_marg_util_cons")),
          f"items[{offset + 3}]")


def test_keeper_file_shape():
    # One metadata line, five parameters, four function definitions and one
    # correspondence definition, then the three blocks: the decision perch is
    # the stage's entry perch, and no arrival block stands before it.
    kinds = [type(item).__name__ for item in KEEPER.items]
    assert kinds == (["Metadata"] + ["Declare"] * 5 + ["Statement"] * 5
                     + ["Block"] * 3), kinds
    assert stage_ast.unlowered_parse_nodes(KEEPER) == []
    check(KEEPER.items[0], Metadata("stage", "keeper_cons"), "items[0]")


def test_keeper_declarations():
    # Both curvatures are declared above one: at one the written expression
    # divides by zero.
    scalar_declarations(KEEPER.items, 1, [
        ("β", Interval(Range(Open(), Number(0), Number(1), Open())),
         "discount factor"),
        ("α", Interval(Range(Open(), Number(0), Number(1), Open())),
         "weight of consumption in utility"),
        ("γ_c", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from consumption"),
        ("γ_h", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from housing services"),
        ("κ", Named("ℝ₊₊"), "housing services per unit of the housing stock"),
    ])


def test_keeper_functions_and_feasible_set():
    preference_functions(KEEPER.items, 6)
    # A definition whose body is a set is a correspondence definition: from
    # cash on hand to the interval of feasible consumption.
    check(KEEPER.items[10],
          Statement(CorrDef("Γ", [coord("x", None, [dom("ℝ₊₊")])],
                            Interval(Range(Open(), Number(0), sym("x"),
                                           Closed()))),
                    ident("feasible")),
          "items[10]")


def test_keeper_transitions():
    # The budget: savings are the declared non-negative output, so the equation
    # and the declared sets state that consumption cannot exceed cash on hand.
    # The header types the decision states, the stage having no arrival block
    # whose output would type them.
    budget = Block(
        header("dcsn_to_cntn", sig(
            [coord("w_d", None, [dom("ℝ₊₊")]), coord("h_d", None, [dom("ℝ₊₊")]),
             coord("z_d", None, [dom("ℝ₊₊")]),
             coord("c", None, [dom("ℝ₊₊"), Role(Control())])],
            [Infoset(Decision())],
            [coord("a_nxt_kp", None, [dom("ℝ₊")]),
             coord("h_nxt_kp", None, [dom("ℝ₊₊")]),
             coord("z_nxt_kp", None, [dom("ℝ₊₊")])],
            [Infoset(Continuation())])),
        [Statement(Equation(sym("a_nxt_kp"), Sub(sym("w_d"), sym("c"))),
                   ident("savings")),
         Statement(Equation(sym("h_nxt_kp"), sym("h_d")), ident("housing")),
         Statement(Equation(sym("z_nxt_kp"), sym("z_d")),
                   ident("income_state"))])
    check(KEEPER.items[11], budget, "items[11]")


def test_keeper_values():
    # Current utility plus the discounted continuation value. The inputs name
    # the continuation value and the control and no side word; the decision
    # state h_d the line reads is a coordinate of the output and is not
    # listed (the backward-header rule of 12 October 2026).
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V", At(Continuation()), value()), coord("c")],
            [],
            [coord("V", None, value())],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Add(Call("𝑢", [sym("c"), sym("h_d")]),
                                Mul(sym("β"), cntn("V")))),
                   ident("value"))])
    check(KEEPER.items[12], want, "items[12]")
    # The marginal block of marginals_keeper_cons.bl: the derivative of the
    # decision value in cash, the marginal utility of consumption; and its
    # derivative in housing, the housing services of the period plus the
    # discounted derivative of the continuation value in housing. Its header
    # joins the builder's perches as the builder writes them, with no side
    # word on the inputs.
    (marginal,) = block_file(KEEPER_MARGINALS.items, "keeper_cons")
    want = Block(
        header("dcsn_marginal", sig(
            [coord("V", At(Continuation())), coord("c")],
            [],
            [coord("V")],
            [Infoset(Decision())])),
        [Statement(Equation(derivative("w_d", sym("V")), Call("𝑢_c", [sym("c")])),
                   ident("marginal_cash")),
         Statement(Equation(derivative("h_d", sym("V")),
                            Add(Call("𝑢_h", [sym("h_d")]),
                                Mul(sym("β"), derivative("h_nxt_kp", cntn("V"))))),
                   ident("marginal_housing"))])
    check(marginal, want, "marginals_keeper_cons.bl items[1]")


def test_keeper_policy():
    # The stage file's policy block states the maximisation alone: it binds
    # the control on its feasible set. The method block of keeper_cons_egm.bl
    # holds the endogenous grid method: the inverse Euler line is an
    # inequality, which defines candidate consumption as a correspondence; the
    # second line inverts the budget; the third identifies the control with
    # the candidate.
    objective = Add(Call("𝑢", [sym("c"), sym("h_d")]),
                    Mul(sym("β"), cntn("V")))
    signature = sig(
        [coord("V", At(Continuation()), value())],
        [Infoset(Continuation())],
        [coord("c", None, [dom("ℝ₊₊"), Role(Control())])],
        [Infoset(Decision())])
    want = Block(
        header("policy", signature),
        [Statement(Equation(sym("c"),
                            Operator("argmax",
                                     [In("c", Call("Γ", [sym("w_d")]))],
                                     [objective])),
                   ident("optimality"))])
    check(KEEPER.items[13], want, "items[13]")
    (method,) = block_file(KEEPER_EGM.items, "keeper_cons")
    want = Block(
        header("egm", signature),
        [Statement(Inequality(cntn("c"), Le(),
                              Call("𝑢_c_inv",
                                   [Mul(sym("β"), derivative("a_nxt_kp", cntn("V")))])),
                   ident("InvEuler")),
         Statement(Equation(cntn("w_d"),
                            Add(sym("a_nxt_kp"), cntn("c"))),
                   ident("endoggrid")),
         Statement(Equation(sym("c"), cntn("c")), ident("cons_choice"))])
    check(method, want, "keeper_cons_egm.bl items[1]")


# --- adjuster_cons.bl --------------------------------------------------------

def test_adjuster_file_shape():
    # One metadata line, six parameters, four function definitions and two
    # correspondence definitions, then the three blocks: the decision perch is
    # the stage's entry perch, and no arrival block stands before it.
    kinds = [type(item).__name__ for item in ADJUSTER.items]
    assert kinds == (["Metadata"] + ["Declare"] * 6 + ["Statement"] * 6
                     + ["Block"] * 3), kinds
    assert stage_ast.unlowered_parse_nodes(ADJUSTER) == []
    check(ADJUSTER.items[0], Metadata("stage", "adjuster_cons"), "items[0]")


def test_adjuster_declarations_and_functions():
    scalar_declarations(ADJUSTER.items, 1, [
        ("β", Interval(Range(Open(), Number(0), Number(1), Open())),
         "discount factor"),
        ("α", Interval(Range(Open(), Number(0), Number(1), Open())),
         "weight of consumption in utility"),
        ("γ_c", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from consumption"),
        ("γ_h", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from housing services"),
        ("κ", Named("ℝ₊₊"), "housing services per unit of the housing stock"),
        ("τ", Named("ℝ₊₊"),
         "cost of adjusting housing, per unit of housing bought"),
    ])
    # The same four closed forms as the keeper's stage: one household, one
    # period, one utility function.
    preference_functions(ADJUSTER.items, 7)


def test_adjuster_feasible_sets():
    # Two correspondences, read in the order the maximisation binds them:
    # consumption up to total wealth, then housing up to what is left, divided
    # by the unit price of housing.
    check(ADJUSTER.items[11],
          Statement(CorrDef("Γ_c", [coord("x", None, [dom("ℝ₊₊")])],
                            Interval(Range(Open(), Number(0), sym("x"),
                                           Closed()))),
                    ident("feasible_consumption")),
          "items[11]")
    check(ADJUSTER.items[12],
          Statement(CorrDef("Γ_h", [coord("x", None, [dom("ℝ₊")])],
                            Interval(Range(Open(), Number(0),
                                           Div(sym("x"),
                                               Add(Number(1), sym("τ"))),
                                           Closed()))),
                    ident("feasible_housing")),
          "items[12]")


def test_adjuster_transitions():
    # Two controls on the decision side; the budget subtracts consumption and
    # then the cost of the new house, so the sum associates to the left. The
    # header types the decision states, the stage having no arrival block
    # whose output would type them.
    budget = Block(
        header("dcsn_to_cntn", sig(
            [coord("m", None, [dom("ℝ₊₊")]), coord("z_d", None, [dom("ℝ₊₊")]),
             coord("c", None, [dom("ℝ₊₊"), Role(Control())]),
             coord("h_choice", None, [dom("ℝ₊₊"), Role(Control())])],
            [Infoset(Decision())],
            [coord("a_nxt_adj", None, [dom("ℝ₊")]),
             coord("h_nxt_adj", None, [dom("ℝ₊₊")]),
             coord("z_nxt_adj", None, [dom("ℝ₊₊")])],
            [Infoset(Continuation())])),
        [Statement(Equation(sym("a_nxt_adj"),
                            Sub(Sub(sym("m"), sym("c")),
                                Mul(Add(Number(1), sym("τ")),
                                    sym("h_choice")))),
                   ident("savings")),
         Statement(Equation(sym("h_nxt_adj"), sym("h_choice")),
                   ident("housing")),
         Statement(Equation(sym("z_nxt_adj"), sym("z_d")),
                   ident("income_state"))])
    check(ADJUSTER.items[13], budget, "items[13]")


def test_adjuster_values():
    # Utility is over consumption and the new house. The one derivative the
    # marginal block of marginals_adjuster_cons.bl states is that of the
    # decision value in cash on hand m, which the tenure stage reads on this
    # branch, its total wealth `w_adj` joined to `m`.
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V", At(Continuation()), value()),
             coord("c"), coord("h_choice")],
            [Infoset(Continuation())],
            [coord("V", None, value())],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Add(Call("𝑢", [sym("c"), sym("h_choice")]),
                                Mul(sym("β"), cntn("V")))),
                   ident("value"))])
    check(ADJUSTER.items[14], want, "items[14]")
    (marginal,) = block_file(ADJUSTER_MARGINALS.items, "adjuster_cons")
    want = Block(
        header("dcsn_marginal", sig(
            [coord("c")],
            [Infoset(Continuation())],
            [coord("V")],
            [Infoset(Decision())])),
        [Statement(Equation(derivative("m", sym("V")), Call("𝑢_c", [sym("c")])),
                   ident("marginal_wealth"))])
    check(marginal, want, "marginals_adjuster_cons.bl items[1]")


def test_adjuster_policy():
    # The stage file's policy block states the joint maximisation alone: a
    # tuple on the left, and two binders each carrying a feasible set, the
    # second reading the first binder. The method block of
    # adjuster_cons_egm.bl holds the inverse Euler inequality, the inverted
    # budget, and the two first-order conditions as one solution statement in
    # two unknowns.
    objective = Add(Call("𝑢", [sym("c"), sym("h_choice")]),
                    Mul(sym("β"), cntn("V")))
    housing_residual = Sub(
        Sub(Mul(Add(Number(1), sym("τ")), Call("𝑢_c", [sym("c")])),
            Call("𝑢_h", [sym("h_choice")])),
        Mul(sym("β"), derivative("h_nxt_adj", cntn("V"))))
    signature = sig(
        [coord("V", At(Continuation()), value())],
        [Infoset(Continuation())],
        [coord("c", None, [dom("ℝ₊₊"), Role(Control())]),
         coord("h_choice", None, [dom("ℝ₊₊"), Role(Control())])],
        [Infoset(Decision())])
    want = Block(
        header("policy", signature),
        [Statement(Equation(Tuple([sym("c"), sym("h_choice")]),
                            Operator("argmax",
                                     [In("c", Call("Γ_c", [sym("m")])),
                                      In("h_choice",
                                         Call("Γ_h", [Sub(sym("m"),
                                                          sym("c"))]))],
                                     [objective])),
                   ident("optimality"))])
    check(ADJUSTER.items[15], want, "items[15]")
    (method,) = block_file(ADJUSTER_EGM.items, "adjuster_cons")
    want = Block(
        header("egm", signature),
        [Statement(Inequality(cntn("c"), Le(),
                              Call("𝑢_c_inv",
                                   [Mul(sym("β"), derivative("a_nxt_adj", cntn("V")))])),
                   ident("InvEuler")),
         Statement(Equation(cntn("m"),
                            Add(Add(sym("a_nxt_adj"), cntn("c")),
                                Mul(Add(Number(1), sym("τ")),
                                    sym("h_nxt_adj")))),
                   ident("endoggrid")),
         Statement(Equation(Tuple([sym("c"), sym("h_choice")]),
                            Operator("solve", [Var("c"), Var("h_choice")],
                                     [Sub(sym("c"), cntn("c")),
                                      housing_residual])),
                   ident("choice"))])
    check(method, want, "adjuster_cons_egm.bl items[1]")


if __name__ == "__main__":
    sys.exit(run_checks(globals(), "on the three durables stages and their block files"))
